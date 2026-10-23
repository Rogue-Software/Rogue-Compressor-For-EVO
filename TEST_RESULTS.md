# Final-package test results — 0.9.0-beta.1

Executed 2026-10-23 on the existing Windows 11 Home x64 development PC,
Ryzen 7 5800X. This is existing-host testing, not a fresh Windows certification.
The v11.3 application/tracker Python files are byte-identical to the preserved
user-tested source; changes concern packaging, dependencies and documentation.

| Test | Executed result |
|---|---|
| Inno Setup installer | Built; silent installation to a new QA directory exited 0 |
| Installed application | Original branded window rendered; all packaged file hashes matched |
| Portable ZIP | CRC and every extracted file hash checked; extracted EXE launched and rendered |
| Uninstall | With QA app closed, exit 0; QA installation directory removed |
| No external Python/FFmpeg on PATH | Packaged EXE launched and completed export with Windows-only PATH; loaded Python/Qt DLLs came from its _internal tree |
| Bundled FFmpeg/FFprobe | Version/protocol/encoder inspection, decode and actual application export succeeded; CLI network protocols disabled at build time |
| Original HEVC input | Imported and played upright; initial/ended black frames were resolved by observing active playback, no packaging change required |
| Manual selection | Full head selected in actual packaged GUI |
| v11.3 review | Entire 924-frame source rendered; playback, seeking and single-frame stepping executed |
| Frame correction | Added/saved correction at zero-based frame 815; larger black rectangle present in actual export at that frame |
| Compression | Full BB application export: 9,029,513 bytes, below 10,000,000 bytes |
| Orientation | H.264 output decoded at 1080×1920, upright |
| Audio | AAC retained; input/output mono 8 kHz comparison correlation 0.988477; measured lag 0.0 s. No separate human listening test claimed |
| Duration | 923 output frames vs 924 source frames, existing shortest-stream one-frame tail trim disclosed |
| Maximum privacy | Unchanged source forces Maximum internally when masking is enabled; GUI masked review/export executed |
| Facial exposure inspection | Actual exported contact sheet and all head crops 800–922 inspected; visible facial features at 910–922 confirmed. Frame 815 correction applied. No all-frame or zero-exposure claim |
| Model/data exclusion | Only existing 232,589-byte MIT YuNet model. No experimental models, test clips, face images, research data or caches in release payload |
| Preservation | 116 previously frozen source/release/research file hashes matched |
| Source obligations | Exact source archives, configuration/build recipes and original notices assembled as required accompanying source ZIP; Qt DLL provenance and OpenCV wrapper Git-blob match verified |

After the executed GUI tests, only a plain-text offline README, corrected model
README and a copy of its MIT licence were added. The final installer was rebuilt;
final installer/file-equivalence/uninstall results are recorded again locally.
Executable, tracker, runtime binaries and export code did not change.

## Not executed / limits

- Fresh Windows 10/11 installation with Python never installed: no clean VM or
  Windows Sandbox available on this host. PATH isolation is not equivalent.
- Physically disconnected-network installation/export: not executed. Local
  processing succeeded using bundled tools; CLI network support is disabled,
  but this is not a claim that every Qt/OpenCV library lacks network capability.
- GPU encoding, non-x64 Windows and every input codec: not qualified.
- Independent second-person facial-pixel privacy review: not performed. The
  final candidate's earlier frames were decoded but not all visually re-reviewed.
- Windows reputation/SmartScreen behavior on an unrelated PC: not qualified.

An earlier candidate's complete 923-frame crop review also found facial misses;
those results remain preserved privately. No tracking algorithm changes were
made to hide those failures. The final export's tail misses are consistent with
the disclosed experimental limitation. Keep the face relatively stationary and
head inside the frame; physically conceal it when reliable anonymity matters.

## Release decision

Core installer, launch, compression, portrait output, audio and correction
workflow tests passed on this host. Identified licence/source-distribution
requirements are addressed by the accompanying notices and corresponding-source
asset. Suitable for publisher approval as a clearly labelled experimental beta,
with the unexecuted environment tests and known tracking misses disclosed.
This is not an anonymity certification. No public publication is authorized yet.

## Beginner guide packaging update

A dedicated plain-text README.txt now covers installation, interface features,
IN/OUT selection, optional masking, full-head selection, individual frame
corrections, export, mandatory exported-video review, troubleshooting and Issues.
The homepage has a How to Use section and links to that guide.

Instructions were checked against unchanged main.py, v113_review.py and
compressor.py and the already executed packaged-interface workflow. The guide
explicitly distinguishes the visible GPU menu option from the CPU-only encoder
supplied in this beta, and saved-frame corrections from preview playback.
No new GPU functionality or tracking capability is claimed.

The updated installer was actually installed to a new QA folder. All 521 payload
file hashes matched, including README.txt beside the installed EXE; its bytes
match the repository guide. The updated portable ZIP passed CRC and all payload
hash checks, with identical README.txt copies at its top level and beside the
EXE. Closed-app uninstall exited 0 and removed the QA directory.

Only the bundled guide changed from the prior candidate: the other 520 payload
files, including every executable, runtime DLL, model and application file, are
unchanged. Previous export/audio/interface results remain applicable; the full
video workflow was not unnecessarily rerun for this text-only change. Previous
artifacts, checksums and reports remain preserved in the earlier staging folder.
