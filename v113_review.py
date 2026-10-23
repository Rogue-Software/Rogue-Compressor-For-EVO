"""Review adapter for the UNMODIFIED v11.3 tracker; mask preview cached once."""
import tempfile
from pathlib import Path
import cv2
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSlider,QMessageBox
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from privacy_editor import DrawLabel
from track_head_fast_v11_3 import clamp,flow_box,template_recover,anchored_recover


def render_original(source, start, end, box, output, progress=None):
    """Exact v11.3 flow/anchor/padding loop, using the app's selected ROI and trim."""
    cap=cv2.VideoCapture(str(source))
    cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
    if not cap.isOpened():raise RuntimeError('Could not open source')
    cap.set(cv2.CAP_PROP_POS_MSEC,float(start)*1000)
    ok,first=cap.read()
    if not ok:raise RuntimeError('Cannot decode trim start')
    fps=cap.get(cv2.CAP_PROP_FPS) or 30
    oh,ow=first.shape[:2]; ratio=min(1,640/ow);sw,sh=round(ow*ratio),round(oh*ratio)
    def small(f):return cv2.resize(f,(sw,sh),interpolation=cv2.INTER_AREA)
    preview=small(first)
    x,y,w,h=box
    last=clamp([x*sw,y*sh,w*sw,h*sh],sw,sh)
    ix,iy,iw,ih=last
    original_template=preview[iy:iy+ih,ix:ix+iw].copy()
    prev=preview;gray=cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY)
    writer=cv2.VideoWriter(str(output),cv2.VideoWriter_fourcc(*'mp4v'),fps,(ow,oh))
    if not writer.isOpened():raise RuntimeError('Cannot create preview video')
    count=max(1,round((end-start)*fps))
    try:
        for frameidx in range(count):
            if frameidx==0:full=first;cur=preview
            else:
                ok,full=cap.read()
                if not ok:break
                cur=small(full)
                newgray=cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY)
                moved,conf=flow_box(gray,newgray,last)
                if moved is None:
                    moved,conf2=template_recover(prev,cur,last)
                    if moved is None:moved=last
                if frameidx%5==0:
                    anchored,score=anchored_recover(cur,original_template,moved,(iw,ih))
                    if anchored is not None:
                        old_center=np.array([moved[0]+moved[2]/2,moved[1]+moved[3]/2])
                        new_center=np.array([anchored[0]+iw/2,anchored[1]+ih/2])
                        shift=float(np.linalg.norm(new_center-old_center))
                        if shift>max(3,min(iw,ih)*.12):moved=anchored
                last=moved;gray=newgray
            x,y,w,h=last
            px=int(w*.30);py=int(h*.30)
            x1=max(0,int((x-px)/ratio));y1=max(0,int((y-py)/ratio))
            x2=min(ow,int((x+w+px)/ratio));y2=min(oh,int((y+h+py)/ratio))
            full[y1:y2,x1:x2]=(0,0,0)
            writer.write(full);prev=cur
            if progress and frameidx%15==0:progress(int(100*(frameidx+1)/count))
    finally:
        cap.release();writer.release()
    return fps

class RenderWorker(QThread):
    ready=Signal(float);failed=Signal(str);progress=Signal(int)
    def __init__(self,source,start_time,end_time,box,output):
        super().__init__();self.source=source;self.start_time=start_time;self.end_time=end_time;self.box=box;self.output=output
    def run(self):
        try:self.ready.emit(render_original(self.source,self.start_time,self.end_time,self.box,self.output,self.progress.emit))
        except Exception as exc:self.failed.emit(str(exc))

