"""
narration_generator.py - Generate audio narration from step transcripts using Gemini.
Uses Google's Gemini API for text-to-speech generation.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import wave

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
SUPPORTED_AUDIO_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a")
OPENING_CUES = [
    "We start at the front door.",
    "Here is the opening move.",
    "First, the stage.",
]
EARLY_TRANSITION_CUES = [
    "Now the target comes into focus.",
    "This is where the useful part starts.",
    "With the setup in place, we can chase the signal.",
]
MID_TRANSITION_CUES = [
    "Now the page has something to say.",
    "This is where the pattern starts to show.",
    "Here the workflow stops posing and starts proving.",
]
LATE_TRANSITION_CUES = [
    "Now the payoff is close enough to see.",
    "This is where the result starts to feel earned.",
    "From here, the workflow turns into something reusable.",
]
SOFT_TRANSITION_CUES = [
    "Next, we keep the flow clear.",
    "Now we move one step further.",
    "On the next screen, the process stays easy to follow.",
    "We continue carefully from here.",
]
FINALE_CUES = [
    "That is the payoff shot.",
    "That closes the loop cleanly.",
    "That lands the result.",
]
WAITING_ASIDES = [
    "Hmm... little pause here. The page is still catching up, so we give it a second.",
    "We will hold for a beat here and let the screen settle before we move on.",
    "Still thinking. No rush, we will wait for the page to finish the move.",
]
WAITING_ASIDES_SAFE = [
    "The page is still working, so we give it a moment and keep the flow steady.",
    "A short pause here while the screen catches up cleanly.",
    "Still loading, so we wait a beat before the next move.",
]
FALLBACK_WAITING_ASIDES = [
    "Give this a second to settle.",
    "We will let the page catch up.",
    "A quick beat while the results arrive.",
]
DEFAULT_TTS_DIRECTION = (
    "Perform this as a warm, human product-demo narrator with light cinematic polish. "
    "Use a measured, conversational pace and make every sentence easy to understand on the first listen. "
    "Leave short, audible pauses between ideas, especially after the first sentence in each beat. "
    "Sound expressive, friendly, and lightly playful, like a great explainer walking beside the viewer. "
    "Keep jokes subtle and charming, never distracting or sarcastic. "
    "Avoid robotic pacing, flat delivery, breathless reads, and rushed speech."
)
MAX_AUDIO_SPEEDUP = 1.4
DEFAULT_AUDIO_PACE = 0.94
GEMINI_QUOTA_EXHAUSTED = False
LONG_STEP_FILLER_THRESHOLD_SEC = 11.5
GERUND_OVERRIDES = {
    "open": "opening",
    "navigate": "navigating",
    "search": "searching",
    "view": "viewing",
    "review": "reviewing",
    "inspect": "inspecting",
    "check": "checking",
    "browse": "browsing",
    "switch": "switching",
    "replace": "swapping in",
    "add": "adding",
    "run": "running",
    "fill": "filling",
    "enter": "entering",
    "set": "setting",
    "choose": "choosing",
    "select": "selecting",
    "move": "moving",
    "go": "going",
    "complete": "completing",
    "use": "using",
    "download": "downloading",
    "export": "exporting",
    "split": "splitting",
    "write": "writing",
    "click": "clicking",
    "stop": "stopping",
}
STEP_COMMENTARY = {
    "open": [
        "Now the workflow has a stage.",
        "This gives the whole demo a place to stand.",
        "From here, every click has context.",
    ],
    "navigate": [
        "We skip the wandering and land on the part that matters.",
        "No side quest, just the useful page.",
        "That puts the real subject right in front of us.",
    ],
    "search": [
        "That cuts straight through the hunting.",
        "The signal shows up faster when the search is this tight.",
        "Now the next move is obvious for a reason.",
    ],
    "view": [
        "This is the first clean read on what matters.",
        "Now the screen stops feeling busy and starts feeling useful.",
        "The headline numbers do the first round of storytelling here.",
    ],
    "review": [
        "This is where the pattern stops hiding.",
        "Now the trend line starts behaving like evidence.",
        "Here the page finally tells us something worth listening to.",
    ],
    "inspect": [
        "The close-up matters because the clues live here.",
        "This is the layer where the small details start carrying weight.",
        "A quick inspection here saves a lot of guessing later.",
    ],
    "check": [
        "A fast check here tells us whether the foundation actually holds.",
        "This is where confidence is either earned or lost.",
        "That keeps the whole run grounded in something real.",
    ],
    "browse": [
        "Now comparison gets lighter and the noise drops out.",
        "This turns a click-fest into something you can actually scan.",
        "More clarity, fewer tiny detours.",
    ],
    "switch": [
        "A different angle tells the story faster here.",
        "The view changes, and suddenly the read gets easier.",
        "Sometimes one switch is all it takes for the page to make sense.",
    ],
    "replace": [
        "Same rhythm, new question, and that is the whole point.",
        "This is where the workflow proves it is reusable.",
        "One small swap and the demo starts feeling like a system.",
    ],
    "add": [
        "One more layer makes the picture richer without making it messy.",
        "This expands the flow without breaking its rhythm.",
        "Now the story has a little more range.",
    ],
    "run": [
        "This is the moment the setup cashes out into something visible.",
        "Now the page gets to do the heavy lifting.",
        "This is where all the quiet setup finally earns applause.",
    ],
    "fill": [
        "This is exactly the repetitive work a person should only explain once.",
        "No one needs a sequel called type the same thing again.",
        "Automation earns trust fastest in moments like this.",
    ],
    "enter": [
        "Every future rerun gets cheaper because of this little moment.",
        "The boring part belongs to automation, not to patience.",
        "This is the sort of repetition the workflow should steal from us.",
    ],
    "set": [
        "That small setting keeps future runs honest.",
        "A precise value here saves a lot of drift later.",
        "This is where consistency gets baked into the flow.",
    ],
    "choose": [
        "Keeping the choice visible is what makes the flow teachable.",
        "Now the decision is explicit, not implied.",
        "This is where reproducibility stops being a promise and becomes a detail.",
    ],
    "select": [
        "A clean selection here keeps the run from improvising.",
        "This is how reruns stay dependable instead of lucky.",
        "The more explicit this beat is, the calmer the whole workflow feels.",
    ],
    "move": [
        "This keeps the eye oriented instead of yanking it around.",
        "The move is simple, but it keeps the rhythm under control.",
        "A deliberate shift here keeps the story readable.",
    ],
    "go": [
        "The flow moves forward without dropping the thread.",
        "That keeps the sequence moving while the context is still warm.",
        "A move like this keeps the scene from getting sticky.",
    ],
    "complete": [
        "Now the finish state is unmistakable.",
        "That is the exact payoff the workflow was building toward.",
        "The end lands cleanly, and that matters more than it sounds.",
    ],
    "use": [
        "This is where the demo stops being decorative and starts being useful.",
        "Now the workflow earns its keep.",
        "A simple action here makes the whole thing feel practical.",
    ],
    "download": [
        "Now the result feels like something you can actually hand off.",
        "This is the handoff shot, not just the end of a demo.",
        "The outcome turns tangible right here.",
    ],
    "export": [
        "This is the handoff from browser moment to reusable artifact.",
        "Now the output can travel beyond the demo.",
        "The browser does its part, and the result is ready for the next tool.",
    ],
    "split": [
        "The framing matters because it lets cause and effect sit in one glance.",
        "A split like this does half the storytelling for us.",
        "Now the logic and the result can share the frame.",
    ],
    "write": [
        "Making the logic visible is what turns a demo into a recipe.",
        "Now the workflow feels repeatable instead of magical.",
        "Once the query is on screen, the mystery mostly disappears.",
    ],
    "click": [
        "A clear click like this keeps the eye exactly where it needs to be.",
        "The action lands on target, and the viewer never has to hunt for it.",
        "This is the kind of click that keeps the whole scene readable.",
    ],
    "stop": [
        "This stop is deliberate, not hesitant.",
        "Stopping here keeps the demo safe without making it vague.",
        "The flow remains understandable even because we stop at the right boundary.",
    ],
}
COMPACT_STORY_TAGS = {
    "open": "That gives the workflow a stage.",
    "navigate": "That puts the real subject in front of us.",
    "search": "That gets us to the signal fast.",
    "view": "Now the key read is visible.",
    "review": "Now the pattern has a voice.",
    "inspect": "The clues live in this layer.",
    "check": "That tells us if the foundation holds.",
    "browse": "Now comparison gets easier.",
    "switch": "A better angle changes the read.",
    "replace": "Same flow, different question.",
    "add": "Now the picture gets fuller.",
    "run": "Here the setup turns into results.",
    "fill": "This is where automation saves patience.",
    "enter": "This is where repetition gets retired.",
    "set": "That keeps the run honest.",
    "choose": "The choice stays visible.",
    "select": "That keeps the flow deterministic.",
    "move": "That keeps the eye oriented.",
    "go": "The thread stays intact.",
    "use": "Now the workflow becomes useful.",
    "download": "Now there is something to hand off.",
    "export": "This is the handoff point.",
    "split": "Now both sides of the workflow are visible.",
    "write": "Now the logic has a voice.",
    "click": "The action stays easy to track.",
    "stop": "That keeps the demo safe.",
}

for directory in [OUTPUT_DIR, SCREENSHOT_DIR]:
    os.makedirs(directory, exist_ok=True)


def load_local_env():
    """Load project .env values if python-dotenv is installed."""
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        print("WARNING: .env file found but python-dotenv is not installed.")
        return

    load_dotenv(env_path, override=False)


def remove_existing_audio_outputs(output_prefix: str):
    """Delete older narration audio files so a rerun cannot reuse stale audio."""
    for extension in SUPPORTED_AUDIO_EXTENSIONS:
        audio_path = f"{output_prefix}{extension}"
        if os.path.exists(audio_path):
            os.remove(audio_path)


def find_existing_audio_output(output_prefix: str) -> str | None:
    """Return the first existing audio output for a narration prefix."""
    for extension in SUPPORTED_AUDIO_EXTENSIONS:
        audio_path = f"{output_prefix}{extension}"
        if os.path.exists(audio_path):
            return audio_path
    return None


def extension_for_mime_type(mime_type: str | None) -> str:
    """Map Gemini audio mime types to a file extension."""
    mapping = {
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/ogg": ".ogg",
        "audio/flac": ".flac",
        "audio/aac": ".aac",
        "audio/mp4": ".m4a",
    }
    return mapping.get((mime_type or "").lower(), ".wav")


def parse_mime_parameters(mime_type: str | None) -> tuple[str, dict[str, str]]:
    """Split a mime type into the base type and lower-cased parameters."""
    if not mime_type:
        return "", {}

    parts = [part.strip() for part in mime_type.split(";") if part.strip()]
    base_type = parts[0].lower() if parts else ""
    params: dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            params[key.strip().lower()] = value.strip()
    return base_type, params


def save_audio_payload(audio_bytes: bytes, mime_type: str | None, output_prefix: str) -> str:
    """Persist Gemini audio bytes, wrapping raw PCM into a WAV container when needed."""
    base_type, params = parse_mime_parameters(mime_type)

    if base_type in {"audio/l16", "audio/pcm"}:
        sample_rate = int(params.get("rate", "24000"))
        channels = int(params.get("channels", "1"))
        output_path = f"{output_prefix}.wav"
        with wave.open(output_path, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)
        return output_path

    output_path = f"{output_prefix}{extension_for_mime_type(mime_type)}"
    with open(output_path, "wb") as audio_file:
        audio_file.write(audio_bytes)
    return output_path


def get_retry_delay_seconds(error: Exception) -> float:
    """Best-effort extraction of a retry delay from Gemini error text."""
    error_text = str(error)
    for marker in ("Please retry in ", "retryDelay': '", 'retryDelay": "'):
        if marker not in error_text:
            continue

        tail = error_text.split(marker, 1)[1]
        seconds_text = ""
        for char in tail:
            if char.isdigit() or char == ".":
                seconds_text += char
            else:
                break
        if seconds_text:
            return float(seconds_text)
    return 20.0


def run_media_command(cmd: list[str], label: str) -> bool:
    """Run FFmpeg/FFprobe commands and print the useful tail on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True

    print(f"  WARNING: {label} failed with exit code {result.returncode}.")
    stderr = (result.stderr or "").strip()
    if stderr:
        print("\n".join(stderr.splitlines()[-8:]))
    return False


