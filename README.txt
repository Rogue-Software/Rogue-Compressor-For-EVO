ROGUE COMPRESSOR FOR EVO
Beginner's Guide | Version 0.9.0-beta.1 | Rogue Software
======================================================================

IMPORTANT PRIVACY WARNING
Automatic head masking is experimental and may miss frames. Always
review the entire exported video before sharing. Rogue Compressor
does not guarantee anonymity.

Tracking can drift or be lost, leaving facial features visible in
individual frames. Keep your head inside the frame and minimize sudden
head movements. If anonymity is important, physically cover your face
before recording. Manual corrections may still be necessary.

1. ABOUT ROGUE COMPRESSOR
----------------------------------------------------------------------
Rogue Compressor For EVO is a free, offline Windows video compressor
developed by Rogue Software for sharing workout videos on
evolutionary.org. It creates small MP4 files and offers optional,
experimental head masking. It is not a guaranteed anonymization tool.

Designed primarily for one person recording with a stationary camera.
Keep your face relatively stationary and your whole head in frame.
Crowds, camera cuts, complete exits/re-entry, bending, rotation and
occlusions can defeat automatic tracking.

2. FEATURES AND REQUIREMENTS
----------------------------------------------------------------------
- Import a local video, play/pause it and preview the selected section.
- Set IN and OUT times to keep a clip of more than 0, up to 60 seconds.
- Export an H.264 MP4 below 10 MB; the interface targets 9.5 MB.
- Preserve source audio, when present, as AAC in the exported MP4.
- Optional experimental automatic head masking after manual selection.
- Select your whole head once and add frame-by-frame privacy corrections.
- Maximum privacy masking strength is always used internally when
  masking is enabled. It does not guarantee successful tracking.
- A Video encoder menu offers Auto, CPU and GPU options. This beta's
  bundled media tools supply CPU encoding only. Select
  "CPU - x264 (two-pass)" (shown with a dash in the menu), or leave Auto
  selected to use CPU. The visible GPU option is not usable in this
  package; it reports that no hardware encoder is available. A GPU is
  not required. Do not download or replace bundled tools to use it.

Windows 10/11 x64 is the target platform. Testing was performed on an
existing Windows 11 PC; fresh-machine and Windows 10 tests have not
been performed. Allow space for temporary, full-resolution review
videos, which can be much larger than the final MP4.

No separate Python, FFmpeg, AI service, account or subscription is
needed. Local video processing works without an internet connection.
The optional "Get Muscle Memory" link opens an external website only
if you choose to click it. GitHub downloads and bug reporting need
internet access; they are not required for local processing.

3. INSTALL OR USE THE PORTABLE VERSION
----------------------------------------------------------------------
Installer:
  1. Download Rogue_Compressor_For_EVO_Setup_0.9.0-beta.1_win64.exe
     from the official GitHub release. Compare its SHA256 checksum
     with SHA256SUMS.txt if you know how to verify downloads.
  2. Run the installer and follow its prompts. The default location is
     your user's Programs/Rogue Software/Rogue Compressor For EVO Beta
     folder. The beta installs separately from the stable release.
  3. Open Rogue Compressor For EVO Beta from the Start menu.
     This README.txt is also in the installation folder beside the EXE.

Portable:
  1. Download Rogue_Compressor_For_EVO_Portable_0.9.0-beta.1_win64.zip.
  2. Right-click it and choose Extract All. Choose a writable folder.
  3. Open the extracted RogueCompressorForEVO folder and double-click
     RogueCompressorForEVO.exe. Do not run it inside the ZIP or move
     only the EXE. Its _internal folder must remain beside it.
     A copy of this guide is at the ZIP's top level and beside the EXE.

The beta is unsigned, so Windows may display a publisher/reputation
warning. Do not bypass a security block; report the exact warning.
Close Rogue before uninstalling it through Windows Installed apps.
Your source videos and chosen export files are separate from the app.

4. HOW TO USE - YOUR FIRST VIDEO
----------------------------------------------------------------------
Step 1 - Import
  Click "Import Video" in "01 / SOURCE" and select a local video.
  Click Play to view it; use Pause, Stop and the playback slider as
  needed. Confirm that it plays upright. The main playback area shows
  the original video, not the privacy-masked result.

Step 2 - Choose the section to keep
  In "PLAYBACK & CLIP SELECTION", enter the starting time in IN and
  ending time in OUT. Both values are seconds measured from the start
  of the source. For example, IN 10.00 s and OUT 40.00 s keeps 30 seconds.
  OUT must be after IN, and the selected duration must not exceed
  60 seconds. Click "Preview Selected Clip" to check your selection.

Step 3 - Choose whether to use experimental masking
  In "02 / FACE PRIVACY", use "Automatically blur detected faces" to
  enable or disable masking. If disabled, the export will not hide your
  face. If enabled, complete Steps 4 and 5 before exporting.

Step 4 - Select your entire head
  Click "Select Manual Face Mask". The selection window shows the
  frame at your IN time. Drag a rectangle around your entire head,
  including hair, ears and a little extra margin, then click
  "Use this face mask". If the head is not visible at that time, choose
  a suitable IN time and select again.

  Select your entire head, including hair and ears, with a little extra
  margin. Keep your head in frame throughout the recording.

  Although the checkbox says "blur", this manual v11.3 review workflow
  covers the tracked region with a solid black rectangle.

