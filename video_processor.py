"""
video_processor.py - Post-process recorded videos.
Handles: compression, caption overlay, FPS reduction, audio merge.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

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


def normalize_caption_text(text: str) -> str:
    """Collapse subtitle whitespace before chunking it for display."""
    return re.sub(r"\s+", " ", text or "").strip()


def wrap_caption_chunk(text: str) -> str:
    """Insert one balanced line break when a caption chunk gets visually wide."""
    words = text.split()
    if len(words) < 7:
        return text

    best_split = None
    best_score = None
    for index in range(2, len(words) - 1):
        left = " ".join(words[:index])
        right = " ".join(words[index:])
        score = (max(len(left), len(right)), abs(len(left) - len(right)))
        if best_score is None or score < best_score:
            best_score = score
            best_split = (left, right)

    if not best_split:
        return text
    return f"{best_split[0]}\n{best_split[1]}"


def split_timeline_caption_text(text: str, max_words: int = 7) -> list[str]:
    """Break long narration lines into shorter subtitle beats."""
    normalized = normalize_caption_text(text)
    if not normalized:
        return []

    chunks = []
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    for sentence in sentences:
        line = sentence.strip()
        if not line:
            continue

        words = line.split()
        while len(words) > max_words:
            chunk_words = words[:max_words]
            chunks.append(wrap_caption_chunk(" ".join(chunk_words)))
            words = words[max_words:]

        if words:
            chunks.append(wrap_caption_chunk(" ".join(words)))

    return chunks or [wrap_caption_chunk(normalized)]


def caption_chunk_windows(start_sec: float, end_sec: float, chunks: list[str]) -> list[tuple[float, float, str]]:
    """Distribute subtitle chunks across the spoken segment by word weight."""
    if not chunks:
        return []

    if len(chunks) == 1:
        return [(start_sec, end_sec, chunks[0])]

    duration_sec = max(end_sec - start_sec, 0.2)
    chunk_weights = [max(len(chunk.replace("\n", " ").split()), 1) for chunk in chunks]
    total_weight = sum(chunk_weights)
    minimum_chunk_sec = 0.55
    windows = []
    cursor = start_sec

    for index, chunk in enumerate(chunks):
        if index == len(chunks) - 1:
            chunk_end = end_sec
        else:
            proportional_sec = duration_sec * (chunk_weights[index] / total_weight)
            remaining_min_sec = minimum_chunk_sec * (len(chunks) - index - 1)
            chunk_end = min(cursor + max(proportional_sec, minimum_chunk_sec), end_sec - remaining_min_sec)

        windows.append((cursor, chunk_end, chunk))
        cursor = chunk_end

    return windows


def retime_video_to_timeline(
    input_path: str,
    narration_timeline_path: str | None,
    output_path: str,
) -> bool:
    """Speed-match grouped source windows to explicit narration timing targets."""
    segments = load_narration_segments(narration_timeline_path)
    if not segments:
        return False

    required_fields = {"source_start_sec", "source_end_sec", "offset_sec", "target_window_end_sec"}
    if any(not required_fields.issubset(segment.keys()) for segment in segments):
        return False

    with tempfile.TemporaryDirectory(prefix="video_retime_", dir=OUTPUT_DIR) as temp_dir:
        segment_paths = []

        for index, segment in enumerate(segments, start=1):
            source_start = float(segment.get("source_start_sec", 0.0) or 0.0)
            source_end = float(segment.get("source_end_sec", source_start) or source_start)
            target_start = float(segment.get("offset_sec", 0.0) or 0.0)
            target_end = float(segment.get("target_window_end_sec", target_start) or target_start)
            source_duration = max(source_end - source_start, 0.05)
            target_duration = max(target_end - target_start, 0.05)
            setpts_factor = target_duration / source_duration

            segment_path = os.path.join(temp_dir, f"segment_{index:02d}.webm")
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{source_start:.3f}",
                "-to",
                f"{source_end:.3f}",
                "-i",
                input_path,
                "-vf",
                f"setpts={setpts_factor:.6f}*PTS",
                "-an",
                "-c:v",
                "libvpx-vp9",
                "-crf",
                "45",
                "-b:v",
                "0",
                segment_path,
            ]
            if not run_media_command(cmd, f"Retiming segment {index} for {os.path.basename(input_path)}"):
                return False
            segment_paths.append(segment_path)

        if not segment_paths:
            return False

        concat_path = os.path.join(temp_dir, "segments.txt")
        with open(concat_path, "w", encoding="utf-8") as concat_file:
            for path in segment_paths:
                normalized_path = path.replace("\\", "/")
                concat_file.write(f"file '{normalized_path}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_path,
            "-an",
            "-c:v",
            "libvpx-vp9",
            "-crf",
            "45",
            "-b:v",
            "0",
            output_path,
        ]
        if not run_media_command(cmd, f"Timeline retime concat for {os.path.basename(input_path)}"):
            return False

    if not os.path.exists(output_path):
        print(f"  ERROR: Retimed video missing: {output_path}")
        return False

    print(f"  Retimed video to narration timeline: {output_path}")
    return True


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
            caption_index = 1
            for segment in narration_segments:
                start_sec = max(0.0, float(segment.get("start_sec", segment.get("offset_sec", 0.0)) or 0.0))
                fallback_duration = max(float(segment.get("clip_duration_sec", 0.0) or 0.0), 1.1)
                end_sec = float(segment.get("end_sec", start_sec + fallback_duration) or (start_sec + fallback_duration))
                start_sec = min(start_sec, video_duration)
                end_sec = min(max(end_sec, start_sec + 0.2), video_duration)
                subtitle = (
                    segment.get("spoken_text")
                    or segment.get("subtitle")
                    or segment.get("text")
                    or ""
                ).strip()
                if not subtitle:
                    continue

                caption_chunks = split_timeline_caption_text(subtitle)
                for chunk_start, chunk_end, chunk_text in caption_chunk_windows(start_sec, end_sec, caption_chunks):
                    f.write(f"{caption_index}\n")
                    f.write(f"{format_srt_time(chunk_start)} --> {format_srt_time(chunk_end)}\n")
                    f.write(f"{chunk_text}\n\n")
                    caption_index += 1

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
            "force_style='FontSize=14,FontName=Trebuchet MS,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H46000000,"
            "BackColour=&H00000000,BorderStyle=1,Outline=1,Shadow=0,"
            "MarginV=18,MarginL=34,MarginR=34,Alignment=2,Spacing=0.1'"
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


def trim_video_to_duration(input_path: str, output_path: str, target_duration: float):
    """Trim a video down to the narration length when retiming drifts slightly long."""
    current_duration = get_media_duration(input_path)
    if current_duration <= target_duration + 0.05:
        shutil.copyfile(input_path, output_path)
        return True

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-t",
        f"{target_duration:.3f}",
        "-c:v",
        "libvpx-vp9",
        "-crf",
        "45",
        "-b:v",
        "0",
        "-an",
        output_path,
    ]

    print(f"  Trimming video to narration length...")
    if not run_media_command(cmd, f"Video trim for {os.path.basename(input_path)}"):
        return False

    if not os.path.exists(output_path):
        print(f"  ERROR: Trimmed video missing: {output_path}")
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

    # Step 2: Optionally retime video to an explicit narration timeline
    narration_timeline_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_timeline.json")
    caption_source_path = compressed_path
    target_duration = get_media_duration(compressed_path)

    retimed_video_path = os.path.join(OUTPUT_DIR, f"{demo_name}_retimed.webm")
    if retime_video_to_timeline(compressed_path, narration_timeline_path, retimed_video_path):
        caption_source_path = retimed_video_path
        target_duration = get_media_duration(caption_source_path)

    # Step 3: Align base video duration with narration if audio still runs longer
    audio_path = find_narration_audio(demo_name)

    if audio_path:
        audio_duration = get_media_duration(audio_path)
        if audio_duration > target_duration + 0.05:
            timed_video_path = os.path.join(OUTPUT_DIR, f"{demo_name}_timed.webm")
            if extend_video_to_duration(caption_source_path, timed_video_path, audio_duration):
                caption_source_path = timed_video_path
                target_duration = get_media_duration(caption_source_path)
        elif audio_duration < target_duration - 0.05:
            timed_video_path = os.path.join(OUTPUT_DIR, f"{demo_name}_timed.webm")
            if trim_video_to_duration(caption_source_path, timed_video_path, audio_duration):
                caption_source_path = timed_video_path
                target_duration = get_media_duration(caption_source_path)

    # Step 4: Generate captions from steps JSON
    steps_path = os.path.join(SCREENSHOT_DIR, f"{demo_name}_steps.json")
    srt_path = os.path.join(OUTPUT_DIR, f"{demo_name}_captions.srt")
    captioned_path = caption_source_path

    if os.path.exists(steps_path):
        narration_beats_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_beats.json")
        generate_caption_file(
            steps_path,
            target_duration,
            srt_path,
            narration_beats_path=narration_beats_path,
            narration_timeline_path=narration_timeline_path,
        )

        # Step 5: Burn captions
        candidate_captioned_path = os.path.join(OUTPUT_DIR, f"{demo_name}_captioned.webm")
        if burn_captions(caption_source_path, srt_path, candidate_captioned_path):
            captioned_path = candidate_captioned_path
        else:
            print("  WARNING: Caption burn failed, using compressed video without hard subtitles")
    else:
        print(f"  WARNING: No steps JSON found, skipping captions")

    # Step 6: Merge audio if available
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