def get_media_duration(path: str) -> float:
    """Read a media duration in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True,
        text=True,
    )
    return float((result.stdout or "0").strip() or "0")


def normalize_audio_to_wav(input_path: str, output_path: str):
    """Convert any generated clip into one concat-friendly WAV format."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ac",
        "1",
        "-ar",
        "24000",
        "-c:a",
        "pcm_s16le",
        output_path,
    ]
    if not run_media_command(cmd, f"Audio normalization for {os.path.basename(input_path)}"):
        return None
    return output_path


def apply_audio_pace(input_path: str, pace_factor: float, output_path: str):
    """Gently slow a clip down so the narration is easier to follow."""
    if abs(pace_factor - 1.0) <= 0.01:
        return input_path, get_media_duration(input_path)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-filter:a",
        f"atempo={pace_factor:.6f}",
        "-ac",
        "1",
        "-ar",
        "24000",
        "-c:a",
        "pcm_s16le",
        output_path,
    ]
    if not run_media_command(cmd, f"Audio pacing for {os.path.basename(input_path)}"):
        return input_path, get_media_duration(input_path)
    return output_path, get_media_duration(output_path)


def atempo_filter_for_ratio(speed_factor: float) -> str:
    """Build an ffmpeg atempo chain that supports large speed-ups."""
    remaining = max(speed_factor, 1.0)
    factors = []
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    factors.append(remaining)
    return ",".join(f"atempo={factor:.6f}" for factor in factors)


