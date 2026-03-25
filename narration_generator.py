"""
narration_generator.py - Generate audio narration from step transcripts using Gemini.
Uses Google's Gemini API for text-to-speech generation.
"""

import json
import os
import sys
import time
import wave

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
SUPPORTED_AUDIO_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a")
OPENING_CUES = [
    "Lights up.",
    "And... action.",
    "Opening shot.",
]
TRANSITION_CUES = [
    "Quick scene change.",
    "Cue the montage.",
    "Now the camera swings to the next beat.",
    "Here comes the payoff shot.",
]
SOFT_TRANSITION_CUES = [
    "Next beat.",
    "From here, we keep moving.",
    "On the next screen.",
    "Now we continue.",
]
FINALE_CUES = [
    "Roll credits.",
    "That is the hero shot.",
    "And that is our closing scene.",
]
DEFAULT_TTS_DIRECTION = (
    "Perform this as a warm, cinematic product-demo narrator. "
    "Sound natural, expressive, and confident, with clean pauses between paragraphs. "
    "Let the voice feel human, lightly playful, and polished, like a smart movie trailer narrator "
    "guiding a slick tutorial. Keep jokes subtle and charming, never distracting or sarcastic. "
    "Avoid robotic pacing, flat delivery, and rushed speech."
)
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
        "This gets the right screen on stage before the real automation choreography begins.",
        "Every good walkthrough needs an establishing shot, and this is ours.",
        "Now the viewer knows exactly where the story starts.",
    ],
    "navigate": [
        "That skips the wandering and gets the important screen in front of us fast.",
        "Straight to the useful page, no side quest required.",
        "A clean jump like this keeps the momentum intact.",
    ],
    "search": [
        "This is usually where people lose time, so automation earns its keep immediately.",
        "And just like that, the scavenger hunt is over.",
        "A precise search here makes the rest of the flow feel inevitable.",
    ],
    "view": [
        "It gives us the quick snapshot before we go deeper.",
        "Here comes the close-up that frames the next few moves.",
        "This wide shot makes the rest of the details easier to read.",
    ],
    "review": [
        "This is where the screen starts telling a story instead of just showing raw numbers.",
        "Now the plot thickens, in the best spreadsheet kind of way.",
        "This is the moment where trends stop hiding and start speaking clearly.",
    ],
    "inspect": [
        "A close look here makes the important signal easier to spot.",
        "Time for the close-up, because the good clues live in the details.",
        "This is where the small details quietly become the whole story.",
    ],
    "check": [
        "One quick check here tells us whether things look solid or stretched.",
        "A fast balance check like this keeps surprises out of the sequel.",
        "This is the kind of sanity check that makes the whole workflow feel trustworthy.",
    ],
    "browse": [
        "This keeps comparison easy without opening every result by hand.",
        "It turns the click-fest into something much lighter.",
        "Now the viewer can scan instead of slog, which is always a nice plot twist.",
    ],
    "switch": [
        "The change in view helps the viewer understand the comparison at a glance.",
        "A quick angle change here makes the story easier to follow.",
        "Sometimes the smartest move is just a better camera angle, and this is one of those moments.",
    ],
    "replace": [
        "A small swap here shows how reusable the flow really is.",
        "Same workflow, new question, very satisfying.",
        "This is where the system stops being a demo and starts looking reusable.",
    ],
    "add": [
        "It is a nice reminder that the workflow can grow without turning brittle.",
        "One more layer, and the story gets richer without getting messier.",
        "This extra beat gives the demo a little more range without breaking its rhythm.",
    ],
    "run": [
        "Once we run it, the page does the heavy lifting for us.",
        "Cue the detective soundtrack; now the data gets to make its entrance.",
        "This is the button where all the setup finally pays off.",
    ],
    "fill": [
        "This is exactly the repetitive work automation should steal from us.",
        "Because nobody asked for a sequel called type the same form twice.",
        "A little typing here saves a lot of future boredom.",
    ],
    "enter": [
        "A little data entry here saves the same keystrokes on every future run.",
        "Nobody wins an award for manual retyping, so the automation can have this one.",
        "This is the boring part, which makes it perfect for automation.",
    ],
    "set": [
        "Being explicit here keeps reruns consistent.",
        "A precise setting now saves a lot of guesswork later.",
        "Locking this down keeps the workflow sharp on every replay.",
    ],
    "choose": [
        "Making the choice visible keeps the demo reproducible.",
        "A visible choice here turns guesswork into a repeatable scene.",
        "This keeps the viewer aligned with exactly what the automation is deciding.",
    ],
    "select": [
        "This keeps the flow deterministic instead of relying on page defaults.",
        "A clean selection like this keeps the workflow from improvising.",
        "Explicit beats like this are what make reruns feel dependable.",
    ],
    "move": [
        "It keeps the viewer oriented instead of jumping around too abruptly.",
        "A smooth move here makes the whole sequence easier on the eyes.",
        "This keeps the pacing deliberate instead of twitchy.",
    ],
    "go": [
        "That keeps the sequence moving while the context still feels fresh.",
        "We keep the momentum without losing the thread.",
        "A move like this keeps the scene flowing naturally.",
    ],
    "complete": [
        "Now the end state is easy to verify.",
        "That is the exact payoff shot we wanted.",
        "The finish state lands cleanly here, and that matters.",
    ],
    "use": [
        "This is the moment where the walkthrough turns into something practical.",
        "A simple action here makes the whole demo feel useful, not decorative.",
        "This is where the workflow earns its applause.",
    ],
    "download": [
        "That makes the outcome feel like a real deliverable, not just a demo.",
        "Boom, that is the handoff shot.",
        "This is the part where the viewer gets something tangible at the end.",
    ],
    "export": [
        "This is the handoff point from browser workflow to reusable output.",
        "And there is the clean exit into the next tool in the chain.",
        "This is where the browser scene hands the story over to the rest of the stack.",
    ],
    "split": [
        "The layout matters here because it makes cause and effect easy to follow.",
        "This framing does half the storytelling work for us.",
        "A split view like this is basically free cinematography for a tutorial.",
    ],
    "write": [
        "Making the query visible is what turns the demo into a repeatable system.",
        "This is the script inside the script, and that is where the magic lives.",
        "Once the logic is visible, the whole workflow feels much less mysterious.",
    ],
    "click": [
        "A visible click here helps the viewer track the action instantly.",
        "That click lands like a cue mark, exactly where the eye needs it.",
        "A crisp click here keeps the viewer from playing hide and seek with the cursor.",
    ],
    "stop": [
        "This is a deliberate stop, not a failure, and that distinction matters.",
        "No stunt work beyond this point, and honestly that is the smart choice.",
        "Stopping here keeps the demo safe while still making the flow fully understandable.",
    ],
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
    cues = SOFT_TRANSITION_CUES if sensitive else TRANSITION_CUES
    return pick_variant(cues, step_num)


