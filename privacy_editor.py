"""Rogue privacy correction editor: manual masks applied to exact export frames."""
import subprocess
from collections import OrderedDict
import cv2
import numpy as np
from PySide6.QtCore import Qt, QRect, Signal, QThread, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QProgressBar,
                               QSlider, QSpinBox, QListWidget, QMessageBox, QScrollArea)
from face_blur import _video_info, _apply_boxes, analyze_privacy_masks, _clamp

class MaskAnalysisWorker(QThread):
    ready = Signal(object)
    failed = Signal(str)
    progress = Signal(int)
    def __init__(self, source, start, end, strength, manual_box):
        super().__init__()
        self.source, self.start_time, self.end_time = source, start, end
        self.strength, self.manual_box = strength, manual_box
    def run(self):
        try:
            masks, w, h, fps = analyze_privacy_masks(
                self.source, self.start_time, self.end_time, self.strength, self.manual_box,
                self.progress.emit)
            self.ready.emit(masks)
        except Exception as exc:
            self.failed.emit(str(exc))

class DrawLabel(QLabel):
    changed = Signal()
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(420,260)
        self.setMouseTracking(True)
        self.frame = None
        self.box = None
        self.origin = None
        self.overlay = []
    def set_frame(self, frame, boxes):
        self.frame=frame
        self.overlay=boxes
        self.update_image()
    def _geometry(self):
        if self.frame is None:return (0,0,1,1)
        h,w=self.frame.shape[:2]
        s=min(self.width()/w,self.height()/h)
        dw,dh=max(1,int(w*s)),max(1,int(h*s))
        return ((self.width()-dw)//2,(self.height()-dh)//2,dw,dh)
    def _point(self,pos):
        x,y,w,h=self._geometry()
        return (min(1.,max(0.,(pos.x()-x)/w)),min(1.,max(0.,(pos.y()-y)/h)))
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.frame is not None:
            self.origin=self._point(event.position());self.box=None
    def mouseMoveEvent(self,event):
        if self.origin is not None:
            x,y=self._point(event.position());ox,oy=self.origin
            self.box=[min(ox,x),min(oy,y),abs(x-ox),abs(y-oy)]
            self.update()
    def mouseReleaseEvent(self,event):
        if self.origin is not None:
            self.mouseMoveEvent(event);self.origin=None
            if self.box and self.box[2]>.015 and self.box[3]>.015:self.changed.emit()
    def update_image(self):
        if self.frame is None:return
        rgb=cv2.cvtColor(self.frame,cv2.COLOR_BGR2RGB)
        h,w=rgb.shape[:2]
        self.pix=QPixmap.fromImage(QImage(rgb.data,w,h,w*3,QImage.Format.Format_RGB888).copy())
        self.update()
    def paintEvent(self,event):
        if self.frame is None:return
        painter=QPainter(self)
        x,y,w,h=self._geometry()
        painter.drawPixmap(QRect(x,y,w,h),self.pix)
        for box in self.overlay:
            bx,by,bw,bh=box
            painter.setPen(QPen(Qt.GlobalColor.green,2))
            painter.drawRect(QRect(int(x+bx*w),int(y+by*h),int(bw*w),int(bh*h)))
        if self.box:
            bx,by,bw,bh=self.box
            painter.setPen(QPen(Qt.GlobalColor.red,3))
            painter.drawRect(QRect(int(x+bx*w),int(y+by*h),int(bw*w),int(bh*h)))
        painter.end()

class PrivacyEditor(QDialog):
    def __init__(self,source,start,end,strength,corrections,parent=None):
        super().__init__(parent)
        self.setWindowTitle('Rogue — Frame-by-frame privacy corrections')
        self.resize(950,790)
        self.source=str(source);self.start=float(start);self.end=float(end)
        self.w,self.h,self.fps=_video_info(source)
        self.count=max(1,round((self.end-self.start)*self.fps))
        self.strength=strength
        self.manual_box=getattr(parent, "manual_box", None)
        self.auto_masks=None
        self.analysis_failed=False
        self.corrections=[dict(c) for c in corrections]
        self.cache=OrderedDict()
        root=QVBoxLayout(self)
        root.addWidget(QLabel('Automatic blur is shown on each frame. Drag over an EXPOSED head to correct it.'))
        mode_row=QHBoxLayout()
        self.blurred=QCheckBox('Show blurred preview (automatic + manual)')
        self.blurred.setChecked(True)
        self.blurred.toggled.connect(lambda _:self.show_frame(self.seek.value()))
        mode_row.addWidget(self.blurred)
        self.outlines=QCheckBox('Show mask outlines')
        self.outlines.toggled.connect(lambda _:self.show_frame(self.seek.value()))
        mode_row.addWidget(self.outlines)
        root.addLayout(mode_row)
        self.analysis_label=QLabel('Analyzing automatic head tracking...')
        root.addWidget(self.analysis_label)
        self.analysis_bar=QProgressBar();self.analysis_bar.setRange(0,100);root.addWidget(self.analysis_bar)
        self.view=DrawLabel();root.addWidget(self.view,1)
        self.info=QLabel();root.addWidget(self.info)
        self.seek=QSlider(Qt.Orientation.Horizontal);self.seek.setRange(0,self.count-1)
        self.seek.valueChanged.connect(self.show_frame);root.addWidget(self.seek)
        row=QHBoxLayout()
        for name,delta in [('◀ 1 frame',-1),('1 frame ▶',1),('◀ 10',-10),('10 ▶',10)]:
            b=QPushButton(name);b.clicked.connect(lambda checked=False,d=delta:self.seek.setValue(self.seek.value()+d));row.addWidget(b)
        root.addLayout(row)
        root.addWidget(QLabel('Correction range (clip-relative frame numbers, inclusive). Use a short interval, then review every frame.'))
        row=QHBoxLayout();self.first=QSpinBox();self.last=QSpinBox()
        for s in (self.first,self.last):s.setRange(0,self.count-1)
        row.addWidget(QLabel('From'));row.addWidget(self.first);row.addWidget(QLabel('To'));row.addWidget(self.last)
        b=QPushButton('Use current frame');b.clicked.connect(self.single);row.addWidget(b)
        b=QPushButton('Save mask for range');b.clicked.connect(self.add);row.addWidget(b)
        root.addLayout(row)
        self.items=QListWidget();self.items.setMaximumHeight(110);root.addWidget(self.items)
        row=QHBoxLayout()
        b=QPushButton('Delete selected correction');b.clicked.connect(self.delete);row.addWidget(b)
        b=QPushButton('Save corrections and close');b.clicked.connect(self.accept);row.addWidget(b)
        root.addLayout(row)
        root.addWidget(QLabel('Preview uses the SAME tracking masks as export. Review every frame and the exported MP4 before sharing.'))
        self.refresh();self.show_frame(0)
        self.seek.setEnabled(False)
        self.worker=MaskAnalysisWorker(self.source,self.start,self.end,self.strength,self.manual_box)
        self.worker.progress.connect(self.analysis_bar.setValue)
        self.worker.ready.connect(self._analysis_ready)
        self.worker.failed.connect(self._analysis_failed)
        QTimer.singleShot(0,self.worker.start)
    def _analysis_ready(self, masks):
        self.auto_masks=masks
        self.analysis_label.setText(f'Automatic head masks ready — {len(masks)} frames analyzed')
        self.analysis_bar.setValue(100)
        self.seek.setEnabled(True)
        self.show_frame(self.seek.value())
    def _analysis_failed(self, error):
        self.analysis_failed=True
        self.analysis_label.setText('Automatic analysis FAILED — blurred preview unavailable')
        QMessageBox.critical(self,'Automatic analysis failed',error)
        self.blurred.setChecked(False)
        self.blurred.setEnabled(False)
        self.seek.setEnabled(True)
    def reject(self):
        if self.worker.isRunning():
            QMessageBox.information(self,'Analysis running','Wait for automatic analysis to finish before closing.')
            return
        super().reject()
    def accept(self):
        if self.worker.isRunning():
            QMessageBox.information(self,'Analysis running','Wait for automatic analysis to finish before saving.')
            return
        super().accept()
    def single(self):
        self.first.setValue(self.seek.value());self.last.setValue(self.seek.value())
    def _frame(self,i):
        if i in self.cache:
            self.cache.move_to_end(i);return self.cache[i]
        t=self.start+i/self.fps
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-ss',f'{t:.7f}','-i',self.source,'-frames:v','1',
             '-vf',f'scale={self.w}:{self.h}','-pix_fmt','bgr24','-f','rawvideo','-']
        data=subprocess.run(cmd,capture_output=True,check=True).stdout
        if len(data)!=self.w*self.h*3:raise RuntimeError('Could not decode frame '+str(i))
        frame=np.frombuffer(data,np.uint8).reshape(self.h,self.w,3).copy()
        self.cache[i]=frame
        if len(self.cache)>12:self.cache.popitem(last=False)
        return frame
    def show_frame(self,i):
        self.info.setText(f'Frame {i+1}/{self.count}  •  clip {i/self.fps:.3f}s  •  source {self.start+i/self.fps:.3f}s')
        try:
            manual=[c['box'] for c in self.corrections if c['start']<=i<=c['end']]
            automatic=self.auto_masks[i] if self.auto_masks is not None and i<len(self.auto_masks) else []
            raw=self._frame(i)
            manual_pixels=[_clamp([b[0]*self.w,b[1]*self.h,b[2]*self.w,b[3]*self.h],self.w,self.h) for b in manual]
            if self.blurred.isChecked() and self.auto_masks is not None:
                shown=_apply_boxes(raw,list(automatic)+manual_pixels,self.strength,self.manual_box is not None)
            else:
                shown=raw
            overlay=[]
            if self.outlines.isChecked():
                overlay=[[b[0]/self.w,b[1]/self.h,b[2]/self.w,b[3]/self.h] for b in automatic]
                overlay+=manual
            self.view.box=None
            self.view.set_frame(shown,overlay)
            if self.auto_masks is not None:
                self.info.setText(self.info.text()+f'  •  {len(automatic)} automatic / {len(manual)} manual mask(s)')
        except Exception as exc:QMessageBox.warning(self,'Frame decode failed',str(exc))
    def add(self):
        box=self.view.box
        if not box or box[2]<.015 or box[3]<.015:
            QMessageBox.warning(self,'Select a head','Drag a rectangle around the head first.');return
        a,b=self.first.value(),self.last.value()
        if b<a:QMessageBox.warning(self,'Invalid range','End frame must be >= start frame.');return
        self.corrections.append({'start':a,'end':b,'box':[float(v) for v in box]})
        self.refresh();self.show_frame(self.seek.value())
    def delete(self):
        i=self.items.currentRow()
        if i>=0:self.corrections.pop(i);self.refresh();self.show_frame(self.seek.value())
    def refresh(self):
        self.items.clear()
        for c in self.corrections:
            self.items.addItem(f"Frames {c['start']+1}–{c['end']+1} ({c['start']/self.fps:.2f}–{c['end']/self.fps:.2f}s) — manual head mask")