def fit_audio_clip_to_duration(input_path: str, max_duration: float, output_path: str):
    """Speed up an audio clip only a little if it would overflow its timing budget."""
    current_duration = get_media_duration(input_path)
    if max_duration <= 0 or current_duration <= max_duration + 0.06:
        return input_path, current_duration

    speed_factor = current_duration / max_duration
    if speed_factor <= 1.05:
        return input_path, current_duration

    applied_speed = min(speed_factor, MAX_AUDIO_SPEEDUP)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-filter:a",
        atempo_filter_for_ratio(applied_speed),
        "-ac",
        "1",
        "-ar",
        "24000",
        "-c:a",
        "pcm_s16le",
        output_path,
    ]
    if not run_media_command(cmd, f"Audio timing fit for {os.path.basename(input_path)}"):
        return input_path, current_duration
    return output_path, get_media_duration(output_path)


def create_silence_clip(duration_sec: float, output_path: str):
    """Create a silence WAV clip for timeline gaps."""
    safe_duration = max(duration_sec, 0.02)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=24000:cl=mono",
        "-t",
        f"{safe_duration:.3f}",
        "-ac",
        "1",
        "-ar",
        "24000",
        "-c:a",
        "pcm_s16le",
        output_path,
    ]
    if not run_media_command(cmd, f"Silence generation for {os.path.basename(output_path)}"):
        return None
    return output_path


