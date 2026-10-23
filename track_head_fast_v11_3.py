"""Rogue v11.3 experimental fast manual-head tracker. Review ALL output before sharing."""
import argparse, json, time
from pathlib import Path
import cv2
import numpy as np

def clamp(box, w, h):
    x,y,bw,bh=map(int,map(round,box))
    bw=max(8,min(w,bw)); bh=max(8,min(h,bh))
    return [max(0,min(w-bw,x)),max(0,min(h-bh,y)),bw,bh]

def flow_box(old, new, box):
    x,y,w,h=box
    mask=np.zeros_like(old)
    mask[max(0,y):min(old.shape[0],y+h),max(0,x):min(old.shape[1],x+w)]=255
    pts=cv2.goodFeaturesToTrack(old, maxCorners=130, qualityLevel=.012, minDistance=4, mask=mask)
    if pts is None or len(pts)<9: return None,0
    nxt,status,_=cv2.calcOpticalFlowPyrLK(old,new,pts,None,winSize=(25,25),maxLevel=3)
    if nxt is None or status is None: return None,0
    ok=status.ravel()==1
    if ok.sum()<9: return None,0
    src=pts[ok,0]; dst=nxt[ok,0]
    mat,inliers=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=3)
    if mat is None or inliers is None: return None,0
    fraction=float(inliers.sum())/len(src)
    scale=float(np.hypot(mat[0,0],mat[0,1]))
    if fraction<.58 or not .88<scale<1.13: return None,fraction
    center=mat@np.array([x+w/2,y+h/2,1.])
    if abs(center[0]-(x+w/2))>w*.65 or abs(center[1]-(y+h/2))>h*.65: return None,fraction
    return clamp([center[0]-w*scale/2,center[1]-h*scale/2,w*scale,h*scale],new.shape[1],new.shape[0]),fraction

def template_recover(prev_frame, frame, box):
    x,y,w,h=box
    if min(w,h)<15:return None,0
    template=prev_frame[y:y+h,x:x+w]
    if template.size==0:return None,0
    radius=int(max(w,h)*.5)
    x1=max(0,x-radius);y1=max(0,y-radius)
    x2=min(frame.shape[1],x+w+radius);y2=min(frame.shape[0],y+h+radius)
    search=frame[y1:y2,x1:x2]
    if search.shape[0]<h or search.shape[1]<w:return None,0
    score=cv2.matchTemplate(search,template,cv2.TM_CCOEFF_NORMED)
    _,val,_,pos=cv2.minMaxLoc(score)
    if val<.72:return None,float(val)
    return clamp([x1+pos[0],y1+pos[1],w,h],frame.shape[1],frame.shape[0]),float(val)


def select_head_corner(image):
    """Explicit corner-to-corner drag, with R to redraw and Space/Enter to accept."""
    title = 'ROGUE v11.3 - click CORNER and drag | SPACE confirm | R reset | ESC cancel'
    state = {'start': None, 'end': None, 'dragging': False}
    def mouse(event, x, y, flags, userdata):
        if event == cv2.EVENT_LBUTTONDOWN:
            state.update(start=(x,y), end=(x,y), dragging=True)
        elif event == cv2.EVENT_MOUSEMOVE and state['dragging']:
            state['end']=(x,y)
        elif event == cv2.EVENT_LBUTTONUP and state['dragging']:
            state.update(end=(x,y), dragging=False)
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, image.shape[1], image.shape[0])
    cv2.setMouseCallback(title, mouse)
    try:
        while True:
            view=image.copy()
            if state['start'] and state['end']:
                a,b=state['start'],state['end']
                cv2.rectangle(view,a,b,(0,255,255),2)
            cv2.putText(view,'Drag corner to corner | SPACE: confirm | R: redraw | ESC: cancel',
                        (8, max(18,image.shape[0]-12)),cv2.FONT_HERSHEY_SIMPLEX,.43,(0,255,255),1,cv2.LINE_AA)
            cv2.imshow(title,view)
            key=cv2.waitKey(20)&0xFF
            if key in (ord('r'),ord('R')):
                state.update(start=None,end=None,dragging=False)
            elif key in (13,32):
                if state['start'] and state['end'] and not state['dragging']:
                    x1,y1=state['start'];x2,y2=state['end']
                    box=[min(x1,x2),min(y1,y2),abs(x2-x1),abs(y2-y1)]
                    if box[2]>=10 and box[3]>=10:return box
            elif key==27:
                raise RuntimeError('Head selection cancelled')
    finally:
        cv2.destroyWindow(title)


