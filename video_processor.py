"""
video_processor.py - Post-process recorded videos.
Handles: compression, caption overlay, FPS reduction, audio merge.
"""

import json
import os
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
SUPPORTED_AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a")

for directory in [VIDEO_DIR, OUTPUT_DIR, SCREENSHOT_DIR]:
    os.makedirs(directory, exist_ok=True)


def run_media_command(cmd: list[str], label: str) -> bool:
    """Run an FFmpeg/FFprobe command and surface useful errors."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True

    print(f"  ERROR: {label} failed with exit code {result.returncode}.")
    stderr = (result.stderr or "").strip()
    if stderr:
        print("\n".join(stderr.splitlines()[-8:]))
    return False


def get_media_duration(video_path: str) -> float:
    """Get media duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def generate_caption_file(steps_json_path: str, video_duration: float, output_path: str):
    """
    Generate an SRT subtitle file from steps JSON.
    Distributes steps across the duration using relative caption word counts.
    """
    with open(steps_json_path) as f:
        steps = json.load(f)

    num_steps = len(steps)
    if num_steps == 0:
        return

    weights = []
    for step in steps:
        caption_text = f"Step {step['step']}: {step['description']}"
        weights.append(max(len(caption_text.split()), 1))

    total_weight = sum(weights)
    current_sec = 0.0

    with open(output_path, "w") as f:
        for i, step in enumerate(steps):
            start_sec = current_sec
            if i == num_steps - 1:
                end_sec = video_duration
            else:
                end_sec = current_sec + (video_duration * (weights[i] / total_weight))
            current_sec = end_sec

            start_time = format_srt_time(start_sec)
            end_time = format_srt_time(end_sec)

            f.write(f"{i + 1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"Step {step['step']}: {step['description']}\n\n")

    print(f"  Captions generated: {output_path}")


def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def compress_video(input_path: str, output_path: str, fps: int = 5, crf: int = 55):
    """
    Compress video per Pavan's specs:
    - Low FPS (3-5)
    - High CRF (55+)
    - WebM format
    - Max 30 seconds
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"fps={fps},scale=1280:720",
        "-c:v", "libvpx-vp9",
        "-crf", str(crf),
        "-b:v", "0",
        "-t", "120",  # Max 2 minutes
        "-an",  # Remove audio (will add narration later)
        output_path
    ]

    print(f"  Compressing: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    if not run_media_command(cmd, f"Compression for {os.path.basename(input_path)}"):
        return False

    if not os.path.exists(output_path):
        print(f"  ERROR: Compression output missing: {output_path}")
        return False

    print(f"  Done. Output: {output_path}")
    return True


def burn_captions(input_path: str, srt_path: str, output_path: str):
    """Burn SRT captions into the video as hard subtitles."""
    # Escape special characters in path for FFmpeg filter
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", (
            f"subtitles='{escaped_srt}':"
            "force_style='FontSize=14,FontName=Arial,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "Outline=2,Shadow=1,MarginV=30'"
        ),
        "-c:v", "libvpx-vp9",
        "-crf", "45",
        "-b:v", "0",
        output_path
    ]

    print(f"  Burning captions into video...")
    if not run_media_command(cmd, f"Caption burn for {os.path.basename(input_path)}"):
        return False

    if not os.path.exists(output_path):
        print(f"  ERROR: Captioned video missing: {output_path}")
        return False

    print(f"  Done: {output_path}")
    return True


def extend_video_to_duration(input_path: str, output_path: str, target_duration: float):
    """Freeze the final frame so video duration can match narration length."""
    current_duration = get_media_duration(input_path)
    extra_duration = max(0.0, target_duration - current_duration)

    if extra_duration <= 0.05:
        shutil.copyfile(input_path, output_path)
        return True

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"tpad=stop_mode=clone:stop_duration={extra_duration:.3f}",
        "-c:v", "libvpx-vp9",
        "-crf", "45",
        "-b:v", "0",
        "-an",
        output_path,
    ]

    print(f"  Extending video to match narration length...")
    if not run_media_command(cmd, f"Video extension for {os.path.basename(input_path)}"):
        return False

    if not os.path.exists(output_path):
        print(f"  ERROR: Extended video missing: {output_path}")
        return False

    print(f"  Done: {output_path}")
    return True


def merge_audio(video_path: str, audio_path: str, output_path: str):
    """Merge narration audio with video."""
    target_duration = get_media_duration(video_path)
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-filter:a", "apad",
        "-c:v", "libvpx-vp9",
        "-crf", "45",
        "-b:v", "0",
        "-c:a", "libopus",
        "-t", f"{target_duration:.3f}",
        output_path
    ]

    print(f"  Merging audio...")
    if not run_media_command(cmd, f"Audio merge for {os.path.basename(video_path)}"):
        return False

    if not os.path.exists(output_path):
        print(f"  ERROR: Narrated video missing: {output_path}")
        return False

    print(f"  Done: {output_path}")
    return True


def find_narration_audio(demo_name: str) -> str | None:
    """Return the first existing narration audio path for a demo."""
    audio_prefix = os.path.join(OUTPUT_DIR, f"{demo_name}_narration")
    for extension in SUPPORTED_AUDIO_EXTENSIONS:
        candidate = f"{audio_prefix}{extension}"
        if os.path.exists(candidate):
            return candidate
    return None


def process_demo(demo_name: str, fps: int = 5, crf: int = 55):
    """
    Full processing pipeline for a single demo:
    1. Find raw video
    2. Compress it
    3. Generate captions
    4. Burn captions into video
    5. (Optional) Merge audio if narration exists
    """
    print(f"\n{'='*50}")
    print(f"Processing: {demo_name}")
    print(f"{'='*50}")

    # Find raw video
    raw_dir = os.path.join(VIDEO_DIR, demo_name)
    if not os.path.exists(raw_dir):
        print(f"  ERROR: No video directory found for {demo_name}")
        return None

    canonical_raw_path = os.path.join(raw_dir, f"{demo_name}.webm")
    if os.path.exists(canonical_raw_path):
        raw_path = canonical_raw_path
    else:
        raw_videos = [f for f in os.listdir(raw_dir) if f.endswith(".webm")]
        if not raw_videos:
            print(f"  ERROR: No raw video found in {raw_dir}")
            return None

        raw_path = max(
            (os.path.join(raw_dir, name) for name in raw_videos),
            key=lambda path: (os.path.getsize(path), os.path.getmtime(path)),
        )

    # Step 1: Compress
    compressed_path = os.path.join(OUTPUT_DIR, f"{demo_name}_compressed.webm")
    if not compress_video(raw_path, compressed_path, fps=fps, crf=crf):
        return None

    # Step 2: Align base video duration with narration if available
    audio_path = find_narration_audio(demo_name)
    caption_source_path = compressed_path
    target_duration = get_media_duration(compressed_path)

    if audio_path:
        audio_duration = get_media_duration(audio_path)
        if audio_duration > target_duration + 0.05:
            timed_video_path = os.path.join(OUTPUT_DIR, f"{demo_name}_timed.webm")
            if extend_video_to_duration(compressed_path, timed_video_path, audio_duration):
                caption_source_path = timed_video_path
                target_duration = get_media_duration(caption_source_path)

    # Step 3: Generate captions from steps JSON
    steps_path = os.path.join(SCREENSHOT_DIR, f"{demo_name}_steps.json")
    srt_path = os.path.join(OUTPUT_DIR, f"{demo_name}_captions.srt")
    captioned_path = caption_source_path

    if os.path.exists(steps_path):
        generate_caption_file(steps_path, target_duration, srt_path)

        # Step 4: Burn captions
        candidate_captioned_path = os.path.join(OUTPUT_DIR, f"{demo_name}_captioned.webm")
        if burn_captions(caption_source_path, srt_path, candidate_captioned_path):
            captioned_path = candidate_captioned_path
        else:
            print("  WARNING: Caption burn failed, using compressed video without hard subtitles")
    else:
        print(f"  WARNING: No steps JSON found, skipping captions")

    # Step 5: Merge audio if available
    final_output = os.path.join(OUTPUT_DIR, f"{demo_name}_final.webm")

    if audio_path:
        if merge_audio(captioned_path, audio_path, final_output):
            final_path = final_output
        else:
            print("  WARNING: Audio merge failed, keeping video without narration")
            final_path = captioned_path
    else:
        final_path = captioned_path
        print(f"  NOTE: No narration audio found, using video without audio")

    # Copy as final
    if final_path != final_output:
        shutil.copyfile(final_path, final_output)

    print(f"\n  FINAL VIDEO: {final_output}")
    return final_output


if __name__ == "__main__":
    if len(sys.argv) > 1:
        demo = sys.argv[1]
        process_demo(demo)
    else:
        print("Usage: python video_processor.py <demo_name>")
        print("Example: python video_processor.py screener")