Step 5 - Review and correct
  Click "Frame-by-frame Privacy Corrections" and wait for rendering.
  In "Rogue - v11.3 Mask Review", click "Play / Pause" to watch.
  Use the slider to seek and the previous/next Frame buttons to step
  through doubtful frames. Pay particular attention to bending,
  lifting, barbell lowering, quick motion and the beginning/end.

  To correct a frame:
    a. Pause or step to the frame, then click "Correct this frame".
    b. Draw a rectangle over the entire exposed head with some margin.
    c. Click "Save correction". Check the saved-frame message.
    d. Repeat for other affected frames; a correction protects only
       the frame where it was saved, not the surrounding sequence.

  When finished, click "Approve reviewed clip". This accepts the
  review for export; it does not certify that the video is anonymous.
  Saved correction rectangles are applied during export. Playback of
  the original rendered preview may not show those added rectangles.
  Verify them in the final exported MP4.

  Changing the trim or initial selection requires another review.
  Finish corrections and approve within the same review session;
  reopening the editor creates a new review. There is no saved-project
  workflow documented for this beta.

Step 6 - Export
  In "03 / EXPORT", select "CPU - x264 (two-pass)" from "Video encoder",
  or leave Auto selected. Click "EXPORT MP4" and choose a writable
  location and a NEW filename ending in .mp4. Do not choose the source
  file or an existing export: the app does not overwrite them.
  Wait for "Export complete" and the saved-file size message.

Step 7 - Check before sharing
  Open the saved MP4 in your video player. Watch the ENTIRE export,
  check the audio and orientation, and inspect doubtful moments
  frame by frame. Do not rely only on the app preview. If any facial
  feature remains visible, correct and export again to a new filename,
  or do not share it. Physically conceal your face before recording
  when reliable anonymity matters.

5. TROUBLESHOOTING
----------------------------------------------------------------------
Incorrect orientation:
  Let playback start before judging a black preview. Check orientation
  in the original, selection window and final export. Portrait footage
  with rotation metadata was tested, but not every source format was.
  There is no manual Rotate button in this beta. If it remains wrong,
  stop before sharing; correct the source orientation in your recording
  or video-editing tool, then import it again. Report the source format.

Tracking drift or visible features:
  Keep the head in frame, avoid sudden motion and select the whole head
  at IN. Review every affected frame, save corrections and check the
  exported file. Tracking is experimental; repeated failures may make
  a recording unsuitable. Physical face concealment is the safer choice
  when anonymity matters. Do not assume Maximum privacy prevents drift.

Oversized masks:
  The tracker adds safety padding, so the black block can extend onto
  clothing or background. Select the whole head with a little margin,
  rather than a large area of the torso. Do not make the selection so
  small that hair, ears or moving head edges are uncovered. There is
  no padding/strength adjustment documented for this beta. Make a new
  selection and review again if necessary.

Slow processing:
  Full-resolution review rendering and CPU two-pass encoding take time.
  Wait for rendering to finish; keep enough free space for temporary
  videos, use a shorter section and close other heavy programs. The
  visible GPU option will not speed up this CPU-only beta package.
  No real-time performance is promised.

Failed export:
  Ensure IN/OUT select more than 0 and at most 60 seconds. With masking
  enabled, select the head and click "Approve reviewed clip" first.
  Choose CPU encoding, a new filename and a writable local folder;
  check free space. If the file cannot meet the size limit, try a shorter
  clip. Keep the complete _internal folder. If an error says FFmpeg is
  missing, re-extract/reinstall the official package; a separate FFmpeg
  or Python installation should not be necessary. Report the exact error
  if it continues. Do not delete or overwrite your only source recording.

Missing audio:
  Confirm that the source contains audio and your video player is not
  muted. The privacy-review window is for visual review and may be
  silent; check the actual exported MP4 for sound. Export preserves
  available source audio as AAC and cannot add sound to a silent source.
  If source sound is present but export sound is missing, report it with
  the source codec/format and selected times. There is no separate audio
  track selector documented for this beta.

6. SUPPORT, LICENCES AND KNOWN LIMITATIONS
----------------------------------------------------------------------
Repository: https://github.com/Rogue-Software/Rogue-Compressor-For-EVO
Report bugs: https://github.com/Rogue-Software/Rogue-Compressor-For-EVO/issues

Include beta version, Windows version, CPU, input format/dimensions,
selected times, steps to reproduce and the exact error. Do not upload
private videos, face images, personal paths or sensitive logs. Use only
synthetic or explicitly consented examples with redistribution rights.

Known tracking misses include visible facial features in individual
frames during the barbell-lowering/re-entry test. A one-frame tail trim
was also measured with the existing shortest-stream export behavior.
Fresh-machine, Windows 10 and physically disconnected-network tests
have not been executed. See the repository's TEST_RESULTS.md for detail.

Application source: MIT licence. Third-party components retain their
own licences. See LICENSE, THIRD_PARTY_NOTICES.txt, _internal/licenses
and the accompanying third-party corresponding-source ZIP on GitHub.

Rogue Software | Free local video compression for the EVO community
