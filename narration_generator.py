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


def generate_narration_script(steps_json_path: str) -> str:
    """Convert steps JSON into a natural narration script."""
    with open(steps_json_path) as f:
        steps = json.load(f)

    narration_parts = []
    for step in steps:
        desc = step["description"]
        narration_parts.append(f"Step {step['step']}: {desc}.")

    # Keep the spoken script tightly aligned with the on-screen captions.
    return "\n".join(narration_parts)


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
    script = generate_narration_script(steps_path)
    print(f"\n  Narration script ({len(script)} chars):")
    print(f"  {script[:200]}...")

    # Save script as text
    script_path = os.path.join(OUTPUT_DIR, f"{demo_name}_narration.txt")
    with open(script_path, "w") as f:
        f.write(script)

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