def concat_audio_clips(input_paths: list[str], output_path: str):
    """Concatenate WAV clips into one final narration track."""
    list_path = f"{output_path}.txt"
    with open(list_path, "w", encoding="utf-8") as file:
        for path in input_paths:
            normalized = path.replace("\\", "/").replace("'", "'\\''")
            file.write(f"file '{normalized}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-c",
        "copy",
        output_path,
    ]
    success = run_media_command(cmd, f"Audio concat for {os.path.basename(output_path)}")
    try:
        os.remove(list_path)
    except OSError:
        pass
    return output_path if success else None


load_local_env()


def normalize_text(text: str) -> str:
    """Collapse repeated whitespace and trim trailing punctuation noise."""
    return " ".join((text or "").strip().rstrip(".").split())


def first_word(text: str) -> str:
    """Return the first space-delimited token in lower case."""
    return normalize_text(text).split(" ", 1)[0].lower()


def lower_first_non_acronym(text: str) -> str:
    """Lowercase the first word when it is not a short acronym."""
    text = normalize_text(text)
    if not text:
        return text

    first, _, remainder = text.partition(" ")
    if first.isupper() and len(first) <= 4:
        return text

    lowered = first[:1].lower() + first[1:]
    return f"{lowered} {remainder}".strip()


def to_gerund_clause(text: str) -> str:
    """Turn an imperative description into a more conversational opening clause."""
    text = normalize_text(text)
    if not text:
        return text

    first, _, remainder = text.partition(" ")
    gerund = GERUND_OVERRIDES.get(first.lower())
    if not gerund:
        return lower_first_non_acronym(text)
    return f"{gerund} {remainder}".strip()


def spoken_description(text: str) -> str:
    """Trim detailed labels into a cleaner line for voice narration."""
    cleaned = normalize_text(text)
    if not cleaned:
        return cleaned

    for token in [" - ", ": ", "; "]:
        head, separator, _ = cleaned.partition(token)
        if separator and len(head.split()) >= 2:
            return head.strip()
    return cleaned


def trim_words(text: str, max_words: int) -> str:
    """Limit a line to a manageable spoken length."""
    words = normalize_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",;:-")


def pick_variant(options: list[str], seed: int) -> str:
    """Choose a stable line variant so the narration does not feel repetitive."""
    if not options:
        return ""
    return options[seed % len(options)]


def is_sensitive_step(description: str, url: str = "") -> bool:
    """Avoid jokey tone for sensitive government or identity flows."""
    lowered = f"{normalize_text(description).lower()} {url.lower()}".strip()
    return any(token in lowered for token in ["visa", "passport", "captcha", "nationality", "government"])


