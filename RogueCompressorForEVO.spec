# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets'), ('models', 'models'), ('../licenses', 'licenses')]
binaries = [('../vendor/bin/ffmpeg.exe', 'bin'), ('../vendor/bin/ffprobe.exe', 'bin')]
hiddenimports = ['PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets']
tmp_ret = collect_all('cv2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Packaging fix: Qt uses Windows' unversioned ICU API forwarders. A foreign
# Poppler ICU on the build PATH exports version-suffixed symbols and cannot
# satisfy those imports. Resolve these OS libraries from Windows, as the
# original working onedir build does; do not ship the unrelated Poppler ICU.

# Only the Qt modules and platform/media/image plugins actually used by this
# QWidget application. No Qt Quick, PDF, Virtual Keyboard or software Mesa.
qt_modules = {'QtCore','QtGui','QtWidgets','QtNetwork','QtOpenGL','QtMultimedia','QtMultimediaWidgets'}
qt_dlls = {('Qt6'+n[2:]+'.dll').lower() for n in qt_modules}
qt_pyds = {(n+'.pyd').lower() for n in qt_modules}
qt_other = {'pyside6.abi3.dll','avcodec-63.dll','avformat-63.dll','avutil-61.dll','swresample-7.dll','swscale-10.dll','msvcp140.dll','msvcp140_1.dll','msvcp140_2.dll','vcruntime140.dll','vcruntime140_1.dll'}
qt_plugins = {'platforms/qwindows.dll','styles/qmodernwindowsstyle.dll','multimedia/ffmpegmediaplugin.dll','multimedia/windowsmediaplugin.dll','imageformats/qgif.dll','imageformats/qico.dll','imageformats/qjpeg.dll','networkinformation/qnetworklistmanager.dll','tls/qschannelbackend.dll','tls/qcertonlybackend.dll'}
def keep_binary(x):
    n=x[0].replace('\\','/').lower()
    if n in {'icuuc.dll','icudt78.dll','opengl32sw.dll'}:return False
    if n.startswith('pyside6/'):
        q=n[len('pyside6/'):]
        return q in qt_dlls | qt_pyds | qt_other or (q.startswith('plugins/') and q[len('plugins/'):] in qt_plugins)
    return True
a.binaries = [x for x in a.binaries if keep_binary(x)]
a.datas = [x for x in a.datas if not x[0].replace('\\','/').lower().startswith(('pyside6/translations/','pyside6/qml/','pyside6/resources/'))]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RogueCompressorForEVO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['rogue_compressor.ico'],
    version='version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='RogueCompressorForEVO',
)