def anchored_recover(frame, original_template, previous_box, initial_size):
    """Conservative match to FIRST selected head image; never self-updates."""
    x,y,w,h=previous_box
    tw,th=initial_size
    if original_template.size == 0:return None,0.0
    radius=int(max(tw,th)*0.9)
    cx,cy=x+w//2,y+h//2
    x1=max(0,cx-tw//2-radius);y1=max(0,cy-th//2-radius)
    x2=min(frame.shape[1],cx+tw//2+radius);y2=min(frame.shape[0],cy+th//2+radius)
    search=frame[y1:y2,x1:x2]
    if search.shape[0]<th or search.shape[1]<tw:return None,0.0
    response=cv2.matchTemplate(search,original_template,cv2.TM_CCOEFF_NORMED)
    _,score,_,pos=cv2.minMaxLoc(response)
    if not np.isfinite(score) or score<0.83:return None,float(score)
    candidate=clamp([x1+pos[0],y1+pos[1],tw,th],frame.shape[1],frame.shape[0])
    return candidate,float(score)

def main():
    ap=argparse.ArgumentParser(description='Experimental fast head privacy tracker; requires manual review')
    ap.add_argument('video',type=Path)
    ap.add_argument('--output',type=Path,default=Path('head_fast_review.mp4'))
    ap.add_argument('--width',type=int,default=640)
    ap.add_argument('--max-seconds',type=float,default=60)
    ap.add_argument('--pad',type=float,default=.30)
    ap.add_argument('--anchor-every',type=int,default=5,help='Try original-head appearance check every N frames (0 disables)')
    ap.add_argument('--box',nargs=4,type=int,metavar=('X','Y','W','H'),help='Head box at tracking resolution')
    args=ap.parse_args()
    if not args.video.is_file():ap.error('Video not found')
    if args.output.exists() or args.output.resolve()==args.video.resolve():ap.error('Choose a NEW output path')
    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened():ap.error('Cannot open video')
    fps=cap.get(cv2.CAP_PROP_FPS) or 30
    ok,first=cap.read()
    if not ok:ap.error('Cannot decode first frame')
    ow,oh=first.shape[1],first.shape[0]
    ratio=min(1,args.width/ow)
    sw,sh=round(ow*ratio),round(oh*ratio)
    def small(f):return cv2.resize(f,(sw,sh),interpolation=cv2.INTER_AREA)
    preview=small(first)
    if args.box:box=clamp(args.box,sw,sh)
    else:
        bx=select_head_corner(preview)
        box=clamp(bx,sw,sh)
        if bx[2]<10 or bx[3]<10:ap.error('No valid head box selected')
    writer=cv2.VideoWriter(str(args.output),cv2.VideoWriter_fourcc(*'mp4v'),fps,(ow,oh))
    if not writer.isOpened():ap.error('Could not create MP4')
    maxframes=max(1,int(fps*args.max_seconds))
    prev=preview
    gray=cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY)
    issues=[]; frameidx=0; t0=time.monotonic(); last=box
    ix,iy,iw,ih=box
    original_template=preview[iy:iy+ih,ix:ix+iw].copy()
    corrections=0
    try:
        while frameidx<maxframes:
            if frameidx==0:full=first; cur=preview
            else:
                ok,full=cap.read()
                if not ok:break
                cur=small(full)
                newgray=cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY)
                moved,conf=flow_box(gray,newgray,last)
                if moved is None:
                    moved,conf2=template_recover(prev,cur,last)
                    if moved is None:
                        issues.append({'frame':frameidx,'time_seconds':round(frameidx/fps,3),'reason':'tracking lost; last box held'})
                        moved=last
                    else:
                        issues.append({'frame':frameidx,'time_seconds':round(frameidx/fps,3),'reason':'template recovery; verify head coverage'})
                # Independent appearance anchor: compare against the ORIGINAL head crop,
                # not the drifting previous-frame crop. Only correct with strong evidence.
                if args.anchor_every>0 and frameidx%args.anchor_every==0:
                    anchored,score=anchored_recover(cur,original_template,moved,(iw,ih))
                    if anchored is not None:
                        old_center=np.array([moved[0]+moved[2]/2,moved[1]+moved[3]/2])
                        new_center=np.array([anchored[0]+iw/2,anchored[1]+ih/2])
                        shift=float(np.linalg.norm(new_center-old_center))
                        if shift>max(3,min(iw,ih)*.12):
                            issues.append({'frame':frameidx,'time_seconds':round(frameidx/fps,3),
                                           'reason':'strong original-template anchor correction; verify coverage',
                                           'anchor_score':round(score,3)})
                            moved=anchored
                            corrections+=1
                last=moved
                gray=newgray
            x,y,w,h=last
            px=int(w*args.pad);py=int(h*args.pad)
            x1=max(0,int((x-px)/ratio));y1=max(0,int((y-py)/ratio))
            x2=min(ow,int((x+w+px)/ratio));y2=min(oh,int((y+h+py)/ratio))
            full[y1:y2,x1:x2]=(0,0,0)
            writer.write(full)
            prev=cur
            frameidx+=1
            if frameidx%60==0:print(f'{frameidx} frames / {time.monotonic()-t0:.1f}s elapsed',flush=True)
    finally:
        cap.release();writer.release();cv2.destroyAllWindows()
    report=args.output.with_suffix('.review.json')
    report.write_text(json.dumps({'source':str(args.video),'output':str(args.output),'frames':frameidx,'fps':fps,'seconds_elapsed':round(time.monotonic()-t0,2),'anchor_corrections':corrections,'uncertain_frames':issues,'warning':'EXPERIMENTAL. Even frames without warnings may expose the head. Review every frame before sharing. Video audio is not preserved.'},indent=2))
    print(f'Finished {frameidx} frames in {time.monotonic()-t0:.1f}s; {len(issues)} uncertain frames.\nReview video: {args.output}\nReview report: {report}\nNOT a privacy-verified export.')
if __name__=='__main__':main()