def cinematic_cue(step_num: int, total_steps: int, sensitive: bool) -> str:
    """Add a short cinematic expression to keep the delivery lively."""
    if step_num == total_steps:
        return pick_variant(FINALE_CUES, step_num)
    if step_num == 1:
        return pick_variant(OPENING_CUES, step_num)

    if sensitive:
        return pick_variant(SOFT_TRANSITION_CUES, step_num)

    progress = step_num / max(total_steps, 1)
    if progress <= 0.34:
        cues = EARLY_TRANSITION_CUES
    elif progress <= 0.72:
        cues = MID_TRANSITION_CUES
    else:
        cues = LATE_TRANSITION_CUES
    return pick_variant(cues, step_num)


def step_start_sec(step: dict, fallback: float) -> float:
    """Resolve the measured start time for a step."""
    return float(step.get("start_elapsed_sec", fallback) or fallback)


def step_end_sec(step: dict, fallback: float) -> float:
    """Resolve the measured end time for a step."""
    end_value = step.get("end_elapsed_sec")
    if end_value is not None:
        return float(end_value)
    duration = float(step.get("duration_sec", 0.0) or 0.0)
    return fallback + duration


def build_waiting_aside(step: dict, step_num: int) -> str:
    """Generate a short filler line for visibly slow steps."""
    description = step.get("description", "")
    url = step.get("url", "")
    variants = WAITING_ASIDES_SAFE if is_sensitive_step(description, url) else WAITING_ASIDES
    return pick_variant(variants, step_num)


def build_fallback_waiting_aside(step: dict, step_num: int) -> str:
    """Generate a very short filler line for fallback narration."""
    if is_sensitive_step(step.get("description", ""), step.get("url", "")):
        return "We will give the page a second."
    return pick_variant(FALLBACK_WAITING_ASIDES, step_num)


def build_compact_action_line(spoken_action: str, step_num: int, total_steps: int) -> str:
    """Build a short line that reads naturally in the fallback voice."""
    compact_action = trim_words(spoken_action, 11)
    verb = first_word(compact_action)
    if step_num == 1:
        return f"We start by {to_gerund_clause(compact_action)}."
    if step_num == total_steps:
        return "That completes the flow."
    if verb in GERUND_OVERRIDES:
        return f"Next, we {lower_first_non_acronym(compact_action)}."
    return f"{compact_action}."


def compact_story_tail(description: str, url: str = "") -> str:
    """Return a compact why-it-matters line for the fallback voice."""
    lowered = normalize_text(description).lower()
    if "captcha" in lowered:
        return "That keeps the demo safe."
    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "The flow is ready to replay."
    if "rendered; now compare" in lowered:
        return "Now the comparison is easy to read."

    verb = first_word(lowered)
    tail = COMPACT_STORY_TAGS.get(verb, "")
    if is_sensitive_step(description, url) and verb in {"fill", "enter", "stop"}:
        return "The flow stays clear and respectful."
    return tail


def build_fallback_primary_narration(
    description: str,
    spoken_action: str,
    step_num: int,
    total_steps: int,
    duration_sec: float,
    url: str = "",
) -> str:
    """Build a concise but less naive voice line that stays close to the screen action."""
    lowered = description.lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "That completes the flow."
    if "stop at captcha" in lowered or "captcha step" in lowered:
        return "We stop at the captcha step here."
    if "rendered; now compare" in lowered:
        return "Now the new results are on the map for comparison."

    action_line = build_compact_action_line(spoken_action, step_num, total_steps)
    tail = compact_story_tail(description, url)
    if tail and (duration_sec >= 6.0 or len(spoken_action.split()) <= 7):
        return f"{action_line} {tail}".strip()
    return action_line


def narration_commentary(description: str, step_num: int, url: str = "") -> str:
    """Choose a short aside that keeps the script sounding human."""
    lowered = normalize_text(description).lower()
    sensitive = is_sensitive_step(description, url)

    if "captcha" in lowered:
        return "That keeps the demo safe and clear."
    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "The flow is ready to replay."
    if "rendered; now compare" in lowered:
        return "Now the comparison is easy to read."

    verb = first_word(lowered)
    variants = STEP_COMMENTARY.get(verb)
    if variants:
        if sensitive and len(variants) > 1:
            return variants[0]
        return pick_variant(variants, step_num)
    return "It keeps the flow easy to follow without sounding like a checklist."


def narration_pause_ms(description: str, step_num: int, total_steps: int) -> int:
    """Recommend a small pause after a beat so the viewer can absorb the action."""
    lowered = normalize_text(description).lower()

    if step_num == total_steps or "tutorial complete" in lowered or "captcha" in lowered:
        return 1550
    if any(token in lowered for token in ["review", "browse", "inspect", "check", "compare", "view"]):
        return 1200
    if any(token in lowered for token in ["fill", "enter", "set", "add", "write", "select", "choose"]):
        return 1050
    if any(token in lowered for token in ["download", "export", "run"]):
        return 1120
    return 920


