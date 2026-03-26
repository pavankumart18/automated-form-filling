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


def load_narration_segments(narration_timeline_path: str | None) -> list[dict]:
    """Load synthesized narration timeline segments if available."""
    if not narration_timeline_path or not os.path.exists(narration_timeline_path):
        return []

    try:
        with open(narration_timeline_path, encoding="utf-8") as f:
            payload = json.load(f)
        segments = payload.get("segments", [])
        return segments if isinstance(segments, list) else []
    except Exception:
        return []


def generate_caption_file(
    steps_json_path: str,
    video_duration: float,
    output_path: str,
    narration_beats_path: str | None = None,
    narration_timeline_path: str | None = None,
):
    """
    Generate an SRT subtitle file from steps JSON.
    Distributes steps across the duration using relative caption word counts and
    leaves small gaps between captions so the viewer can absorb each action.
    """
    with open(steps_json_path, encoding="utf-8") as f:
        steps = json.load(f)

    num_steps = len(steps)
    if num_steps == 0:
        return

    narration_segments = load_narration_segments(narration_timeline_path)
    if narration_segments:
        with open(output_path, "w", encoding="utf-8") as f:
            for index, segment in enumerate(narration_segments, start=1):
                start_sec = max(0.0, float(segment.get("start_sec", segment.get("offset_sec", 0.0)) or 0.0))
                fallback_duration = max(float(segment.get("clip_duration_sec", 0.0) or 0.0), 1.1)
                end_sec = float(segment.get("end_sec", start_sec + fallback_duration) or (start_sec + fallback_duration))
                start_sec = min(start_sec, video_duration)
                end_sec = min(max(end_sec, start_sec + 0.2), video_duration)
                subtitle = (segment.get("subtitle") or segment.get("text") or "").strip()
                if not subtitle:
                    continue

                f.write(f"{index}\n")
                f.write(f"{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}\n")
                f.write(f"{subtitle}\n\n")

        print(f"  Captions generated from narration timeline: {output_path}")
        return

    narration_beats = None
    if narration_beats_path and os.path.exists(narration_beats_path):
        try:
            with open(narration_beats_path, encoding="utf-8") as f:
                candidate_beats = json.load(f)
            if len(candidate_beats) == num_steps:
                narration_beats = candidate_beats
        except Exception:
            narration_beats = None

    timed_steps_available = all(
        ("start_elapsed_sec" in step or "end_elapsed_sec" in step or "duration_sec" in step)
        for step in steps
    )
    if timed_steps_available:
        total_recorded_duration = 0.0
        actual_ranges = []

        previous_end = 0.0
        for step in steps:
            start_sec = float(step.get("start_elapsed_sec", previous_end) or previous_end)
            end_sec = float(step.get("end_elapsed_sec", start_sec + float(step.get("duration_sec", 0.0) or 0.0)) or start_sec)
            if end_sec <= start_sec:
                end_sec = start_sec + max(float(step.get("duration_sec", 0.0) or 0.0), 0.4)
            actual_ranges.append((start_sec, end_sec))
            previous_end = end_sec
            total_recorded_duration = max(total_recorded_duration, end_sec)

        scale = (video_duration / total_recorded_duration) if total_recorded_duration > 0 else 1.0
        with open(output_path, "w", encoding="utf-8") as f:
            for index, step in enumerate(steps, start=1):
                start_sec, end_sec = actual_ranges[index - 1]
                caption_text = step["description"].strip()
                scaled_start = min(start_sec * scale, video_duration)
                scaled_end = min(max(end_sec * scale, scaled_start + 0.2), video_duration)
                f.write(f"{index}\n")
                f.write(f"{format_srt_time(scaled_start)} --> {format_srt_time(scaled_end)}\n")
                f.write(f"{caption_text}\n\n")

        print(f"  Captions generated from measured step timings: {output_path}")
        return

    weights = []
    caption_texts = []
    desired_gaps = []

    for index, step in enumerate(steps):
        beat = narration_beats[index] if narration_beats else {}
        caption_text = (beat.get("description") or step["description"]).strip()
        caption_texts.append(caption_text)
        weights.append(max(len(caption_text.split()), 1))
        pause_ms = int(beat.get("pause_ms", 420)) if index < num_steps - 1 else 0
        desired_gaps.append(max(pause_ms / 1000.0, 0.0))

    total_weight = sum(weights)
    requested_gap_budget = sum(desired_gaps[:-1])
    max_gap_budget = video_duration * 0.18
    gap_scale = min(1.0, max_gap_budget / requested_gap_budget) if requested_gap_budget else 1.0
    scaled_gaps = [gap * gap_scale for gap in desired_gaps]
    total_gap_budget = sum(scaled_gaps[:-1])
    active_duration = max(video_duration - total_gap_budget, video_duration * 0.72)

    # If we had to reserve too much time for captions, shrink the gaps again.
    if active_duration + total_gap_budget > video_duration and requested_gap_budget:
        revised_gap_budget = max(video_duration * 0.12, video_duration - active_duration)
        gap_scale = revised_gap_budget / requested_gap_budget
        scaled_gaps = [gap * gap_scale for gap in desired_gaps]
        total_gap_budget = sum(scaled_gaps[:-1])
        active_duration = video_duration - total_gap_budget

    current_sec = 0.0

    with open(output_path, "w", encoding="utf-8") as f:
        for i, step in enumerate(steps):
            start_sec = current_sec
            if i == num_steps - 1:
                end_sec = video_duration
            else:
                step_duration = active_duration * (weights[i] / total_weight)
                end_sec = current_sec + step_duration
            current_sec = end_sec + (scaled_gaps[i] if i < num_steps - 1 else 0.0)

            start_time = format_srt_time(start_sec)
            end_time = format_srt_time(end_sec)

            f.write(f"{i + 1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{caption_texts[i]}\n\n")

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
            "force_style='FontSize=18,FontName=Trebuchet MS,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H28000000,"
            "BackColour=&H78000000,BorderStyle=3,Outline=1,Shadow=0,"
            "MarginV=26,Alignment=2,Spacing=0.3'"
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
        narration_beats_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_beats.json")
        narration_timeline_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_timeline.json")
        generate_caption_file(
            steps_path,
            target_duration,
            srt_path,
            narration_beats_path=narration_beats_path,
            narration_timeline_path=narration_timeline_path,
        )

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
