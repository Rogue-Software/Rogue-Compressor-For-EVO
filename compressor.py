"""FFmpeg two-pass, size-budgeted clip exporter (no GUI dependencies)."""
import os
import shutil
import subprocess
import tempfile
import re
from pathlib import Path

TARGET_BYTES = 9_500_000  # decimal MB; comfortably below 10,000,000 bytes



def available_encoders():
    """List candidate H.264 encoders advertised by the installed FFmpeg build.

    Hardware support is validated by an actual encode when exporting.
    """
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return ['libx264']
    proc = subprocess.run([ffmpeg, '-hide_banner', '-encoders'], capture_output=True, text=True)
    names = set(re.findall(r'^\s*[A-Z.]{6}\s+(\S+)', proc.stdout, re.MULTILINE))
    return ['libx264'] + [e for e in ('h264_nvenc', 'h264_amf', 'h264_qsv', 'h264_vaapi') if e in names]


def _encode_args(encoder, bitrate):
    common = ['-c:v', encoder, '-b:v', str(bitrate), '-pix_fmt', 'yuv420p']
    if encoder == 'libx264':
        return common + ['-preset', 'medium']
    if encoder == 'h264_nvenc':
        return common + ['-preset', 'p5', '-rc', 'vbr']
    if encoder == 'h264_amf':
        return common + ['-quality', 'balanced']
    if encoder == 'h264_qsv':
        return common
    if encoder == 'h264_vaapi':
        # VAAPI requires a hardware device and a hardware-frame upload path.
        # Do not offer it until device configuration is implemented.
        raise RuntimeError('VAAPI device setup is not implemented yet; choose CPU.')
    raise ValueError(f'Unsupported encoder: {encoder}')


def _run_encode(ffmpeg, video_input, audio_source, audio_start, duration,
                bitrate, audio_bps, encoder, partial, passlog, progress, blur_faces):
    base = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y']
    video_options = ['-t', str(duration), '-map', '0:v:0'] + _encode_args(encoder, bitrate)
    if encoder == 'libx264':
        for pass_num in (1, 2):
            args = base + video_input
            if pass_num == 2:
                args += ['-ss', str(audio_start), '-i', str(audio_source)]
            args += video_options + ['-pass', str(pass_num), '-passlogfile', passlog]
            if pass_num == 1:
                args += ['-an', '-f', 'null', os.devnull]
            else:
                args += ['-map', '1:a:0?', '-c:a', 'aac', '-b:a', str(audio_bps),
                         '-shortest', '-movflags', '+faststart', str(partial)]
            proc = subprocess.run(args, capture_output=True, text=True)
            if proc.returncode:
                raise RuntimeError(f'FFmpeg {encoder} pass {pass_num} failed:\n{proc.stderr[-2500:]}')
            if progress:
                progress((40 if blur_faces else 0) + int(pass_num * (25 if blur_faces else 45)))
    else:
        # Most hardware encoders do not support x264-style -pass 1/2.
        args = base + video_input + ['-ss', str(audio_start), '-i', str(audio_source)]
        args += video_options + ['-map', '1:a:0?', '-c:a', 'aac', '-b:a', str(audio_bps),
                                 '-shortest', '-movflags', '+faststart', str(partial)]
        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError(f'FFmpeg {encoder} failed:\n{proc.stderr[-2500:]}')
        if progress:
            progress(90)


def export_clip(source, destination, start, end, on_progress=None, blur_faces=False, blur_strength="Strong", manual_box=None, corrections=None, encoder="auto", reviewed=None):
    """Export a trimmed H.264/AAC MP4 below TARGET_BYTES or raise an error.

    Progress callback receives integer 0..100. Original is never modified.
    """
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg is not installed or is missing from PATH.')
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source == destination:
        raise ValueError('Output must not overwrite the input video.')
    duration = float(end) - float(start)
    if not (0 < duration <= 60):
        raise ValueError('Select a clip between 0 and 60 seconds.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Reserve space for container overhead and audio. Cap bitrate for small clips.
    audio_bps = 64000
    total_bps = int((TARGET_BYTES * 8 * 0.94) / duration)
    video_bps = max(50000, total_bps - audio_bps)
    with tempfile.TemporaryDirectory(prefix='rogue_export_') as tempdir:
        video_source = source
        video_start = start
        audio_source = source
        audio_start = start
        if blur_faces and reviewed is not None:
            from v113_review import apply_corrections
            reviewed_file, reviewed_corrections = reviewed
            video_source = Path(tempdir) / 'reviewed_corrected.avi'
            apply_corrections(reviewed_file, reviewed_corrections, video_source)
            video_start = 0
        elif blur_faces:
            from face_blur import make_blurred_video
            video_source = Path(tempdir) / 'faces_blurred.avi'
            duration = make_blurred_video(source, video_source, start, end, blur_strength, on_progress, manual_box, corrections)
            video_start = 0
        passlog = str(Path(tempdir) / 'pass')
        partial = Path(tempdir) / 'result.mp4'
        video_input = ['-ss', str(video_start), '-i', str(video_source)]
        supported = available_encoders()
        if encoder == 'cpu':
            encoder = 'libx264'
        if encoder == 'gpu':
            candidates = [e for e in supported if e in ('h264_nvenc', 'h264_amf', 'h264_qsv')]
            if not candidates:
                raise RuntimeError('No hardware H.264 encoder advertised by FFmpeg. Choose CPU.')
            encoder = candidates[0]
        if encoder == 'auto':
            candidates = [e for e in supported if e in ('h264_nvenc', 'h264_amf', 'h264_qsv')]
            candidates += ['libx264']
        else:
            if encoder not in supported:
                raise RuntimeError(f'{encoder} is not available in this FFmpeg installation.')
            candidates = [encoder]
        errors = []
        for chosen in candidates:
            # Retry at lower rates if the container is larger than the 10 MB limit.
            # This is essential for hardware VBR encoders which can overshoot.
            for factor in (1.0, .82, .65, .48):
                partial.unlink(missing_ok=True)
                try:
                    _run_encode(ffmpeg, video_input, audio_source, audio_start, duration,
                                int(video_bps*factor), audio_bps, chosen, partial,
                                passlog, on_progress, blur_faces)
                    if partial.is_file() and partial.stat().st_size < 10_000_000:
                        break
                    errors.append(f'{chosen} at {factor:.0%}: exceeded 10 MB')
                except RuntimeError as exc:
                    errors.append(str(exc))
                    break  # An encoder error is unlikely to improve with a lower bitrate.
            if partial.is_file() and partial.stat().st_size < 10_000_000:
                break
        else:
            raise RuntimeError('Could not produce an MP4 below 10 MB. ' + ' | '.join(errors)[-1600:])
        if not partial.exists():
            raise RuntimeError('FFmpeg did not create an output file.')
        if partial.stat().st_size >= 10_000_000:
            raise RuntimeError('Export exceeded 10 MB; reduce clip length and try again.')
        # Move only after validating; do not replace an existing file.
        if destination.exists():
            raise FileExistsError(f'Output already exists: {destination}')
        shutil.move(str(partial), str(destination))
    if on_progress:
        on_progress(100)
    return destination
