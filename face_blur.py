"""Experimental v5 YuNet face masking with full-head appearance tracking. Conservative tracking; no silent Haar fallback.

A neural model is required in models/; review every exported frame before sharing.
"""
import json
import shutil
import subprocess
from pathlib import Path
import cv2
import numpy as np

MODEL_NAME = 'face_detection_yunet_2023mar.onnx'
MODEL_PATH = Path(__file__).resolve().parent / 'models' / MODEL_NAME


def _video_info(source):
    ffprobe = shutil.which('ffprobe')
    if not ffprobe:
        raise RuntimeError('FFprobe is required.')
    p = subprocess.run([ffprobe, '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height,avg_frame_rate:stream_side_data=rotation',
                        '-of', 'json', str(source)], capture_output=True, text=True, check=True)
    s = json.loads(p.stdout)['streams'][0]
    numerator, denominator = s.get('avg_frame_rate', '30/1').split('/')
    fps = float(numerator) / float(denominator)
    rotation = next((int(v['rotation']) for v in s.get('side_data_list', []) if 'rotation' in v), 0)
    w, h = int(s['width']), int(s['height'])
    if abs(rotation) % 180 == 90:
        w, h = h, w
    scale = min(1., 960 / max(w, h))
    w, h = max(2, round(w*scale/2)*2), max(2, round(h*scale/2)*2)
    if not 1 <= fps <= 240:
        raise RuntimeError('Unsupported frame rate.')
    return w, h, fps


def _frames(source, start, w, h):
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg is required.')
    cmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-ss', str(start), '-i', str(source),
           '-an', '-sn', '-vf', f'scale={w}:{h}', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        frame_size = w*h*3
        while True:
            raw = proc.stdout.read(frame_size)
            if len(raw) != frame_size:
                break
            yield np.frombuffer(raw, np.uint8).reshape(h, w, 3).copy()
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.communicate()


def _iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[0]+a[2], b[0]+b[2]), min(a[1]+a[3], b[1]+b[3])
    inter = max(0, x2-x1)*max(0, y2-y1)
    return inter / max(1, a[2]*a[3]+b[2]*b[3]-inter)


def _clamp(box, width, height):
    x,y,w,h = [int(round(v)) for v in box]
    w,h = max(8,min(width,w)), max(8,min(height,h))
    return [max(0,min(width-w,x)),max(0,min(height-h,y)),w,h]


