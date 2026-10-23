# v0.9.0-beta.1 â€” public beta candidate

Rogue Software's free Windows compressor for evolutionary.org. Existing v11.3
application and tracker; no experimental R6â€“R15 integration or tracker changes.

- Up to 60-second local MP4 compression below 10 MB; audio and portrait support.
- Optional experimental masking, manual head selection and frame corrections.
- Maximum privacy masking strength retained internally.
- Self-contained installer and portable package, CPU x264 encoding.
- Source-built FFmpeg/FFprobe with network protocols disabled; reduced Qt payload
  and complete accompanying third-party sources/licences.

**Automatic head masking is experimental and may miss frames. Always review the entire exported video before sharing. Rogue Compressor does not guarantee anonymity.**

Facial features can be visible in individual frames; manual corrections may be
necessary. Keep the face relatively stationary and head in frame. Physically
conceal the face when reliable anonymity matters. This release is primarily a
compressor, not a guaranteed anonymization tool. Known tracking failures are
disclosed beta limitations, not claims of independently verified privacy.

Unsigned Windows x64 build. CPU encoding is supplied; GPU encoding is not
qualified. Clean-machine/Windows 10 and physical network-disconnection tests
have not been executed. See TEST_RESULTS.md for final-package evidence.

The installer, portable ZIP and corresponding-source ZIP must remain together
on the release. Checksums are in SHA256SUMS.txt. Publication requires publisher
approval; preparation as a private repository/draft does not constitute release.

A beginner-friendly README.txt is included beside the installed EXE and at the
portable ZIP top level, with verified interface steps and troubleshooting. The
GitHub homepage includes How to Use and a link to the complete guide.