def build_story_beat(step: dict, total_steps: int) -> dict:
    """Rewrite a step into a short, more human narration beat."""
    step_num = step["step"]
    description = normalize_text(step["description"])
    spoken_action = spoken_description(description)
    url = step.get("url", "")
    lowered = description.lower()
    sensitive = is_sensitive_step(description, url)
    cue = cinematic_cue(step_num, total_steps, sensitive)
    measured_start_sec = step_start_sec(step, 0.0)
    measured_end_sec = step_end_sec(step, measured_start_sec)
    measured_duration_sec = round(max(measured_end_sec - measured_start_sec, 0.1), 3)
    commentary = narration_commentary(description, step_num, url)
    if len(spoken_action.split()) >= 6 and measured_duration_sec < 7.0:
        commentary = ""

    def join_lines(base: str, tail: str = "") -> str:
        if tail:
            return f"{base} {tail}".strip()
        return base.strip()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        narration = f"{cue} The flow is ready to replay."
    elif "stop at captcha" in lowered or "captcha step" in lowered:
        narration = join_lines(f"{cue} We stop at the captcha step here.", commentary)
    elif "rendered; now compare" in lowered:
        subject, comparison = description.split("rendered; now compare", 1)
        narration = join_lines(
            f"{cue} {subject.strip()} are now on the map. We compare {comparison.strip()}.",
            commentary,
        )
    elif step_num == 1:
        narration = join_lines(
            f"{cue} Let's start by {to_gerund_clause(spoken_action)}.",
            commentary,
        )
    else:
        narration = join_lines(
            f"{cue} We {lower_first_non_acronym(spoken_action)}.",
            commentary,
        )

    return {
        "step": step_num,
        "caption": step.get("caption") or f"Step {step_num}: {description}",
        "description": description,
        "narration": narration.strip(),
        "fallback_narration": build_fallback_primary_narration(
            description,
            spoken_action,
            step_num,
            total_steps,
            measured_duration_sec,
            url,
        ),
        "pause_ms": narration_pause_ms(description, step_num, total_steps),
        "url": url,
        "start_elapsed_sec": round(measured_start_sec, 3),
        "end_elapsed_sec": round(measured_end_sec, 3),
        "duration_sec": measured_duration_sec,
    }


def build_narration_timeline(beats: list[dict]) -> list[dict]:
    """Create timed narration segments from the measured step windows."""
    timeline = []

    for beat in beats:
        step_num = beat["step"]
        start_sec = float(beat.get("start_elapsed_sec", 0.0) or 0.0)
        end_sec = float(beat.get("end_elapsed_sec", start_sec) or start_sec)
        duration_sec = max(float(beat.get("duration_sec", end_sec - start_sec) or 0.0), 0.1)
        offset_sec = round(start_sec + 0.32, 3)
        primary_budget = max(duration_sec * (0.78 if duration_sec >= 7.0 else 0.93), 2.75)
        timeline.append(
            {
                "segment_id": f"step_{step_num:02d}_primary",
                "step": step_num,
                "type": "primary",
                "offset_sec": offset_sec,
                "budget_sec": round(primary_budget, 3),
                "text": beat["narration"],
                "fallback_text": beat.get("fallback_narration") or beat["narration"],
                "subtitle": f"Step {step_num}: {beat['description']}",
                "target_window_end_sec": round(end_sec, 3),
            }
        )

        if duration_sec < LONG_STEP_FILLER_THRESHOLD_SEC or "tutorial complete" in beat["description"].lower():
            continue

        filler_offset = start_sec + max(duration_sec * 0.74, 4.0)
        filler_budget = max(end_sec - filler_offset - 0.45, 1.9)
        if filler_budget < 1.9:
            continue

        filler_text = build_waiting_aside(beat, step_num)
        timeline.append(
            {
                "segment_id": f"step_{step_num:02d}_wait",
                "step": step_num,
                "type": "filler",
                "offset_sec": round(filler_offset, 3),
                "budget_sec": round(filler_budget, 3),
                "text": filler_text,
                "fallback_text": build_fallback_waiting_aside(beat, step_num),
                "subtitle": filler_text,
                "target_window_end_sec": round(end_sec, 3),
            }
        )

    timeline.sort(key=lambda item: (item["offset_sec"], item["segment_id"]))
    return timeline