class Obscurer:
    def __init__(self, strength='Strong', manual_box=None):
        if not MODEL_PATH.is_file():
            raise RuntimeError(f'Missing YuNet face detector model: {MODEL_PATH}\nSee README.md for the official download link.')
        if not hasattr(cv2, 'FaceDetectorYN_create'):
            raise RuntimeError('Your OpenCV installation does not support YuNet. Install opencv-python==4.11.0.86.')
        try:
            self.detector = cv2.FaceDetectorYN_create(str(MODEL_PATH), '', (320, 320), 0.65, 0.3, 5000)
        except cv2.error as exc:
            raise RuntimeError(f'Cannot load YuNet model: {exc}') from exc
        self.strength = strength
        self.manual_box = manual_box
        self.tracks = []
        self.index = 0
        self.prev_gray = None
        self.unconfirmed = []
        self.last_boxes = []

    def _detect(self, frame):
        height, width = frame.shape[:2]
        self.detector.setInputSize((width, height))
        _, results = self.detector.detect(frame)
        if results is None:
            return []
        boxes = []
        for row in results:
            if row[-1] < .65:
                continue
            box = _clamp(row[:4], width, height)
            if box[2] >= 14 and box[3] >= 14:
                boxes.append(box)
        return boxes

    def _flow(self, box, gray):
        if self.prev_gray is None:
            return None
        x,y,w,h = box
        mask = np.zeros_like(self.prev_gray)
        ix, iy = int(x+w*.15), int(y+h*.15)
        mask[iy:min(gray.shape[0],int(y+h*.85)),ix:min(gray.shape[1],int(x+w*.85))] = 255
        pts = cv2.goodFeaturesToTrack(self.prev_gray, maxCorners=70, qualityLevel=.015, minDistance=5, mask=mask)
        if pts is None or len(pts) < 8:
            return None
        nxt, status, _ = cv2.calcOpticalFlowPyrLK(self.prev_gray, gray, pts, None, winSize=(21,21), maxLevel=3)
        if nxt is None:
            return None
        good = status.ravel() == 1
        a,b = pts[good,0],nxt[good,0]
        if len(a)<8:
            return None
        matrix, inliers = cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=3)
        if matrix is None or inliers is None or int(inliers.sum()) < max(6,int(len(a)*.65)):
            return None
        scale = np.hypot(matrix[0,0],matrix[0,1])
        if not .92 <= scale <= 1.09:
            return None
        center = np.array([x+w/2,y+h/2,1.])
        cx,cy = matrix @ center
        if abs(cx-(x+w/2)) > w*.25 or abs(cy-(y+h/2)) > h*.25:
            return None
        return _clamp([cx-w*scale/2,cy-h*scale/2,w*scale,h*scale],gray.shape[1],gray.shape[0])

    def process(self, frame):
        height,width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.index == 0 and self.manual_box:
            x,y,w,h = self.manual_box
            self.tracks.append({'box':_clamp([x*width,y*height,w*width,h*height],width,height),
                                'manual':True,'miss':0,'age':1})
        for t in self.tracks:
            moved = self._flow(t['box'], gray)
            if moved is not None:
                t['box'] = moved
            else:
                t['miss'] += 1
        # Detect every frame to minimize reacquisition delays.
        if True:
            detections = self._detect(frame)
            used = set()
            for t in self.tracks:
                candidates = [(i,_iou(t['box'],b)) for i,b in enumerate(detections) if i not in used]
                if candidates:
                    i,score = max(candidates,key=lambda v:v[1])
                    if score >= .22:
                        used.add(i)
                        t['box'] = detections[i]
                        t['miss'] = 0
                        t['age'] += 1
            remaining = [b for i,b in enumerate(detections) if i not in used]
            next_candidates = []
            for box in remaining:
                match = next((c for c in self.unconfirmed if _iou(c['box'],box)>.4),None)
                if match:
                    count = match['count']+1
                else:
                    count = 1
                if count >= 1:
                    self.tracks.append({'box':box,'manual':False,'miss':0,'age':2})
                else:
                    next_candidates.append({'box':box,'count':count})
            self.unconfirmed = next_candidates
        # Retain recent masks across brief optical-flow failures; never treat this as guaranteed tracking.
        self.tracks = [t for t in self.tracks if t['miss'] <= (12 if t['manual'] else 10)]
        output = frame.copy()
        for t in self.tracks:
            x,y,w,h = t['box']
            pad = .40 if not t['manual'] else .35
            px,py = int(w*pad),int(h*pad)
            x1,y1,x2,y2 = max(0,x-px),max(0,y-py),min(width,x+w+px),min(height,y+h+py)
            roi = output[y1:y2,x1:x2]
            if not roi.size:
                continue
            if self.strength == 'Maximum':
                roi[:] = (15,15,15)
            else:
                block = max(12, min(roi.shape[:2])//(12 if self.strength=='Medium' else 3))
                tiny = cv2.resize(roi,(max(1,roi.shape[1]//block),max(1,roi.shape[0]//block)),interpolation=cv2.INTER_AREA)
                roi[:] = cv2.resize(tiny,(roi.shape[1],roi.shape[0]),interpolation=cv2.INTER_NEAREST)
        self.last_boxes = [tuple(t['box']) for t in self.tracks]
        self.prev_gray = gray
        self.index += 1
        return output, len(self.tracks)


def preview_frame(source,start,strength='Strong',manual_box=None):
    w,h,_ = _video_info(source)
    frames = _frames(source,start,w,h)
    try:
        frame = next(frames)
    except StopIteration:
        raise RuntimeError('Cannot decode selected frame.')
    finally:
        frames.close()
    # Preview an isolated frame using the same detection threshold as export.
    obscurer = Obscurer(strength, manual_box)
    detected = obscurer._detect(frame)
    if manual_box:
        x, y, bw, bh = manual_box
        detected.append(_clamp([x*w, y*h, bw*w, bh*h], w, h))
    obscurer.tracks = [{'box': box, 'manual': False, 'miss': 0, 'age': 2} for box in detected]
    obscurer.index = 1  # avoid resetting manual tracks
    return obscurer.process(frame)


def _match_box(a, b):
    """Reject sudden jumps and major changes in size when joining track fragments."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    distance = np.hypot((ax+aw/2)-(bx+bw/2), (ay+ah/2)-(by+bh/2))
    return (distance < max(aw, ah, bw, bh) * 1.15
            and 0.55 < bw / max(aw, 1) < 1.8
            and 0.55 < bh / max(ah, 1) < 1.8)


def _repair_tracks(raw, fps, manual_box=None):
    """Join compatible tracks and bridge brief gaps from both temporal directions.

    Returns per-frame masks. This is a best-effort repair, not proof of anonymity.
    """
    tracks = []
    max_gap = max(1, round(fps * 1.5))
    for frame_idx, boxes in enumerate(raw):
        used = set()
        for box in boxes:
            choices = []
            for ti, track in enumerate(tracks):
                if ti in used:
                    continue
                last_idx, last_box = track[-1]
                if frame_idx - last_idx <= max_gap and _match_box(last_box, box):
                    d = np.hypot((last_box[0]+last_box[2]/2)-(box[0]+box[2]/2),
                                 (last_box[1]+last_box[3]/2)-(box[1]+box[3]/2))
                    choices.append((d, ti))
            if choices:
                _, ti = min(choices)
                tracks[ti].append((frame_idx, box))
                used.add(ti)
            else:
                tracks.append([(frame_idx, box)])
                used.add(len(tracks)-1)

    result = [[] for _ in raw]
    for track in tracks:
        for (ia, a), (ib, b) in zip(track, track[1:]):
            result[ia].append(a)
            if ib - ia <= max_gap and _match_box(a, b):
                for j in range(ia + 1, ib):
                    t = (j - ia) / (ib - ia)
                    result[j].append(tuple(a[k]*(1-t)+b[k]*t for k in range(4)))
        last_idx, last_box = track[-1]
        result[last_idx].append(last_box)
        first_idx, first_box = track[0]
        if first_idx <= round(fps * .4):
            for j in range(first_idx):
                result[j].append(first_box)

    # Second pass: short holes with compatible masks on both sides can occur
    # when the detector drops a track and reacquires it with a new track ID.
    # Do not extrapolate from a single endpoint or across scene changes.
    i = 0
    while i < len(result):
        if result[i]:
            i += 1
            continue
        begin = i
        while i < len(result) and not result[i]:
            i += 1
        end = i
        if begin == 0 or end >= len(result) or end - begin > max_gap:
            continue
        before, after = result[begin - 1], result[end]
        candidates = [(a, b) for a in before for b in after if _match_box(a, b)]
        if not candidates:
            continue
        a, b = min(candidates, key=lambda pair: np.hypot(
            (pair[0][0]+pair[0][2]/2)-(pair[1][0]+pair[1][2]/2),
            (pair[0][1]+pair[0][3]/2)-(pair[1][1]+pair[1][3]/2)))
        span = end - (begin - 1)
        for j in range(begin, end):
            t = (j - (begin - 1)) / span
            result[j].append(tuple(a[k]*(1-t)+b[k]*t for k in range(4)))
    return result


def _motion_bridge(source, start, width, height, masks, fps):
    """Use image motion to carry a known mask across short no-mask intervals.

    This is a best-effort fallback. It never claims a tracked box proves privacy.
    A forward and a backward pass are used to avoid relying on a stale location.
    """
    if not masks or all(masks):
        return masks
    max_hole = max(1, round(fps * 1.25))
    holes = []
    i = 0
    while i < len(masks):
        if masks[i]:
            i += 1
            continue
        a = i
        while i < len(masks) and not masks[i]:
            i += 1
        b = i
        if a > 0 and b < len(masks) and b-a <= max_hole:
            holes.append((a, b))
    if not holes:
        return masks
    wanted = set()
    for a,b in holes:
        wanted.update(range(a-1,b+1))
    grays = {}
    frames = _frames(source,start,width,height)
    try:
        for i,frame in enumerate(frames):
            if i >= len(masks):
                break
            if i in wanted:
                grays[i] = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    finally:
        frames.close()

    def move(box, prev, cur):
        if prev is None or cur is None:
            return None
        x,y,w,h = _clamp(box,width,height)
        region = np.zeros_like(prev)
        # Include head and surrounding movement features.
        x1,y1 = max(0,int(x-w*.35)),max(0,int(y-h*.35))
        x2,y2 = min(width,int(x+w*1.35)),min(height,int(y+h*1.35))
        region[y1:y2,x1:x2] = 255
        pts = cv2.goodFeaturesToTrack(prev,maxCorners=130,qualityLevel=.01,minDistance=4,mask=region)
        if pts is None or len(pts)<6:
            return None
        nxt,status,_ = cv2.calcOpticalFlowPyrLK(prev,cur,pts,None,winSize=(25,25),maxLevel=3)
        if nxt is None or status is None:
            return None
        good = status.ravel()==1
        if good.sum()<6:
            return None
        displacement = nxt[good,0]-pts[good,0]
        dx,dy = np.median(displacement,axis=0)
        # Reject incoherent motion or large jumps.
        errors = np.linalg.norm(displacement-np.array([dx,dy]),axis=1)
        if np.median(errors)>max(8,min(w,h)*.25):
            return None
        if abs(dx)>max(20,w*.5) or abs(dy)>max(20,h*.5):
            return None
        return _clamp([x+dx,y+dy,w,h],width,height)

    for a,b in holes:
        before = masks[a-1]
        after = masks[b]
        if not before or not after:
            continue
        # Choose closest compatible endpoint pair; no cross-scene blind carry.
        pairs = [(x,y) for x in before for y in after if _match_box(x,y)]
        if not pairs:
            continue
        left,right = min(pairs,key=lambda pair: np.hypot(
            (pair[0][0]+pair[0][2]/2)-(pair[1][0]+pair[1][2]/2),
            (pair[0][1]+pair[0][3]/2)-(pair[1][1]+pair[1][3]/2)))
        forward = {}
        box = left
        for j in range(a,b):
            box = move(box,grays.get(j-1),grays.get(j))
            if box is None:
                break
            forward[j]=box
        backward = {}
        box = right
        for j in range(b-1,a-1,-1):
            box = move(box,grays.get(j+1),grays.get(j))
            if box is None:
                break
            backward[j]=box
        for j in range(a,b):
            f,r = forward.get(j),backward.get(j)
            if f is not None and r is not None and _match_box(f,r):
                # Cover both estimates; never average into a smaller, unsafe box.
                x1=min(f[0],r[0]);y1=min(f[1],r[1])
                x2=max(f[0]+f[2],r[0]+r[2]);y2=max(f[1]+f[3],r[1]+r[3])
                masks[j].append(_clamp([x1,y1,x2-x1,y2-y1],width,height))
            elif f is not None:
                masks[j].append(f)
            elif r is not None:
                masks[j].append(r)
    return masks




def _head_box(face, width, height):
    """Expand a face detection to approximate the whole head (hair/ears/chin).

    This is a geometric estimate, not a trained head or pose detector.
    """
    x, y, w, h = face
    return _clamp([x - .25*w, y - .48*h, 1.50*w, 1.68*h], width, height)


def _head_tracking_pass(source, start, width, height, masks, fps, raw_detections=None):
    """Conservative full-head tracking driven by fresh detections and LK motion.

    Crucially, interpolated/repaired masks are NEVER used as detector anchors.
    Predictions are additive and marked uncertain when motion confidence fails.
    """
    if not masks:
        return masks, []
    source_boxes = raw_detections if raw_detections is not None else masks
    anchors = [(_head_box(boxes[0], width, height) if boxes else None)
               for boxes in source_boxes[:len(masks)]]
    anchors.extend([None] * (len(masks)-len(anchors)))
    uncertain = []
    previous_gray = None
    last_head = None
    last_confirmed = -100000
    consecutive_failures = 0
    # Short prediction window. Do not silently mask a stale background region.
    max_unconfirmed = max(1, round(fps * 1.8))
    frames = _frames(source, start, width, height)
    try:
        for i, frame in enumerate(frames):
            if i >= len(masks):
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            anchor = anchors[i]
            predicted = None
            if last_head is not None and previous_gray is not None and i-last_confirmed <= max_unconfirmed:
                x,y,w,h = last_head
                region = np.zeros_like(previous_gray)
                # Track features within the upper head and nearby silhouette.
                x1=max(0,int(x+w*.10));y1=max(0,int(y+h*.08))
                x2=min(width,int(x+w*.90));y2=min(height,int(y+h*.88))
                if x2>x1 and y2>y1:
                    region[y1:y2,x1:x2]=255
                    points=cv2.goodFeaturesToTrack(previous_gray,maxCorners=100,
                            qualityLevel=.012,minDistance=4,mask=region)
                    if points is not None and len(points)>=6:
                        nxt,valid,_=cv2.calcOpticalFlowPyrLK(previous_gray,gray,points,None,
                                                  winSize=(27,27),maxLevel=3)
                        if nxt is not None and valid is not None:
                            good=valid.ravel()==1
                            if int(good.sum())>=6:
                                shifts=nxt[good,0]-points[good,0]
                                dx,dy=np.median(shifts,axis=0)
                                deviation=np.linalg.norm(shifts-[dx,dy],axis=1)
                                if (np.isfinite(dx) and np.isfinite(dy)
                                        and np.median(deviation)<max(7,min(w,h)*.18)
                                        and abs(dx)<max(28,w*.65)
                                        and abs(dy)<max(28,h*.75)):
                                    predicted=_clamp([x+dx,y+dy,w,h],width,height)
            if anchor is not None:
                # Fresh detection overrides drift. Keep a motion prediction too
                # when it plausibly overlaps, covering rapid head rotation.
                if predicted is not None and _match_box(predicted,anchor):
                    masks[i].append(predicted)
                masks[i].append(anchor)
                last_head=anchor
                last_confirmed=i
                consecutive_failures=0
            elif predicted is not None:
                masks[i].append(predicted)
                last_head=predicted
                consecutive_failures=0
            else:
                consecutive_failures+=1
                uncertain.append(i)
                # A very short conservative hold for brief optical-flow failures.
                # This is flagged as uncertain, not treated as verified coverage.
                if last_head is not None and consecutive_failures<=max(2,round(fps*.12)):
                    masks[i].append(last_head)
                else:
                    last_head=None
            previous_gray=gray
    finally:
        frames.close()
    return masks, uncertain

def _apply_boxes(frame, boxes, strength, manual=False):
    height, width = frame.shape[:2]
    output = frame.copy()
    for box in boxes:
        x, y, w, h = _clamp(box, width, height)
        pad = .40 if not manual else .35
        px, py = int(w*pad), int(h*pad)
        x1,y1,x2,y2 = max(0,x-px),max(0,y-py),min(width,x+w+px),min(height,y+h+py)
        roi = output[y1:y2,x1:x2]
        if not roi.size:
            continue
        if strength == 'Maximum':
            roi[:] = (15,15,15)
        else:
            block = max(12, min(roi.shape[:2])//(12 if strength=='Medium' else 3))
            tiny = cv2.resize(roi,(max(1,roi.shape[1]//block),max(1,roi.shape[0]//block)),interpolation=cv2.INTER_AREA)
            roi[:] = cv2.resize(tiny,(roi.shape[1],roi.shape[0]),interpolation=cv2.INTER_NEAREST)
    return output


def analyze_privacy_masks(source, start, end, strength="Strong", manual_box=None, on_progress=None):
    """Compute the exact automatic masks shared by preview and export."""
    w,h,fps = _video_info(source)
    max_frames = max(1,round((end-start)*fps))
    obscurer = Obscurer(strength,manual_box)
    raw = []
    frames = _frames(source,start,w,h)
    try:
        for frame in frames:
            if len(raw) >= max_frames:
                break
            obscurer.process(frame)
            raw.append(list(obscurer.last_boxes))
            if on_progress and len(raw)%15==0:
                on_progress(min(20,int(len(raw)*20/max_frames)))
    finally:
        frames.close()
    if not raw:
        raise RuntimeError('No video frames decoded.')
    repaired = _repair_tracks(raw,fps,manual_box)
    repaired = _motion_bridge(source,start,w,h,repaired,fps)
    repaired, uncertain_head_frames = _head_tracking_pass(source,start,w,h,repaired,fps,raw)
    if uncertain_head_frames:
        import warnings
        warnings.warn(f"Full-head tracking lost confidence on {len(uncertain_head_frames)} frames; review export manually.", RuntimeWarning)
    # Zero masks may indicate an exposed face. Surface these times for review.
    uncovered = [i for i, boxes in enumerate(repaired) if not boxes]
    if uncovered:
        import warnings
        ranges = []
        start_i = previous = uncovered[0]
        for idx in uncovered[1:]:
            if idx != previous + 1:
                ranges.append((start_i / fps, (previous + 1) / fps))
                start_i = idx
            previous = idx
        ranges.append((start_i / fps, (previous + 1) / fps))
        details = ', '.join(f'{a:.2f}-{b:.2f}s' for a, b in ranges[:12])
        warnings.warn('Privacy review required: no face mask at ' + details +
                      (f' (and {len(ranges)-12} more ranges)' if len(ranges)>12 else ''), RuntimeWarning)
    return repaired, w, h, fps


def make_blurred_video(source,output,start,end,strength='Strong',on_progress=None,manual_box=None,corrections=None):
    """Two-stage processing: detect first, bridge short gaps, then render masks.

    Frames are decoded twice to avoid keeping high-resolution video in RAM.
    """
    repaired, w, h, fps = analyze_privacy_masks(source, start, end, strength, manual_box, on_progress)
    # Manual correction rectangles are clip-relative, frame-exact, and always
    # additive: automatic tracking can never remove a user-specified mask.
    for correction in (corrections or []):
        a = max(0, int(correction['start']))
        b = min(len(repaired)-1, int(correction['end']))
        x, y, bw, bh = correction['box']
        box = _clamp([x*w, y*h, bw*w, bh*h], w, h)
        for idx in range(a, b+1):
            repaired[idx].append(box)
    writer = cv2.VideoWriter(str(output),cv2.VideoWriter_fourcc(*'MJPG'),fps,(w,h))
    if not writer.isOpened():
        raise RuntimeError('Cannot initialize intermediate video encoder.')
    frames = _frames(source,start,w,h)
    count = 0
    try:
        for frame in frames:
            if count >= len(repaired):
                break
            writer.write(_apply_boxes(frame,repaired[count],strength,False))
            count += 1
            if on_progress and count%15==0:
                on_progress(min(40,20+int(count*20/len(repaired))))
    finally:
        frames.close()
        writer.release()
    if count != len(repaired):
        raise RuntimeError(f'Video decode changed between passes ({len(repaired)} vs {count} frames).')
    if on_progress:
        on_progress(40)
    return count/fps