class ReviewDialog(QDialog):
    def __init__(self,source,start,end,box,parent=None):
        super().__init__(parent);self.setWindowTitle('Rogue — v11.3 Mask Review');self.resize(850,790)
        self.tmp=tempfile.TemporaryDirectory(prefix='rogue_v113_');self.masked=str(Path(self.tmp.name)/'review.mp4')
        self.fps=30.;self.frame_count=0;self.corrections={};self.current=0;self.cap=None
        self.source=source;self.start_time=start;self.end_time=end
        layout=QVBoxLayout(self)
        self.info=QLabel('Rendering original v11.3 tracking once. Please wait…');layout.addWidget(self.info)
        self.video=QVideoWidget();layout.addWidget(self.video,1)
        self.draw=DrawLabel();self.draw.hide();layout.addWidget(self.draw,1)
        self.player=QMediaPlayer(self);self.player.setVideoOutput(self.video)
        self.player.positionChanged.connect(self.on_position)
        self.player.durationChanged.connect(lambda ms:self.seek.setMaximum(max(0,round(ms*self.fps/1000)-1)))
        self.seek=QSlider(Qt.Orientation.Horizontal);layout.addWidget(self.seek)
        self.seek.sliderReleased.connect(lambda:self.jump(self.seek.value()))
        controls=QHBoxLayout();layout.addLayout(controls)
        for title,fn in [('Play / Pause',self.toggle),('◀ Frame',lambda:self.jump(self.current-1)),('Frame ▶',lambda:self.jump(self.current+1)),('Correct this frame',self.edit_frame),('Save correction',self.save_frame)]:
            b=QPushButton(title);b.clicked.connect(fn);controls.addWidget(b)
        self.save_btn=QPushButton('Approve reviewed clip');self.save_btn.clicked.connect(self.accept);layout.addWidget(self.save_btn)
        self.save_btn.setEnabled(False)
        self.worker=RenderWorker(source,start,end,box,self.masked)
        self.worker.progress.connect(lambda n:self.info.setText(f'Rendering v11.3 masks: {n}%'))
        self.worker.ready.connect(self.ready);self.worker.failed.connect(lambda s:(self.info.setText(s),QMessageBox.critical(self,'Review failed',s)))
        self.worker.start()
    def ready(self,fps):
        self.fps=fps;self.cap=cv2.VideoCapture(self.masked)
        self.cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 0)
        self.frame_count=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT));self.seek.setMaximum(max(0,self.frame_count-1))
        self.player.setSource(QUrl.fromLocalFile(self.masked));self.info.setText('Watch entire clip. Pause and correct any exposed frames.');self.save_btn.setEnabled(True)
    def on_position(self,ms):
        if not self.draw.isVisible():
            self.current=min(max(0,round(ms*self.fps/1000)),max(0,self.frame_count-1))
            if not self.seek.isSliderDown():self.seek.setValue(self.current)
    def toggle(self):
        if self.draw.isVisible():self.draw.hide();self.video.show()
        if self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState:self.player.pause()
        else:self.player.play()
    def jump(self,n):
        self.current=max(0,min(self.frame_count-1,n));self.seek.setValue(self.current)
        self.player.pause();self.player.setPosition(round(self.current*1000/self.fps))
        if self.draw.isVisible():self.edit_frame()
    def edit_frame(self):
        if self.cap is None:return
        self.player.pause();self.cap.set(cv2.CAP_PROP_POS_FRAMES,self.current)
        ok,frame=self.cap.read()
        if not ok:return
        self.video.hide();self.draw.show();self.draw.box=None
        self.draw.set_frame(frame,self.corrections.get(self.current,[]))
        self.info.setText(f'Frame {self.current}: drag a rectangle over any exposed face, then Save correction.')
    def save_frame(self):
        if not self.draw.isVisible() or not self.draw.box:return
        self.corrections.setdefault(self.current,[]).append(list(self.draw.box))
        self.draw.box=None;self.edit_frame()
        self.info.setText(f'Saved correction for frame {self.current}. {len(self.corrections)} corrected frames.')
    def closeEvent(self,event):
        self.player.stop()
        if self.cap:self.cap.release();self.cap=None
        if self.worker.isRunning():self.worker.wait()
        super().closeEvent(event)

def apply_corrections(masked,corrections,out):
    cap=cv2.VideoCapture(masked);fps=cap.get(cv2.CAP_PROP_FPS) or 30
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer=cv2.VideoWriter(str(out),cv2.VideoWriter_fourcc(*'MJPG'),fps,(w,h))
    if not writer.isOpened():raise RuntimeError('Could not write corrected video')
    idx=0
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            for x,y,bw,bh in corrections.get(idx,[]):
                x1=max(0,min(w,int(x*w)));y1=max(0,min(h,int(y*h)))
                x2=max(x1,min(w,int((x+bw)*w)));y2=max(y1,min(h,int((y+bh)*h)))
                frame[y1:y2,x1:x2]=0
            writer.write(frame);idx+=1
    finally:cap.release();writer.release()
