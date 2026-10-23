# Build the beta

Use Windows x64 Python 3.14.7 and requirements-build.txt. Install Inno Setup 6.
Place repository application files/assets/models into a source/ folder, licences
from the corresponding-source ZIP into sibling licenses/, and build FFmpeg using
that ZIP's instructions into sibling vendor/bin/{ffmpeg,ffprobe}.exe.
From source run `python -m PyInstaller --noconfirm --distpath ../portable --workpath ../build RogueCompressorForEVO.spec`.
Copy LICENSE and THIRD_PARTY_NOTICES.txt beside the portable EXE, then compile
installer.iss with ISCC. No test videos, caches or experimental models belong
in the distribution. Preserve the Qt allowlist and Windows ICU packaging fix.
The original application/tracking Python files are unchanged v11.3.
