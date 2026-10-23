"""Packaging-only hook: expose bundled FFmpeg binaries to unchanged app code."""
import os
import sys
from pathlib import Path
base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
bin_dir = base / 'bin'
if bin_dir.is_dir():
    os.environ['PATH'] = str(bin_dir) + os.pathsep + os.environ.get('PATH', '')
