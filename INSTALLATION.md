# Installation and removal

Windows 10/11 x64 target; Windows 11 existing-host verification only. No external
Python/FFmpeg installation, GPU, account or runtime download is required.

1. Download installer or portable ZIP plus SHA256SUMS.txt from this release.
2. In PowerShell run `Get-FileHash -Algorithm SHA256 <downloaded-file>` and compare
   the complete hash with the matching line. A checksum detects corruption; it
   is not a digital publisher signature. The beta is unsigned.
3. Installer: run the EXE and use the per-user beta directory. Portable: extract
   all files to a writable folder, then open RogueCompressorForEVO.exe.
4. Use local input/output files and allow disk space for full-size review videos.
5. Close Rogue before uninstalling from Windows Installed apps. Portable removal
   means removing its extracted folder after closing it; keep your own exports.

Always review the entire exported video if using experimental face masking.
Facial features can remain visible. Physically conceal your face before recording
when reliable anonymity matters. See README.md for usage and limitations.
