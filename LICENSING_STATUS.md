# Third-party redistribution record

The release supplies original notices/licences in the installed _internal/licenses
folder and a corresponding-source ZIP beside the binaries. That ZIP is a required
release asset, not an optional future download promise. No source-offer-only
substitute is used. Application source remains MIT; that does not relicense
third-party components.

| Component | Binary/source basis | Distribution handling |
|---|---|---|
| FFmpeg/FFprobe 9.0.2 + x264 pinned c24e06c | Built here from included unmodified sources | GPLv3+, full sources/configuration/build script supplied; separate CLI executables |
| Qt/PySide/Shiboken 6.12.0 | Official PyPI wheel DLL hashes verified; official source SHA256 verified | LGPLv3, replaceable dynamic libraries, application source/relinking instructions, Qt source/build/provisioning scripts and all collected attribution/licence files |
| Qt FFmpeg 9.0.1 + zlib 1.3.1 | Version/configuration queried from DLL; Qt source attribution agrees | LGPL2.1+ and zlib; exact source archives and upstream build scripts supplied |
| OpenCV FFmpeg wrapper | Exact binary Git blob matches official OpenCV binary commit | Matching source branch archives/build scripts verified by Git blob; FFmpeg n4.4.5 LGPL, BSD libvpx/aom, wrapper notices supplied |
| YuNet | Existing 232,589-byte model | MIT notice retained |
| CPython / NumPy / OpenCV | Build environment distribution versions | Original licences and included dependency notices retained |
| PyInstaller | 6.22.3 bootloader | GPL with distribution exception retained |
| LLVM/MinGW static runtimes | Source-built media tools | Original runtime notices retained |
| Microsoft C++ runtime | Unmodified distribution DLLs | Microsoft redistributable list and installed REDIST notice supplied |

Unused Qt QML/PDF/VirtualKeyboard modules and Mesa software OpenGL are excluded;
no GPL-only Qt addon is required by this QWidget application. Licence texts are
collected from original source archives, not reconstructed summaries.

LGPL library replacement is allowed under _internal/PySide6 and shiboken6;
there is no signature check or prohibition on reverse engineering for debugging
library modifications. ABI changes may require rebuilding bindings/app using
provided application source and upstream build instructions.

Sources/provenance/hashes and exact FFmpeg build configurations are in the source
ZIP. Microsoft runtime redistribution reference:
https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution
Qt licensing: https://doc.qt.io/qt-6/licensing.html
FFmpeg: https://ffmpeg.org/legal.html

The release licence/source-distribution packaging obligations identified during
this review are addressed by these accompanying assets. Keep those assets and
notices intact on publication and redistribution. Do not substitute old large
Gyan builds or unrelated development models without a new component review.


## Corrected final verification

The intervening publication audit identified missing Python incorporated-software
notices. That failed report remains preserved. The current licensing snapshot
resolves libmpdec/Expat and adds the complete Python/native notice coverage,
exact OpenSSL/libffi/XZ materials and explicit Qt LicenseFile targets. See
[LICENSING_VERIFICATION.md](LICENSING_VERIFICATION.md) for actual evidence and
executed packaging checks. No known mandatory requirement remains unresolved
in this reviewed candidate. The release is still private/draft pending approval.