def generate_narration_package(steps_json_path: str) -> dict:
    """Build structured narration beats plus the final script text."""
    with open(steps_json_path, encoding="utf-8") as file:
        steps = json.load(file)

    total_steps = len(steps)
    beats = [build_story_beat(step, total_steps) for step in steps]
    timeline = build_narration_timeline(beats)
    script = "\n\n".join(segment["text"] for segment in timeline)
    total_duration = max((float(beat.get("end_elapsed_sec", 0.0) or 0.0) for beat in beats), default=0.0)
    return {
        "beats": beats,
        "timeline": timeline,
        "script": script,
        "total_duration_sec": round(total_duration, 3),
    }


def generate_narration_script(steps_json_path: str) -> str:
    """Backward-compatible wrapper used by older callers."""
    return generate_narration_package(steps_json_path)["script"]


def generate_audio_gemini(text: str, output_prefix: str, api_key: str = None):
    """
    Generate audio narration using Google Gemini.

    Setup:
    1. Go to https://aistudio.google.com/
    2. Get an API key
    3. Put it in .env as GEMINI_API_KEY=your_key_here
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("ERROR: google.genai is not installed.")
        print("Run: pip install google-genai --break-system-packages")
        return None

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: No Gemini API key found.")
        print("Set it in the project .env file as GEMINI_API_KEY=your_key_here")
        return None

    global GEMINI_QUOTA_EXHAUSTED
    if GEMINI_QUOTA_EXHAUSTED:
        return None

    model_name = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    voice_name = os.environ.get("GEMINI_VOICE_NAME", "charon")
    client = genai.Client(api_key=api_key)

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["audio"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name
                            )
                        )
                    ),
                ),
            )

            audio_bytes = bytearray()
            mime_type = None
            for part in response.parts or []:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and inline_data.data:
                    audio_bytes.extend(inline_data.data)
                    mime_type = mime_type or inline_data.mime_type

            if not audio_bytes:
                print("  WARNING: Gemini returned no audio payload.")
                return None

            output_path = save_audio_payload(bytes(audio_bytes), mime_type, output_prefix)

            print(f"  Audio narration saved: {output_path}")
            return output_path

        except Exception as e:
            is_retryable = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            is_daily_quota_issue = any(
                token in str(e)
                for token in [
                    "GenerateRequestsPerDayPerProjectPerModel",
                    "generate_requests_per_model_per_day",
                    "per_day",
                ]
            )
            if is_daily_quota_issue:
                GEMINI_QUOTA_EXHAUSTED = True
                print("  WARNING: Gemini daily TTS quota is exhausted, switching remaining segments to fallback audio.")
                return None
            if is_retryable and attempt < 2:
                delay_seconds = get_retry_delay_seconds(e)
                print(f"  WARNING: Gemini rate-limited. Retrying in {delay_seconds:.1f}s...")
                time.sleep(delay_seconds)
                continue

            print(f"  WARNING: Gemini audio generation failed: {e}")
            print("  Falling back to alternate audio generation")
            return None

    return None


def generate_audio_gtts_fallback(text: str, output_prefix: str):
    """
    Fallback: Use gTTS (Google Text-to-Speech) if Gemini is unavailable.
    Free, no API key needed, decent quality.

    Install: pip install gtts --break-system-packages
    """
    try:
        from gtts import gTTS

        output_path = f"{output_prefix}.mp3"
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        print(f"  Audio narration saved (gTTS fallback): {output_path}")
        return output_path
    except ImportError:
        print("  WARNING: gTTS not installed. Run: pip install gtts --break-system-packages")
        return None
    except Exception as e:
        print(f"  WARNING: gTTS failed: {e}")
        return None


def synthesize_segment_audio(segment: dict, temp_dir: str):
    """Generate one narration clip and force it into a concat-friendly WAV shape."""
    base_prefix = os.path.join(temp_dir, segment["segment_id"])
    raw_path = generate_audio_gemini(segment["text"], base_prefix)
    used_fallback = False
    if not raw_path:
        fallback_text = segment.get("fallback_text") or segment["text"]
        raw_path = generate_audio_gtts_fallback(fallback_text, base_prefix)
        used_fallback = raw_path is not None
    if not raw_path:
        return None

    normalized_path = f"{base_prefix}_normalized.wav"
    normalized = normalize_audio_to_wav(raw_path, normalized_path)
    if not normalized:
        return None

    paced_path = f"{base_prefix}_paced.wav"
    pace_factor = 1.0 if used_fallback else DEFAULT_AUDIO_PACE
    paced, _ = apply_audio_pace(normalized, pace_factor, paced_path)

    fitted_path = f"{base_prefix}_fitted.wav"
    fitted, fitted_duration = fit_audio_clip_to_duration(
        paced,
        float(segment.get("budget_sec", 0.0) or 0.0),
        fitted_path,
    )
    segment["clip_duration_sec"] = round(fitted_duration, 3)
    segment["clip_path"] = fitted
    return fitted


def build_timed_audio_track(timeline: list[dict], total_duration_sec: float, output_path: str):
    """Create one final narration track by placing segment clips on the measured timeline."""
    if not timeline:
        return None

    with tempfile.TemporaryDirectory(prefix="narration_timeline_", dir=OUTPUT_DIR) as temp_dir:
        clip_sequence = []
        current_cursor_sec = 0.0

        for index, segment in enumerate(timeline, start=1):
            clip_path = synthesize_segment_audio(segment, temp_dir)
            if not clip_path:
                print(f"  WARNING: Skipping failed narration segment {segment['segment_id']}")
                continue

            offset_sec = float(segment.get("offset_sec", current_cursor_sec) or current_cursor_sec)
            placed_start_sec = max(offset_sec, current_cursor_sec)
            if placed_start_sec > current_cursor_sec + 0.02:
                silence_path = create_silence_clip(
                    placed_start_sec - current_cursor_sec,
                    os.path.join(temp_dir, f"silence_{index:02d}.wav"),
                )
                if silence_path:
                    clip_sequence.append(silence_path)
                current_cursor_sec = placed_start_sec

            clip_sequence.append(clip_path)
            clip_duration = float(segment.get("clip_duration_sec", get_media_duration(clip_path)) or 0.0)
            segment["start_sec"] = round(placed_start_sec, 3)
            segment["end_sec"] = round(placed_start_sec + clip_duration, 3)
            current_cursor_sec = placed_start_sec + clip_duration

        if total_duration_sec > current_cursor_sec + 0.02:
            tail_silence = create_silence_clip(
                total_duration_sec - current_cursor_sec,
                os.path.join(temp_dir, "silence_tail.wav"),
            )
            if tail_silence:
                clip_sequence.append(tail_silence)

        if not clip_sequence:
            return None

        return concat_audio_clips(clip_sequence, output_path)


def generate_narration(demo_name: str):
    """
    Full narration pipeline:
    1. Read steps JSON
    2. Generate narration script
    3. Try Gemini audio, fall back to gTTS
    """
    steps_path = os.path.join(SCREENSHOT_DIR, f"{demo_name}_steps.json")
    if not os.path.exists(steps_path):
        print(f"  ERROR: No steps file found: {steps_path}")
        return None

    # Generate script
    package = generate_narration_package(steps_path)
    script = package["script"]
    beats = package["beats"]
    timeline = package["timeline"]
    total_duration_sec = float(package.get("total_duration_sec", 0.0) or 0.0)
    print(f"\n  Narration script ({len(script)} chars):")
    print(f"  {script[:200]}...")

    # Save script as text
    script_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    beats_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_beats.json")
    with open(beats_path, "w", encoding="utf-8") as f:
        json.dump(beats, f, indent=2)

    timeline_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_timeline.json")
    with open(timeline_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "demo_name": demo_name,
                "total_duration_sec": total_duration_sec,
                "segments": timeline,
            },
            f,
            indent=2,
        )

    # Generate audio
    audio_prefix = os.path.join(OUTPUT_DIR, f"{demo_name}_narration")
    existing_audio_path = find_existing_audio_output(audio_prefix)
    remove_existing_audio_outputs(audio_prefix)

    final_audio_path = f"{audio_prefix}.wav"
    temp_audio_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_tmp.wav")
    remove_existing_audio_outputs(os.path.join(OUTPUT_DIR, f"{demo_name}_narration_tmp"))
    audio_path = build_timed_audio_track(timeline, total_duration_sec, temp_audio_path)

    if audio_path:
        remove_existing_audio_outputs(audio_prefix)
        if os.path.abspath(audio_path) != os.path.abspath(final_audio_path):
            os.replace(audio_path, final_audio_path)
        audio_path = final_audio_path
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "demo_name": demo_name,
                    "total_duration_sec": round(
                        max(total_duration_sec, get_media_duration(audio_path)),
                        3,
                    ),
                    "segments": timeline,
                },
                f,
                indent=2,
            )
        return audio_path
    else:
        remove_existing_audio_outputs(os.path.join(OUTPUT_DIR, f"{demo_name}_narration_tmp"))
        if existing_audio_path:
            print(f"  NOTE: Keeping previous narration audio: {existing_audio_path}")
            return existing_audio_path
        print("  NOTE: No audio generated. Video will be silent with captions only.")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        demo = sys.argv[1]
        generate_narration(demo)
    else:
        print("Usage: python narration_generator.py <demo_name>")