def narration_commentary(description: str, step_num: int, url: str = "") -> str:
    """Choose a short aside that keeps the script sounding human."""
    lowered = normalize_text(description).lower()
    sensitive = is_sensitive_step(description, url)

    if "captcha" in lowered:
        return "That way the walkthrough stays safe while still showing the exact handoff point."
    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "The flow is now captured end to end and ready to replay or adapt."
    if "rendered; now compare" in lowered:
        return "Seeing both patterns on screen is what makes the comparison click."

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
        return 900
    if any(token in lowered for token in ["review", "browse", "inspect", "check", "compare", "view"]):
        return 700
    if any(token in lowered for token in ["fill", "enter", "set", "add", "write", "select", "choose"]):
        return 550
    if any(token in lowered for token in ["download", "export", "run"]):
        return 650
    return 450


def build_story_beat(step: dict, total_steps: int) -> dict:
    """Rewrite a step into a short, more human narration beat."""
    step_num = step["step"]
    description = normalize_text(step["description"])
    url = step.get("url", "")
    lowered = description.lower()
    sensitive = is_sensitive_step(description, url)
    cue = cinematic_cue(step_num, total_steps, sensitive)

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        narration = (
            f"{cue} The flow is captured end to end and ready for a replay. "
            f"{narration_commentary(description, step_num, url)}"
        )
    elif "stop at captcha" in lowered or "captcha step" in lowered:
        narration = (
            f"{cue} We intentionally stop at the captcha step here. "
            f"{narration_commentary(description, step_num, url)}"
        )
    elif "rendered; now compare" in lowered:
        subject, comparison = description.split("rendered; now compare", 1)
        narration = (
            f"{cue} {subject.strip()} are now on the map, so we can compare {comparison.strip()}. "
            f"{narration_commentary(description, step_num, url)}"
        )
    elif step_num == 1:
        narration = (
            f"{cue} Let's start by {to_gerund_clause(description)}. "
            f"{narration_commentary(description, step_num, url)}"
        )
    else:
        narration = (
            f"{cue} We {lower_first_non_acronym(description)}. "
            f"{narration_commentary(description, step_num, url)}"
        )

    return {
        "step": step_num,
        "caption": step.get("caption") or f"Step {step_num}: {description}",
        "description": description,
        "narration": narration.strip(),
        "pause_ms": narration_pause_ms(description, step_num, total_steps),
        "url": url,
    }


def generate_narration_package(steps_json_path: str) -> dict:
    """Build structured narration beats plus the final script text."""
    with open(steps_json_path, encoding="utf-8") as file:
        steps = json.load(file)

    total_steps = len(steps)
    beats = [build_story_beat(step, total_steps) for step in steps]
    script = "\n\n".join(beat["narration"] for beat in beats)
    return {"beats": beats, "script": script}


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
            if is_retryable and attempt < 2:
                delay_seconds = get_retry_delay_seconds(e)
                print(f"  WARNING: Gemini rate-limited. Retrying in {delay_seconds:.1f}s...")
                time.sleep(delay_seconds)
                continue

            print(f"  WARNING: Gemini audio generation failed: {e}")
            print("  Falling back to script-only mode (no audio)")
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
    print(f"\n  Narration script ({len(script)} chars):")
    print(f"  {script[:200]}...")

    # Save script as text
    script_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    beats_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_beats.json")
    with open(beats_path, "w", encoding="utf-8") as f:
        json.dump(beats, f, indent=2)

    # Generate audio
    audio_prefix = os.path.join(OUTPUT_DIR, f"{demo_name}_narration")
    temp_audio_prefix = os.path.join(OUTPUT_DIR, f"{demo_name}_narration_tmp")
    existing_audio_path = find_existing_audio_output(audio_prefix)
    remove_existing_audio_outputs(temp_audio_prefix)

    # Try Gemini first, then gTTS fallback
    audio_path = generate_audio_gemini(script, temp_audio_prefix)
    if not audio_path:
        audio_path = generate_audio_gtts_fallback(script, temp_audio_prefix)

    if audio_path:
        _, extension = os.path.splitext(audio_path)
        final_audio_path = f"{audio_prefix}{extension}"
        remove_existing_audio_outputs(audio_prefix)
        os.replace(audio_path, final_audio_path)
        return final_audio_path
    else:
        remove_existing_audio_outputs(temp_audio_prefix)
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
