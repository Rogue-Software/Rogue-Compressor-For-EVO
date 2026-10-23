# Rogue Compressor For EVO

**Free Windows video compressor for evolutionary.org — Rogue Software**

Version **0.9.0-beta.1**, Windows 10/11 x64. Compress a workout clip of up to
60 seconds to an MP4 below 10 MB, with audio and portrait orientation retained.
An optional experimental face-masking workflow uses the existing v11.3 engine.

> **Automatic head masking is experimental and may miss frames. Always review the entire exported video before sharing. Rogue Compressor does not guarantee anonymity.**
>
> Facial features may remain visible in individual frames. Manual corrections
> may be necessary. If reliable anonymity matters, physically conceal your face
> before recording. Maximum privacy is the masking strength, not a guarantee
> that tracking will cover every frame.

Designed primarily for one person with a stationary camera. Keep your face
relatively stationary and your head inside the frame. Rapid bending, rotation,
occlusion, crowds, camera cuts and leaving/re-entering the frame can defeat
tracking. Unsupported footage is not privacy verified.

**Select your entire head, including hair and ears, with a little extra margin. Keep your head in frame throughout the recording.**

## Install

Download the installer or portable ZIP from the approved GitHub prerelease and
verify its SHA256 against SHA256SUMS.txt. No Python, FFmpeg, GPU, account,
subscription, AI API or internet connection is required for local processing.
All required runtime components and the existing small YuNet model are bundled.

Run `Rogue_Compressor_For_EVO_Setup_0.9.0-beta.1_win64.exe`. It installs per
user in Rogue Software/Rogue Compressor For EVO Beta, separately from the stable
release. The executable is unsigned; Windows may show a reputation warning.
Do not bypass a security block; report it. For portable use, extract the whole
ZIP and run RogueCompressorForEVO.exe. Keep its _internal folder beside it.
Close Rogue before uninstalling through Windows Installed apps.

Target: Windows 10/11 x64; final-package testing was performed on the existing
Windows 11 development PC. Fresh Windows and Windows 10 qualification have not
been executed. See TEST_RESULTS.md for precisely what was tested.

## How to Use

New to the app? Read the complete [beginner's guide (README.txt)](README.txt).
It is also included in the installation folder and at the portable ZIP's top
level, so instructions are available offline.

1. Click **Import Video** under **01 / SOURCE**, choose a local video, and
   use **Play** to check it is upright. The main preview shows the original.
2. Enter **IN** and **OUT** times in seconds under **PLAYBACK & CLIP SELECTION**.
   Keep more than 0 and at most 60 seconds; click **Preview Selected Clip**.
3. If desired, enable **Automatically blur detected faces**. For masking, click
   **Select Manual Face Mask**, draw around your entire head including hair,
   ears and a little extra margin, then click **Use this face mask**.
4. Open **Frame-by-frame Privacy Corrections** and wait for rendering. Use
   **Play / Pause**, the slider and the previous/next **Frame** buttons to review.
   For each affected frame, click **Correct this frame**, draw a rectangle over
   the exposed head, then **Save correction**. Corrections apply to individual
   frames during export; preview playback may not show the added rectangles.
5. Click **Approve reviewed clip** when finished. This permits export and does
   not certify privacy. Changing trim or initial selection requires a new review.
6. Choose **CPU — x264 (two-pass)** or leave **Auto** selected under **Video
   encoder**. Click **EXPORT MP4**, select a new filename and wait for completion.
7. Inspect the **entire exported MP4**, including audio and doubtful frames,
   before sharing. Correct and export again if needed. Physically cover your face
   before recording when reliable anonymity matters.

The encoder menu also displays a GPU option, but this beta's bundled FFmpeg
supplies CPU encoding only: selecting GPU reports no hardware encoder. No GPU
encoding is promised. The manual masking workflow uses a solid black rectangle
despite the checkbox's “blur” wording. Maximum privacy remains enabled internally
when masking is used; it does not guarantee tracking accuracy.

## Limitations and privacy

Automatic tracking has known misses, including visible facial features during
the barbell-lowering/re-entry test. This is a disclosed experimental limitation,
not evidence of anonymity. Full review and manual correction are required if
masking is used. A one-frame tail trim was measured in the BB export because of
the existing shortest-stream behavior. Temporary review videos can be large;
allow sufficient disk space and keep private recordings in private locations.

## Report bugs

Use this repository's Issues. Include Windows version, beta version, CPU,
input codec/dimensions/duration, steps and error text. Do not post private
videos, faces, personal paths or logs containing private information. Share
only a synthetic or explicitly consented reproducer with redistribution rights.

## Source and licences

Application source is MIT licensed; third-party components retain their own
licences. See THIRD_PARTY_NOTICES.txt and LICENSING_STATUS.md. Every binary
release must be accompanied by Rogue_Compressor_Third_Party_Sources_0.9.0-beta.1.zip
on the same release, including exact FFmpeg/x264, Qt/PySide and OpenCV wrapper
sources, build recipes and licence texts. Replaceable LGPL DLLs are not locked.
No R6–R15 experimental engine, private test footage or research data is included.

The corrected [licensing verification](LICENSING_VERIFICATION.md) records the
Python incorporated-software notice fixes, dependency audit and installed-package
checks. Application binaries are unchanged. [v0.9.0-beta.1 is now available as a
public prerelease](https://github.com/Rogue-Software/Rogue-Compressor-For-EVO/releases/tag/v0.9.0-beta.1).
See [publication verification](PUBLICATION_STATUS.md) for the public download checks.
