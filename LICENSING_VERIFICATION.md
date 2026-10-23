# Licensing verification — 0.9.0-beta.1, corrected 2026-10-23

**Cleared for final publication approval: no known unresolved mandatory licensing
or corresponding-source requirement remains in the reviewed release materials.**
The repository remains private and the existing release remains an unpublished
prerelease draft. This record supersedes the earlier failed publication review;
the failed report and previous beta assets are preserved as rollback evidence.

## Missing Python notices resolved

- Queried the installed Python 3.14.7 runtime: libmpdec **4.0.0**, Expat **2.8.2**.
  SHA256 checks show the packaged _decimal.pyd, pyexpat.pyd and python314.dll
  are the same binaries as that runtime. libffi/OpenSSL DLL hashes also match.
- Obtained the official Python 3.14 incorporated-software licensing documentation.
  Its libmpdec and Expat notice blocks match the installed 3.14.7 documentation
  verbatim. Complete copyright, conditions, permissions and disclaimers are
  reproduced in THIRD_PARTY_NOTICES.txt and the bundled licensing folder.
- Obtained exact upstream libmpdec 4.0.0 COPYRIGHT.txt and Expat 2.8.2 COPYING.
  These are copied byte-for-byte, including their newer copyright lines, and
  appended verbatim to THIRD_PARTY_NOTICES.txt alongside the historical Python
  documentation notices. Source URLs and download hashes are retained.
- Preserved all **28** licence/acknowledgement blocks from the official Python
  page. The page describes its incorporated-software list as incomplete, so
  the audit also inspected the matching unmodified CPython 3.14.7 source.
- Collected **91** original native-source copyright/licence comment blocks,
  including HACL*/KreMLin MIT notices used by built-in hash functions. The full
  official CPython source archive accompanies the release sources.

Official notice sources:
- https://docs.python.org/3.14/license.html#libmpdec
- https://docs.python.org/3.14/license.html#expat
- https://raw.githubusercontent.com/python/cpython-source-deps/mpdecimal-4.0.0/COPYRIGHT.txt
- https://raw.githubusercontent.com/libexpat/libexpat/R_2_8_2/expat/COPYING

## Complete packaged-dependency review

The actual payload inventory classifies **129 executables, DLLs, native Python
extensions and the model**. The build's pure-Python dependency closure contains
only PyInstaller, NumPy, PySide6, Shiboken6 and OpenCV, in addition to Python's
standard library and the application. No runtime dependency was added.

| Component | Actual checks and supplied materials |
|---|---|
| FFmpeg/FFprobe 9.0.2 + pinned x264 | Existing source-built GPLv3+ executables remain unchanged; exact FFmpeg/x264 sources, configuration headers/makefiles, build script and GPL text remain in the required source ZIP |
| Qt/PySide/Shiboken 6.12.0 | Official-wheel provenance from previous review retained; dynamically replaceable LGPL libraries; exact sources and provisioning/build scripts retained; all **76** explicit attribution LicenseFile references resolved and copied from the official archives, with zero unresolved references |
| Qt FFmpeg 9.0.1 + zlib 1.3.1 | Previous actual DLL licence/configuration query and exact matching sources retained; LGPL2.1+ / zlib notices present |
| OpenCV 4.11.0 and FFmpeg wrapper | Apache/third-party notice files present; wrapper's verified upstream binary/source Git-blob relationship retained, including matching FFmpeg/libvpx/aom/wrapper sources/build scripts |
| CPython + incorporated native components | PSF/Windows terms, complete documentation blocks, exact libmpdec/Expat/libffi notices, XZ COPYING and native-source notices present. XZ COPYING identifies liblzma as public domain; XZ CLI utilities are not shipped |
| OpenSSL 3.5.7 and additional 3.6.4 DLLs | Versions/copyrights inspected; both exact Apache-2.0 licences supplied. Complete upstream trees contain no separate NOTICE file. Build-only Perl components are not shipped |
| NumPy/OpenBLAS/LAPACK/GCC runtime | Existing full distribution notice tree retained, including BSD notices, GCC Runtime Library Exception and GPL text; exception permits distribution of the compiled runtime combination |
| YuNet | Existing MIT licence, model hash/size retained; no research model included |
| LLVM/MinGW static runtime | Original LLVM exception/runtime and MinGW notices retained; toolchain executables are not shipped |
| Microsoft C++/UCRT/API-set runtime | Original unmodified DLLs retained; Microsoft copyright/version metadata checked; official distributable list, UCRT deployment reference and installed Windows SDK licence/third-party notices included. UCRT deployment is a supported Microsoft Windows redistribution mechanism; on Windows 10/11 the OS UCRT takes precedence |
| PyInstaller / Inno Setup | Existing bootloader exception retained; installed Inno licence included. No PyInstaller application rebuild performed; only Inno installer-container compilation |
| Qt static third-party components | Original attribution/notice files retained and explicit file targets checked; FreeType credit added. IJG credit is present in OpenCV's existing complete third-party notice file |

All **14 prior source archives** compare unchanged against the previous source
asset. The additional CPython archive matches its official download hash. The
new source ZIP passed CRC and every recorded internal SHA256 check. Application
source remains MIT; third-party licences remain applicable to their components.
No restriction is imposed on debugging, reverse engineering for LGPL library
modifications or replacing the dynamic LGPL libraries. Application source and
library build/replacement instructions remain supplied.

## Repackaging and executed verification

- Copied the validated application payload; **all 129 binaries/model files are
  byte-identical** to the previous candidate. Source Python files, tracker, UI,
  compression code and executable code are unchanged. Only licence materials
  and distribution documentation changed. Prior artifacts are preserved in a
  rollback directory and their hashes were checked.
- Recompiled the Inno installer container using the existing executable payload.
- Actually installed that installer to a new QA folder: **exit 0**. Checked all
  **584 installed payload hashes**, including root/internal notices. Exact-version
  Expat and libmpdec files matched the official downloaded bytes after installation.
- Portable ZIP passed CRC and all **584** payload hashes, including notices.
  README.txt is still present at ZIP top level and beside the EXE.
- Uninstalled the closed QA application: **exit 0**, QA directory removed.
- Preserved **116** previously frozen production/research hashes.
- Regenerated SHA256SUMS.txt for installer, portable ZIP, required source ZIP and
  separately downloadable README.txt. Draft upload digests are checked separately
  against these local files before final handoff.

The previously executed compression/audio/orientation/correction workflow remains
applicable to the unchanged binaries. It was not rerun for a licence-text change.
Fresh Windows/Windows 10 and physically disconnected-network tests remain
unexecuted as documented in TEST_RESULTS.md; no new such test is claimed.

## Distribution conditions and unresolved requirements

**Known unresolved mandatory licensing requirements: none after the above checks.**
Publish the required corresponding-source ZIP alongside both binary downloads,
retain all bundled notices and the source materials, and retain replaceability
and debugging rights for LGPL components. The current source repository must
remain available with the release's v0.9.0-beta.1 source commit/tag. Do not replace
the source asset with only GitHub's application-source archive.

Automatic masking remains experimental. Facial features can remain visible in
individual frames; always review the entire export. This licensing clearance is
not a privacy certification. Publication remains subject to the user's final
approval; no public publication has been performed.
