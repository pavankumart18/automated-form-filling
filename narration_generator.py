"""
narration_generator.py - Generate audio narration from step transcripts.
Supports ElevenLabs, Gemini, and a gTTS fallback for text-to-speech generation.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
SUPPORTED_AUDIO_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a")
OPENING_CUES = [
    "Alright, let's dive right in.",
    "Okay, here we go.",
    "Let's set the scene.",
    "*claps hands* Let's get to work.",
]
EARLY_TRANSITION_CUES = [
    "Good, now we're getting to the interesting part.",
    "Alright, this is where things start to click.",
    "Nice. Now we can focus on what actually matters.",
    "And there it is... our first real clue.",
]
MID_TRANSITION_CUES = [
    "Okay, watch this part closely.",
    "Now here's where it gets good.",
    "This is the part that makes the whole thing worth it.",
    "*smirks* Watch what happens next.",
]
LATE_TRANSITION_CUES = [
    "Almost there, and you can already see the payoff.",
    "We're in the home stretch now.",
    "Just a couple more moves and we're done.",
]
SOFT_TRANSITION_CUES = [
    "Moving along smoothly.",
    "Let's keep going, step by step.",
    "Nice and steady, on to the next part.",
    "Continuing the process carefully.",
]
FINALE_CUES = [
    "And that's a wrap.",
    "And just like that, we're done.",
    "There it is, mission accomplished. *chuckles*",
    "Easy enough, right?",
]
WAITING_ASIDES = [
    "Just a moment while the page catches up with us. *laughs* No rush.",
    "Quick breather here while things load.",
    "The page is still doing its thing... any second now.",
]
WAITING_ASIDES_SAFE = [
    "Give the page a second to finish loading.",
    "Short pause while everything settles.",
    "Still loading, so we'll wait right here.",
]
FALLBACK_WAITING_ASIDES = [
    "One moment while this loads.",
    "Let's give it a second.",
    "Quick pause while the results come in.",
]
OVERPASS_WAITING_ASIDES = [
    "The map is crunching through the data, give it a sec.",
    "Processing all those map nodes takes a moment. *chuckles*",
    "Rendering the results now, almost there.",
    "Just loading the map data, won't be long.",
]
OVERPASS_FALLBACK_WAITING_ASIDES = [
    "Map's still loading, hang tight.",
    "One moment while the map renders.",
    "Quick pause for the map data.",
    "Almost there, just rendering.",
]
SCREENER_WAITING_ASIDES = [
    "Loading the financial data... markets are never in a hurry.",
    "Screener is pulling up the numbers. Any second now.",
    "Quick pause while the data populates.",
]
SCREENER_FALLBACK_WAITING_ASIDES = [
    "Screener's loading, one sec.",
    "Data is coming in, hang tight.",
    "Just a moment for the numbers.",
]
ZOHO_WAITING_ASIDES = [
    "The form is updating the calculations... math is hard, let's give it a second.",
    "Give the invoice a moment to recalculate.",
    "Quick pause while the totals update.",
]
ZOHO_FALLBACK_WAITING_ASIDES = [
    "Invoice is updating, one moment.",
    "Totals are recalculating.",
    "Just a second for the form.",
]
TINKERCAD_WAITING_ASIDES = [
    "TinkerCAD is loading the content. Creativity takes time! *laughs*",
    "Just a moment while the page renders.",
    "Gallery is loading up, almost there.",
]
TINKERCAD_FALLBACK_WAITING_ASIDES = [
    "TinkerCAD's loading, one sec.",
    "Quick pause for the gallery.",
    "Content is rendering, hang tight.",
]
INDIAN_VISA_WAITING_ASIDES = [
    "The portal is validating the details... government servers, you know how it is. *laughs*",
    "Government portals can be a bit slow, we'll wait patiently.",
    "Form is refreshing the options, just a second.",
]
INDIAN_VISA_FALLBACK_WAITING_ASIDES = [
    "Portal is still loading.",
    "Options are refreshing, one moment.",
    "Still processing the form data.",
]
DEFAULT_TTS_DIRECTION = (
    "Speak like a captivating storyteller or documentary narrator revealing a profound and fascinating narrative. "
    "Do NOT sound like you are giving instructions or doing a tutorial. Instead, sound like you are "
    "uncovering a mystery or telling an enchanting fable. Use dynamic pacing, a tone of discovery, "
    "and dramatic pauses to let the words sink in. Make it beautiful, emotional, and thoroughly engaging."
)
DEFAULT_ELEVENLABS_VOICE_ID = "jfIS2w2yJi0grJZPyEsk"
DEFAULT_ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"
MAX_AUDIO_SPEEDUP = 1.4
ELEVENLABS_MAX_AUDIO_SPEEDUP = 2.0
DEFAULT_AUDIO_PACE = 0.94
ELEVENLABS_AUDIO_PACE = 1.02
FALLBACK_AUDIO_PACE = 0.96
BALANCED_AUDIO_PACE = 1.0
BALANCED_MAX_AUDIO_SPEEDUP = 1.18
BALANCED_PREFERRED_SPEEDUP = 1.08
AUDIO_FIT_TOLERANCE_SEC = 0.12
GEMINI_QUOTA_EXHAUSTED = False
ELEVENLABS_VOICE_UNAVAILABLE = False
LONG_STEP_FILLER_THRESHOLD_SEC = 11.5
OVERPASS_FILLER_THRESHOLD_SEC = 7.4
SCREENER_FILLER_THRESHOLD_SEC = 7.9
ZOHO_FILLER_THRESHOLD_SEC = 8.9
TINKERCAD_FILLER_THRESHOLD_SEC = 7.8
INDIAN_VISA_FILLER_THRESHOLD_SEC = 7.5
EBAY_FILLER_THRESHOLD_SEC = 7.6
CUSTOM_SCREENER_TIMELINE_SEGMENTS = [
    {
        "start_step": 1,
        "end_step": 2,
        "target_start_sec": 0.0,
        "target_end_sec": 7.0,
        "text": (
            "Most people pick stocks on gut. Let's change that. Open Screener. Search Reliance."
        ),
        "fallback_text": (
            "Most people pick stocks on gut. Let's change that. Open Screener. Search Reliance."
        ),
        "subtitle": "Open Screener and type Reliance Industries.",
    },
    {
        "start_step": 3,
        "end_step": 3,
        "target_start_sec": 7.0,
        "target_end_sec": 14.0,
        "text": (
            "There it is. Click Reliance. Now the real checklist begins."
        ),
        "fallback_text": (
            "There it is. Click Reliance. Now the real checklist begins."
        ),
        "subtitle": "Click Reliance and open the company page.",
    },
    {
        "start_step": 4,
        "end_step": 5,
        "target_start_sec": 14.0,
        "target_end_sec": 25.0,
        "text": (
            "First, check the big three at the top: Market Cap, P/E, and ROCE. Then open quarterly results and make sure profits are actually climbing."
        ),
        "fallback_text": (
            "First, check the big three at the top: Market Cap, P/E, and ROCE. Then open quarterly results and make sure profits are actually climbing."
        ),
        "subtitle": "Check the top metrics, then open quarterly results.",
    },
    {
        "start_step": 6,
        "end_step": 7,
        "target_start_sec": 25.0,
        "target_end_sec": 36.0,
        "text": (
            "Next, sweep through Profit and Loss and the Balance Sheet. Revenues should rise, earnings should look clean, and debt should stay under control."
        ),
        "fallback_text": (
            "Next, sweep through Profit and Loss and the Balance Sheet. Revenues should rise, earnings should look clean, and debt should stay under control."
        ),
        "subtitle": "Check Profit and Loss, then the Balance Sheet.",
    },
    {
        "start_step": 8,
        "end_step": 8,
        "target_start_sec": 36.0,
        "target_end_sec": 43.0,
        "text": (
            "No stock idea yet? Hit Screens. That is your cheat code."
        ),
        "fallback_text": (
            "No stock idea yet? Hit Screens. That is your cheat code."
        ),
        "subtitle": "No stock idea yet? Click Screens.",
    },
    {
        "start_step": 9,
        "end_step": 11,
        "target_start_sec": 43.0,
        "target_end_sec": 56.0,
        "text": (
            "Now click Show all screens and find this exact filter: High Growth, High RoE, Low PE. Fast growers, efficient businesses, sane valuation. Open it."
        ),
        "fallback_text": (
            "Now click Show all screens and find this exact filter: High Growth, High RoE, Low PE. Fast growers, efficient businesses, sane valuation. Open it."
        ),
        "subtitle": "Find and open the High Growth, High RoE, Low PE screen.",
    },
    {
        "start_step": 12,
        "end_step": 13,
        "target_start_sec": 56.0,
        "target_end_sec": 67.0,
        "text": (
            "The filter has done the hunting. Ganesh Infra makes the shortlist, so open it and run the same four-point check. That is how you go from guessing to investing with a plan."
        ),
        "fallback_text": (
            "The filter has done the hunting. Ganesh Infra makes the shortlist, so open it and run the same four-point check. That is how you go from guessing to investing with a plan."
        ),
        "subtitle": "Open Ganesh Infra and run the same four-point check.",
    },
]
CUSTOM_ZOHO_TIMELINE_SEGMENTS = [
    {
        "start_step": 1,
        "end_step": 2,
        "target_start_sec": 0.0,
        "target_end_sec": 17.2,
        "text": (
            "Listen up, freelancers and small biz heroes! Tired of sending invoices that look like they were made in MS Paint? Today, I'm showing you how to go from broke to professional in under two minutes using Zoho's free invoice generator. No login, no soul-crushing forms, just pure efficiency. Let's ride!"
        ),
        "fallback_text": (
            "Listen up, freelancers and small biz heroes! Tired of sending invoices that look like they were made in MS Paint? Today, I'm showing you how to go from broke to professional in under two minutes using Zoho's free invoice generator. No login, no soul-crushing forms, just pure efficiency. Let's ride!"
        ),
        "subtitle": "Open Zoho Invoice and jump into the free invoice generator.",
    },
    {
        "start_step": 3,
        "end_step": 5,
        "target_start_sec": 17.2,
        "target_end_sec": 49.5,
        "text": (
            "Look at that clean UI. Fresh breath of mountain air for your finances. Boom, we're in the cockpit. Time to tell the world who you are. Type in your company name, your name, and your address. Deep breath. The internet is doing its magic. We're officially a business entity, people! Who's paying us? Enter Acme Corp International. Give them a professional address in Mumbai. We aren't just sending a bill; we're sending a statement. Give this masterpiece a number. INV-2026-001, the first of many!"
        ),
        "fallback_text": (
            "Look at that clean UI. Fresh breath of mountain air for your finances. Boom, we're in the cockpit. Time to tell the world who you are. Type in your company name, your name, and your address. Deep breath. The internet is doing its magic. We're officially a business entity, people! Who's paying us? Enter Acme Corp International. Give them a professional address in Mumbai. We aren't just sending a bill; we're sending a statement. Give this masterpiece a number. INV-2026-001, the first of many!"
        ),
        "subtitle": "Enter your business details, client details, and invoice number.",
    },
    {
        "start_step": 6,
        "end_step": 6,
        "target_start_sec": 49.5,
        "target_end_sec": 59.6,
        "text": (
            "Now let's add our first line item: Web Development Services. Forty hours of your genius, don't lowball yourself! Set that GST rate and watch the numbers dance."
        ),
        "fallback_text": (
            "Now let's add our first line item: Web Development Services. Forty hours of your genius, don't lowball yourself! Set that GST rate and watch the numbers dance."
        ),
        "subtitle": "Add the first line item and set the GST.",
    },
    {
        "start_step": 7,
        "end_step": 8,
        "target_start_sec": 59.6,
        "target_end_sec": 78.5,
        "text": (
            "Let's stack those services. UI/UX Design? Check. Annual Server Hosting? Check. Now we let Zoho do the heavy lifting. We are not here for mental math. I didn't come here to calculate 9% of 160,000 in my head; I have a life to live!"
        ),
        "fallback_text": (
            "Let's stack those services. UI/UX Design? Check. Annual Server Hosting? Check. Now we let Zoho do the heavy lifting. We are not here for mental math. I didn't come here to calculate 9% of 160,000 in my head; I have a life to live!"
        ),
        "subtitle": "Add the remaining services and let Zoho handle the math.",
    },
    {
        "start_step": 9,
        "end_step": 9,
        "target_start_sec": 78.5,
        "target_end_sec": 89.3,
        "text": (
            "Step nine: drop in the fine print. Payment due within 30 days. Add the bank details. Quick pause while the totals update. It's like a slot machine spin, except you actually win."
        ),
        "fallback_text": (
            "Step nine: drop in the fine print. Payment due within 30 days. Add the bank details. Quick pause while the totals update. It's like a slot machine spin, except you actually win."
        ),
        "subtitle": "Add the payment terms and bank details.",
    },
    {
        "start_step": 10,
        "end_step": 10,
        "target_start_sec": 89.3,
        "target_end_sec": 94.3,
        "text": (
            "Step ten: review the subtotal and grand total. That's the sound of success."
        ),
        "fallback_text": (
            "Step ten: review the subtotal and grand total. That's the sound of success."
        ),
        "subtitle": "Review the subtotal and grand total.",
    },
    {
        "start_step": 11,
        "end_step": 12,
        "target_start_sec": 94.3,
        "target_end_sec": 104.2,
        "text": (
            "Everything looks crisp and legal. Hit Download/Print, export the PDF, and send it off. Tutorial complete. Your coffee is still cooling. Go get that bread!"
        ),
        "fallback_text": (
            "Everything looks crisp and legal. Hit Download/Print, export the PDF, and send it off. Tutorial complete. Your coffee is still cooling. Go get that bread!"
        ),
        "subtitle": "Export the PDF and finish the invoice.",
    },
]
CUSTOM_TINKERCAD_TIMELINE_SEGMENTS = [
    {
        "start_step": 1,
        "end_step": 2,
        "target_start_sec": 0.0,
        "target_end_sec": 18.2,
        "text": (
            "Open Tinkercad, head into the Learning Center, and start with the beginner lessons. No login, no maze, just the fast lane into 3D design, which is exactly how tutorials should behave."
        ),
        "fallback_text": (
            "Open Tinkercad, head into the Learning Center, and start with the beginner lessons. No login, no maze, just the fast lane into 3D design, which is exactly how tutorials should behave."
        ),
        "subtitle": "Open Tinkercad, then go to the Learning Center.",
    },
    {
        "start_step": 3,
        "end_step": 4,
        "target_start_sec": 18.2,
        "target_end_sec": 31.2,
        "text": (
            "Search 3D design basics, then jump back into the 3D Design track so the CAD lessons stay front and center. We are not wandering the menu today; we are building a clean on-ramp."
        ),
        "fallback_text": (
            "Search 3D design basics, then jump back into the 3D Design track so the CAD lessons stay front and center."
        ),
        "subtitle": "Search beginner basics, then return to the 3D Design track.",
    },
    {
        "start_step": 5,
        "end_step": 6,
        "target_start_sec": 31.2,
        "target_end_sec": 44.3,
        "text": (
            "Open a lesson card and scroll through it. This is the quality check. We want clear visuals, actual steps, and enough detail to keep a beginner moving."
        ),
        "fallback_text": (
            "Open a lesson card and scroll through it. We want clear visuals, actual steps, and enough detail to keep a beginner moving."
        ),
        "subtitle": "Open a lesson card and review the tutorial details.",
    },
    {
        "start_step": 7,
        "end_step": 7,
        "target_start_sec": 44.3,
        "target_end_sec": 54.8,
        "text": (
            "Now jump to the gallery. Community projects are where you steal shapes, collect ideas, spot clever shortcuts, and find the spark that gets you building instead of overthinking."
        ),
        "fallback_text": (
            "Now jump to the gallery. Community projects are where you steal shapes, collect ideas, spot clever shortcuts, and find the spark that gets you building instead of overthinking."
        ),
        "subtitle": "Open the gallery for project inspiration.",
    },
    {
        "start_step": 8,
        "end_step": 8,
        "target_start_sec": 54.8,
        "target_end_sec": 65.9,
        "text": (
            "Browse the gallery for a practical idea, something like a phone stand. Inspiration beats staring at a blank canvas and pretending that counts as design research."
        ),
        "fallback_text": (
            "Browse the gallery for a practical idea, something like a phone stand. Inspiration beats staring at a blank canvas."
        ),
        "subtitle": "Browse the gallery for a practical idea.",
    },
    {
        "start_step": 9,
        "end_step": 9,
        "target_start_sec": 65.9,
        "target_end_sec": 71.2,
        "text": (
            "Open one design. Borrow momentum."
        ),
        "fallback_text": (
            "Open one design. Borrow momentum."
        ),
        "subtitle": "Open a design page for inspiration.",
    },
    {
        "start_step": 10,
        "end_step": 10,
        "target_start_sec": 71.2,
        "target_end_sec": 75.7,
        "text": (
            "Learn. Browse. Build."
        ),
        "fallback_text": (
            "Learn. Browse. Build."
        ),
        "subtitle": "Finish the Tinkercad speedrun.",
    },
]
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
        "And now we have our starting point.",
        "Perfect, this is where everything begins.",
        "Great, we're all set up and ready to go.",
    ],
    "navigate": [
        "Straight to the right page, no detours.",
        "And boom, we're exactly where we need to be.",
        "That takes us right to the good stuff.",
    ],
    "search": [
        "That narrows things down instantly.",
        "And just like that, we've got our results.",
        "Search does the heavy lifting for us here.",
    ],
    "view": [
        "Now we can see what we're working with.",
        "There's our data, clear as day.",
        "And the key information is right here.",
    ],
    "review": [
        "Let's take a closer look at what we've got.",
        "Now this is where the insights start appearing.",
        "Really useful data to dig into here.",
    ],
    "inspect": [
        "The details here are worth paying attention to.",
        "Let's zoom in and see what's really going on.",
        "A closer look reveals some interesting stuff.",
    ],
    "check": [
        "Quick sanity check to make sure everything looks right.",
        "Always good to verify before moving on.",
        "Let's confirm this is all looking correct.",
    ],
    "browse": [
        "Easy to compare options from here.",
        "Now we can scan through everything at a glance.",
        "Nice overview that makes picking easier.",
    ],
    "switch": [
        "Different view, and suddenly things are much clearer.",
        "Switching perspective really helps here.",
        "That change makes all the difference.",
    ],
    "replace": [
        "Same process, different input, and it works just as smoothly.",
        "See how easy it is to swap things around?",
        "The beauty is that this workflow is totally reusable.",
    ],
    "add": [
        "Adding this gives us a more complete picture.",
        "One more piece of the puzzle.",
        "That rounds things out nicely.",
    ],
    "run": [
        "And now we hit go and watch the magic happen.",
        "Here's where all the setup pays off.",
        "Let's see what we get.",
    ],
    "fill": [
        "This is the kind of tedious work that automation handles perfectly.",
        "Imagine doing this manually every time. Exactly.",
        "Automation at its finest right here.",
    ],
    "enter": [
        "Quick data entry, and we're moving on.",
        "Just plugging in the details.",
        "Type it once, and it's done forever.",
    ],
    "set": [
        "That little setting makes a big difference.",
        "Small detail, but it keeps everything consistent.",
        "Precision matters here, and we've got it set.",
    ],
    "choose": [
        "Making our selection clear and deliberate.",
        "An easy choice when you know what you need.",
        "That decision locks in our direction.",
    ],
    "select": [
        "Clean pick, no ambiguity.",
        "Selected and ready to go.",
        "That keeps the workflow predictable and reliable.",
    ],
    "move": [
        "Smooth transition to the next section.",
        "Simple move that keeps everything flowing.",
        "And we're right where we need to be.",
    ],
    "go": [
        "Onward, keeping the momentum going.",
        "Moving right along without losing our place.",
        "And we continue the flow seamlessly.",
    ],
    "complete": [
        "And that's the finish line right there.",
        "Done! Exactly the result we were after.",
        "Everything comes together perfectly.",
    ],
    "use": [
        "Now we're actually putting this to work.",
        "This is where the real value shows up.",
        "Practical and useful, just the way it should be.",
    ],
    "download": [
        "And now we have something tangible to show for it.",
        "Download ready, that's a real deliverable.",
        "The output is ready to use right away.",
    ],
    "export": [
        "Exporting so we can use this outside the browser.",
        "Now this data can go anywhere we need it.",
        "Clean export, ready for the next step.",
    ],
    "split": [
        "Side by side makes it so much easier to compare.",
        "Now we can see both halves of the picture at once.",
        "This layout tells the whole story in one glance.",
    ],
    "write": [
        "Writing it out so anyone can follow along.",
        "Now the logic is transparent and repeatable.",
        "Once it's written down, anyone can reproduce this.",
    ],
    "click": [
        "One click, and we're there.",
        "Simple and precise.",
        "Easy to follow, easy to repeat.",
    ],
    "stop": [
        "We stop here on purpose, this is the safe boundary.",
        "That's our stopping point, clean and deliberate.",
        "We know exactly where to draw the line.",
    ],
}
COMPACT_STORY_TAGS = {
    "open": "And we're up and running.",
    "navigate": "Right where we need to be.",
    "search": "Results come up instantly.",
    "view": "Clear view of what matters.",
    "review": "The data speaks for itself.",
    "inspect": "Worth a closer look.",
    "check": "Quick verification.",
    "browse": "Easy to scan through.",
    "switch": "Better angle on the data.",
    "replace": "Same flow, fresh input.",
    "add": "Building out the full picture.",
    "run": "And we get our results.",
    "fill": "Automation handles the tedium.",
    "enter": "Punched in and done.",
    "set": "Locked in.",
    "choose": "Decision made.",
    "select": "Clean selection.",
    "move": "Smooth transition.",
    "go": "Keeping the flow going.",
    "use": "Putting it to work.",
    "download": "Ready to use offline.",
    "export": "Data is portable now.",
    "split": "Both sides visible at once.",
    "write": "Logic is on screen.",
    "click": "One click, done.",
    "stop": "Safe stopping point.",
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


def sanitize_tts_text(text: str) -> str:
    """Strip non-spoken stage directions so TTS reads more naturally."""
    cleaned = text or ""
    cleaned = re.sub(r"\*\s*\[[^\]]+\]\s*\*", " ", cleaned)
    cleaned = re.sub(r"\[[^\]]+\]", " ", cleaned)
    cleaned = re.sub(r"\*[^*\n]+\*", " ", cleaned)
    cleaned = cleaned.replace("**", " ")
    return " ".join(cleaned.split())


def elevenlabs_api_key_from_env() -> str | None:
    """Return the configured ElevenLabs API key from common env variable names."""
    return os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_LABS_API_KEY")


def elevenlabs_voice_id_from_env() -> str:
    """Return the voice id to use for ElevenLabs narration."""
    return (
        os.environ.get("ELEVENLABS_VOICE_ID")
        or os.environ.get("ELEVEN_LABS_VOICE_ID")
        or DEFAULT_ELEVENLABS_VOICE_ID
    )


def elevenlabs_model_id_from_env() -> str:
    """Return the ElevenLabs model id for narration generation."""
    return os.environ.get("ELEVENLABS_MODEL_ID", DEFAULT_ELEVENLABS_MODEL_ID)


def elevenlabs_output_format_from_env() -> str:
    """Return the desired ElevenLabs audio output format."""
    return os.environ.get("ELEVENLABS_OUTPUT_FORMAT", DEFAULT_ELEVENLABS_OUTPUT_FORMAT)


def extension_for_output_format(output_format: str | None) -> str:
    """Map an ElevenLabs output format to a file extension."""
    format_key = (output_format or "").split("_", 1)[0].lower()
    mapping = {
        "mp3": ".mp3",
        "wav": ".wav",
        "pcm": ".wav",
        "ulaw": ".wav",
    }
    return mapping.get(format_key, ".mp3")


def narration_provider_order() -> list[str]:
    """Choose a TTS provider order from the environment, favoring ElevenLabs."""
    configured = (os.environ.get("NARRATION_TTS_PROVIDER") or "auto").strip().lower()
    if configured == "elevenlabs":
        return ["elevenlabs", "gemini", "gtts"]
    if configured == "gemini":
        return ["gemini", "elevenlabs", "gtts"]
    if configured == "gtts":
        return ["gtts"]
    return ["elevenlabs", "gemini", "gtts"]


def is_elevenlabs_voice_unavailable(error_text: str) -> bool:
    """Detect account or plan errors that will fail every future ElevenLabs segment."""
    lowered = (error_text or "").lower()
    return (
        "paid_plan_required" in lowered
        or "free users cannot use library voices" in lowered
        or "quota_exceeded" in lowered
    )


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


def fit_audio_clip_to_duration(
    input_path: str,
    max_duration: float,
    output_path: str,
    max_speedup: float = MAX_AUDIO_SPEEDUP,
):
    """Speed up an audio clip only a little if it would overflow its timing budget."""
    current_duration = get_media_duration(input_path)
    if max_duration <= 0 or current_duration <= max_duration + 0.06:
        return input_path, current_duration

    speed_factor = current_duration / max_duration
    if speed_factor <= 1.05:
        return input_path, current_duration

    applied_speed = min(speed_factor, max_speedup)
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


def is_overpass_step(description: str, url: str = "") -> bool:
    """Identify Overpass/map-query steps so we can keep that demo playful but tight."""
    lowered = f"{normalize_text(description).lower()} {url.lower()}".strip()
    overpass_tokens = [
        "overpass",
        "query",
        "geojson",
        "charging station",
        "map view",
        "zoom to data",
        "data tab",
        "pharmacy",
        "school",
        "hospital",
    ]
    return "overpass-turbo" in lowered or any(token in lowered for token in overpass_tokens)


def is_screener_step(description: str, url: str = "") -> bool:
    """Identify Screener stock-research steps for custom story pacing."""
    lowered = f"{normalize_text(description).lower()} {url.lower()}".strip()
    screener_tokens = [
        "screener.in",
        "public screens",
        "reliance industries",
        "profit and loss",
        "balance sheet",
        "market cap",
        "valuation snapshot",
        "quarterly financial",
        "bank of india",
    ]
    return (
        "screener.in" in lowered
        or any(token in lowered for token in screener_tokens)
        or re.search(r"\b(?:roe|roce)\b", lowered) is not None
    )


def is_zoho_invoice_step(description: str, url: str = "") -> bool:
    """Identify Zoho Invoice form-filling steps for custom pacing and story tone."""
    lowered = f"{normalize_text(description).lower()} {url.lower()}".strip()
    zoho_tokens = [
        "zoho invoice",
        "invoice generator",
        "business details",
        "bill to",
        "client details",
        "gst",
        "line item",
        "invoice number",
        "payment notes",
        "payment terms",
        "download/print",
        "professional gst invoices",
    ]
    return (
        "zoho.com/invoice" in lowered
        or "zoho.com/in/invoice" in lowered
        or any(token in lowered for token in zoho_tokens)
    )


def is_mondula_step(description: str, url: str = "") -> bool:
    """Identify Mondula form-demo steps for custom pacing and punchier narration."""
    lowered = f"{normalize_text(description).lower()} {url.lower()}".strip()
    mondula_tokens = [
        "mondula",
        "intro page",
        "first form step",
        "textarea",
        "date fields",
        "radio option",
        "checkboxes",
        "dropdown value",
        "conditional input section",
        "selected dish",
        "contact-details page",
        "submit-ready final state",
    ]
    return "mondula.com/msf-demo" in lowered or any(token in lowered for token in mondula_tokens)


def is_tinkercad_step(description: str, url: str = "") -> bool:
    """Identify TinkerCAD learning/gallery steps for custom pacing and story tone."""
    lowered = f"{normalize_text(description).lower()} {url.lower()}".strip()
    tinkercad_tokens = [
        "tinkercad",
        "learning center",
        "3d design tutorials",
        "gallery designs",
        "guided learning content",
        "circuits category",
        "phone stand",
    ]
    return "tinkercad.com" in lowered or any(token in lowered for token in tinkercad_tokens)


def is_indian_visa_step(description: str, url: str = "") -> bool:
    """Identify Indian eVisa steps for careful pacing on slow portal refreshes."""
    lowered = f"{normalize_text(description).lower()} {url.lower()}".strip()
    visa_tokens = [
        "indian evisa",
        "evisa",
        "captcha step",
        "nationality and passport type",
        "port of arrival",
        "visa service",
        "date of arrival",
    ]
    return "indianvisaonline.gov.in" in lowered or any(token in lowered for token in visa_tokens)


def is_ebay_step(description: str, url: str = "") -> bool:
    """Identify eBay Advanced Search steps for a punchier shopping-heist tone."""
    lowered = f"{normalize_text(description).lower()} {url.lower()}".strip()
    ebay_tokens = [
        "ebay advanced search",
        "keyword match dropdown",
        "exact order",
        "exclude from results",
        "title and description",
        "price filters",
        "new-condition items",
        "filtered results page",
        "wh-1000xm5",
    ]
    return (
        "ebay.com/sch/ebayadvsearch" in lowered
        or "ebay.com/sch/i.html" in lowered
        or any(token in lowered for token in ebay_tokens)
    )


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
    if is_overpass_step(description, url):
        custom_overpass_line = overpass_waiting_aside(description)
        if custom_overpass_line:
            return custom_overpass_line
        return pick_variant(OVERPASS_WAITING_ASIDES, step_num)
    if is_screener_step(description, url):
        return pick_variant(SCREENER_WAITING_ASIDES, step_num)
    if is_zoho_invoice_step(description, url):
        custom_zoho_line = zoho_waiting_aside(description)
        if custom_zoho_line:
            return custom_zoho_line
        return pick_variant(ZOHO_WAITING_ASIDES, step_num)
    if is_tinkercad_step(description, url):
        custom_tinkercad_line = tinkercad_waiting_aside(description)
        if custom_tinkercad_line:
            return custom_tinkercad_line
        return pick_variant(TINKERCAD_WAITING_ASIDES, step_num)
    if is_indian_visa_step(description, url):
        custom_visa_line = indian_visa_waiting_aside(description)
        if custom_visa_line:
            return custom_visa_line
        return pick_variant(INDIAN_VISA_WAITING_ASIDES, step_num)
    if is_ebay_step(description, url):
        custom_ebay_line = ebay_waiting_aside(description)
        if custom_ebay_line:
            return custom_ebay_line
        return pick_variant(WAITING_ASIDES, step_num)
    variants = WAITING_ASIDES_SAFE if is_sensitive_step(description, url) else WAITING_ASIDES
    return pick_variant(variants, step_num)


def build_fallback_waiting_aside(step: dict, step_num: int) -> str:
    """Generate a very short filler line for fallback narration."""
    if is_overpass_step(step.get("description", ""), step.get("url", "")):
        custom_overpass_line = overpass_fallback_waiting_aside(step.get("description", ""))
        if custom_overpass_line:
            return custom_overpass_line
        return pick_variant(OVERPASS_FALLBACK_WAITING_ASIDES, step_num)
    if is_screener_step(step.get("description", ""), step.get("url", "")):
        return pick_variant(SCREENER_FALLBACK_WAITING_ASIDES, step_num)
    if is_zoho_invoice_step(step.get("description", ""), step.get("url", "")):
        custom_zoho_line = zoho_fallback_waiting_aside(step.get("description", ""))
        if custom_zoho_line:
            return custom_zoho_line
        return pick_variant(ZOHO_FALLBACK_WAITING_ASIDES, step_num)
    if is_tinkercad_step(step.get("description", ""), step.get("url", "")):
        custom_tinkercad_line = tinkercad_fallback_waiting_aside(step.get("description", ""))
        if custom_tinkercad_line:
            return custom_tinkercad_line
        return pick_variant(TINKERCAD_FALLBACK_WAITING_ASIDES, step_num)
    if is_indian_visa_step(step.get("description", ""), step.get("url", "")):
        custom_visa_line = indian_visa_fallback_waiting_aside(step.get("description", ""))
        if custom_visa_line:
            return custom_visa_line
        return pick_variant(INDIAN_VISA_FALLBACK_WAITING_ASIDES, step_num)
    if is_ebay_step(step.get("description", ""), step.get("url", "")):
        custom_ebay_line = ebay_fallback_waiting_aside(step.get("description", ""))
        if custom_ebay_line:
            return custom_ebay_line
        return pick_variant(FALLBACK_WAITING_ASIDES, step_num)
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


def overpass_fallback_line(description: str, step_num: int, total_steps: int) -> str | None:
    """Return a concise, more interesting spoken line for Overpass steps."""
    lowered = normalize_text(description).lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "That wraps the Overpass run."
    if "open overpass turbo" in lowered:
        return "Open Overpass Turbo and load the workspace."
    if "split view" in lowered:
        return "Split view: editor left, map right."
    if "write a hyderabad hospitals query" in lowered:
        return "Write the Hyderabad hospitals query."
    if "run query to load all mapped hospitals" in lowered:
        return "Run the hospitals query."
    if "zoom to data" in lowered:
        return "Zoom straight to the results."
    if "click map markers" in lowered:
        return "Inspect marker tags."
    if "open data tab" in lowered:
        return "Open the Data tab."
    if "switch back to map view" in lowered:
        return "Back to the Map view."
    if "replace with ev charging station query" in lowered:
        return "Swap to EV charging stations."
    if "rendered; now compare" in lowered or "compare spread versus healthcare locations" in lowered:
        return "Compare EV chargers with hospitals."
    if "run school query" in lowered:
        return "Run the schools query."
    if "add pharmacy query" in lowered:
        return "Add pharmacies as the fourth layer."
    if "single editor workflow" in lowered:
        return "One editor, rapid iteration."
    if "open export options" in lowered:
        return "Open Export options."
    if "export supports geojson" in lowered or "choose geojson" in lowered:
        return "Choose a format like GeoJSON."

    if step_num == total_steps:
        return "That wraps the Overpass run."
    return None


def overpass_story_line(description: str) -> str | None:
    """Return a richer primary narration line for Overpass that still fits the timing windows."""
    lowered = normalize_text(description).lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "Tutorial complete. Blank screen to geo-intelligence. Go bend maps to your will."
    if "open overpass turbo" in lowered:
        return "Welcome to the cockpit, data hunters. Overpass Turbo is live. Calm canvas now, storm next."
    if "split view" in lowered:
        return "Split view. Query wand on the left, map battlefield on the right."
    if "write a hyderabad hospitals query" in lowered:
        return "Hospitals in Hyderabad. Fixed city box, full Overpass QL, nodes, ways, relations. Feed the machine."
    if "run query to load all mapped hospitals" in lowered:
        return "Run it. The API is sprinting across the planet to fetch every hospital marker it can find."
    if "zoom to data" in lowered:
        return "Blue circles everywhere. Zoom to data and teleport onto Hyderabad."
    if "click map markers" in lowered:
        return "Click a marker and read the tags. Name, address, amenity type. Pure urban DNA."
    if "open data tab" in lowered:
        return "Hit the Data tab. Raw OSM attributes. Nerd heaven."
    if "switch back to map view" in lowered:
        return "Back to Map view so we can compare actual coverage."
    if "replace with ev charging station query" in lowered:
        return "Pivot time. Swap hospitals for EV chargers. Same city, totally different future."
    if "rendered; now compare" in lowered or "compare spread versus healthcare locations" in lowered:
        return "Rendering complete. See those gaps? That is urban planning screaming for attention."
    if "run school query" in lowered:
        return "Now add schools. Education layer, same boundary. Watch the city grow in fast-forward."
    if "add pharmacy query" in lowered:
        return "One more. Add pharmacies and build a four-layer dataset cake. City hall wishes it had this."
    if "single editor workflow" in lowered:
        return "Single editor workflow. That is the superpower: iterate faster, analyze deeper, conquer the urban jungle."
    if "open export options" in lowered:
        return "Open Export. We are done playing; now we go pro."
    if "export supports geojson" in lowered or "choose geojson" in lowered:
        return "GeoJSON, KML, GPX, raw OSM. Pick your ammo and ship the data."
    return None


def overpass_waiting_aside(description: str) -> str | None:
    """Return custom wait-cover lines for the Overpass map flow."""
    lowered = normalize_text(description).lower()

    if "open overpass turbo" in lowered:
        return "Map nodes take a second. More math than high school. Boom, rendered."
    if "run query to load all mapped hospitals" in lowered:
        return "The API is hauling hospital markers worldwide. Fast fiber beats virtue."
    if "replace with ev charging station query" in lowered:
        return "Processing again. Come on, little data packets, do your thing."
    if "rendered; now compare" in lowered or "compare spread versus healthcare locations" in lowered:
        return "That spread tells you exactly where the future still needs building."
    if "run school query" in lowered:
        return "Schools are loading. Keep the processors humming. City timelapse, live."
    if "add pharmacy query" in lowered:
        return "Final crunch. If the fan is spinning, that is just the sound of progress."
    if "single editor workflow" in lowered:
        return "One last pass. Look at that density. Pure data art."
    return None


def overpass_fallback_waiting_aside(description: str) -> str | None:
    """Return shorter fallback wait lines for Overpass steps."""
    lowered = normalize_text(description).lower()

    if "open overpass turbo" in lowered:
        return "Map is rendering now."
    if "run query to load all mapped hospitals" in lowered:
        return "Hospital markers are loading."
    if "replace with ev charging station query" in lowered:
        return "EV charger data is loading."
    if "rendered; now compare" in lowered or "compare spread versus healthcare locations" in lowered:
        return "Comparison view is rendering."
    if "run school query" in lowered:
        return "School data is loading."
    if "add pharmacy query" in lowered:
        return "Map is crunching the final layer."
    if "single editor workflow" in lowered:
        return "One last render pass."
    return None


def screener_fallback_line(description: str, step_num: int, total_steps: int) -> str | None:
    """Return a fallback story beat for Screener."""
    lowered = normalize_text(description).lower()

    if "open screener.in" in lowered:
        return "Most people pick stocks on gut feel. Today we use a real checklist on Screener."
    if "open reliance industries directly" in lowered or "search reliance industries" in lowered:
        return "Search Reliance Industries — India's biggest company, a perfect learning subject."
    if "type reliance industries" in lowered:
        return "Search Reliance Industries — India's biggest company, a perfect learning subject."
    if "click reliance industries" in lowered:
        return "It appears right away. Click it. We are now inside Reliance's full financial profile."
    if "view key metrics" in lowered:
        return "Checkpoint one: Market Cap, P/E, and ROCE. Size, price, and capital efficiency — in three numbers."
    if "review quarterly financial trends" in lowered:
        return "Check quarterly results. Profits should go up every quarter — that line tells the whole story."
    if "inspect profit and loss" in lowered:
        return "Profit and Loss: revenue up, expenses controlled. That gap is the margin that matters."
    if "check balance sheet strength" in lowered:
        return "Balance Sheet: watch the debt. Too much means you're funding their past, not their future."
    if "click screens in the top menu" in lowered or "open the public screens page" in lowered:
        return "No stock idea yet? Click Screens — that's where the platform hunts for you."
    if "show all screens" in lowered:
        return "Click Show all screens — a full library of pre-built investor filters, all free."
    if "find the exact high growth" in lowered:
        return "Find High Growth, High RoE, Low PE — fast, efficient, and cheap. That combination is rare."
    if "click the highlighted high growth" in lowered or "open a public screen" in lowered:
        return "Click it. Screener scans the whole market. Your shortlist appears — no formulas needed."
    if "scan the filtered results table" in lowered or "browse filtered companies" in lowered:
        return "Every name here passed the filter. Ganesh Infra stands out — growth strong, valuation sane."
    if "land on the company page" in lowered or "from the results" in lowered:
        return "Open it. Run the four-point check. It passes — it goes on the shortlist. That is the system."

    if step_num == total_steps:
        return "Search, filter, verify — that is the whole system."
    return None


def screener_story_line(description: str) -> str | None:
    """Return a completely narrative, documentary-style story for Screener."""
    lowered = normalize_text(description).lower()

    if "open screener.in" in lowered:
        return "Most people pick stocks on hot tips and gut feel. Today I'll show you how to do it right — with a repeatable checklist on Screener dot in."
    if "open reliance industries directly" in lowered or "search reliance industries" in lowered:
        return "Your first move: search for a company. Reliance Industries is our example — India's largest, and perfect for learning what healthy financials actually look like."
    if "type reliance industries" in lowered:
        return "Your first move: search for a company. Reliance Industries is our example — India's largest, and perfect for learning what healthy financials actually look like."
    if "click reliance industries" in lowered:
        return "It appears instantly in the dropdown. Click it. We are now inside Reliance's complete financial profile — and the checklist begins."
    if "view key metrics" in lowered:
        return "Top of the page — your first checkpoint. Market Cap tells you the size. P/E tells you if you're overpaying. ROCE tells you if management is actually good at using money."
    if "review quarterly financial trends" in lowered:
        return "Scroll down to quarterly results. This is where the story either holds up or falls apart. You want that profit line going up and to the right — every single quarter."
    if "inspect profit and loss" in lowered:
        return "Next: Profit and Loss. Revenue rising is table stakes. What you really want is expenses growing slower than revenue — that's where the margin lives."
    if "check balance sheet strength" in lowered:
        return "Balance Sheet: how much debt is this company carrying? Too much and you are financing their past, not investing in their future."
    if "click screens in the top menu" in lowered or "open the public screens page" in lowered:
        return "Here's where it gets interesting. You don't need to already have a stock in mind. Click Screens — this is Screener's real superpower."
    if "show all screens" in lowered:
        return "Click Show all screens — a full library of pre-built filters, built by experienced investors, all completely free."
    if "find the exact high growth" in lowered:
        return "Find this filter: High Growth, High RoE, Low PE. Fast-growing, capital-efficient, and not yet overpriced. That combination is rare — and exactly what we are hunting for."
    if "click the highlighted high growth" in lowered or "open the high growth" in lowered or "open a public screen" in lowered:
        return "Click it. Screener scans the entire market and hands you a shortlist in seconds. You did not write a single formula."
    if "scan the filtered results table" in lowered or "browse filtered companies" in lowered:
        return "Every company in this table passed the filter. Scan for clean numbers. Ganesh Infra stands out — strong growth, solid returns, valuation still sane."
    if "land on the company page" in lowered or "from the screen for deeper analysis" in lowered or "open any company from the screen results" in lowered:
        return "Click in and run the same four-point check: P/E, ROCE, quarterly trend, Balance Sheet. It passes — it goes on your shortlist. That is the system."
    return None


def zoho_fallback_line(description: str, step_num: int, total_steps: int) -> str | None:
    """Return concise invoice-demo lines that fit Zoho's form-filling windows."""
    lowered = normalize_text(description).lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "And that's a clean Zoho invoice, done."
    if "open zoho invoice" in lowered:
        return "Open Zoho Invoice."
    if "free invoice generator" in lowered:
        return "Jump into the free generator. No login needed."
    if "enter business details" in lowered:
        return "Add your company details first."
    if "enter bill to details" in lowered:
        return "Now fill in the client details."
    if "set invoice number" in lowered:
        return "Set the invoice number."
    if "add line item 1" in lowered:
        return "Add the first billable item."
    if "add line item 2" in lowered:
        return "Add the second line item."
    if "add line item 3" in lowered:
        return "Add the hosting line item."
    if "add payment notes and terms" in lowered:
        return "Add the payment terms and bank details."
    if "review subtotal" in lowered or "gst breakdown" in lowered:
        return "Check the totals and GST."
    if "download/print" in lowered or "export the invoice as pdf" in lowered:
        return "Download the invoice as a PDF."

    if step_num == total_steps:
        return "And that's a clean Zoho invoice, done."
    return None


def zoho_story_line(description: str) -> str | None:
    """Return a warmer story line for the Zoho invoice flow."""
    lowered = normalize_text(description).lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "Flawless GST invoice in under two minutes. Now go get your money!"
    if "open zoho invoice" in lowered:
        return "Alright hustlers and founders, stop crying over broken spreadsheets! Today, we are generating a pristine, professional GST invoice using Zoho Invoice."
    if "free invoice generator" in lowered:
        return "The best part? It's free and needs zero logins. No passwords to forget today. Fire up the free generator page and let's get this bread."
    if "enter business details" in lowered:
        return "Boom, we're in. First up, who's getting paid? We are. Type in your company name, TechStar Solutions, your name, and address."
    if "enter bill to details" in lowered:
        return "Time to bill the big fish. Enter the client details: Acme Corp International. Drop in their address and lock in the billing state, because the taxman is always watching."
    if "set invoice number" in lowered:
        return "Set that invoice number to INV-2026-001. The first invoice is always the sweetest."
    if "add line item 1" in lowered:
        return "Now for the fun part. Line item one: Web Development Services. Forty units at twenty-five hundred a pop. Don't forget the 9 percent GST."
    if "add line item 2" in lowered:
        return "Line item two: UI/UX Design, twenty units at three thousand."
    if "add line item 3" in lowered:
        return "One more for the road! Line item three: Annual Server Hosting. Eighteen thousand flat."
    if "add payment notes and terms" in lowered:
        return "Almost home. Drop your payment terms in the notes: payment due within 30 days. Add your bank details so the money actually finds its way to you."
    if "review subtotal" in lowered or "gst breakdown" in lowered:
        return "Final sanity check. Subtotal, GST, grand total looking absolutely crispy."
    if "download/print" in lowered or "export the invoice as pdf" in lowered:
        return "Hit that Download button, grab your PDF, and boom!"
    return None


def zoho_waiting_aside(description: str) -> str | None:
    """Return pause-covering lines for the longer Zoho form steps."""
    lowered = normalize_text(description).lower()

    if "enter business details" in lowered:
        return "And now we take a deep breath. The internet is doing its magic. Hydrate. Stare intensely at the screen... and we're good!"
    if "add line item 2" in lowered:
        return "Now we let Zoho do the heavy lifting. We are not here for mental math."
    if "add line item 3" in lowered:
        return "Quick pause while the totals update. Like a slot machine spin, except you actually win every time."
    return None


def zoho_fallback_waiting_aside(description: str) -> str | None:
    """Return shorter fallback pause lines for Zoho timing gaps."""
    lowered = normalize_text(description).lower()

    if "enter business details" in lowered:
        return "One moment while the form catches up."
    if "add line item 2" in lowered:
        return "Zoho is handling the math for us."
    if "add line item 3" in lowered:
        return "Quick pause while the totals refresh."
    return None


def mondula_fallback_line(description: str, step_num: int, total_steps: int) -> str | None:
    """Return concise fallback lines for the Mondula form demo."""
    lowered = normalize_text(description).lower()

    if "review summary" in lowered or "submit-ready final state" in lowered:
        return "Summary looks clean and submit-ready."
    if "open the mondula multi-step form demo page" in lowered:
        return "Opening the Mondula demo page."
    if "move from the intro page" in lowered:
        return "Accept the intro and move to the first real step."
    if "fill first page text and textarea fields" in lowered:
        return "Fill the first text fields and the textarea."
    if "go to the next page with additional input fields" in lowered:
        return "Move to page two and wait for the next section."
    if "fill text, custom textarea, and date fields on page two" in lowered:
        return "Fill page two and choose the date."
    if "proceed to radio, checkbox, and dropdown inputs" in lowered:
        return "Next page. Radio, checkboxes, and dropdowns are loading."
    if "select a radio option, multiple checkboxes, and a dropdown value" in lowered:
        return "Pick the radio, checkboxes, and dropdown."
    if "open the conditional input section" in lowered:
        return "Open the conditional section."
    if "fill conditional fields based on the selected dish" in lowered:
        return "Fill the pizza options."
    if "move to the final contact-details page" in lowered:
        return "One last wait before the contact page."
    if "fill final contact page with six required input fields" in lowered:
        return "Fill the final contact details."

    if step_num == total_steps:
        return "Summary looks clean and submit-ready."
    return None


def mondula_story_line(description: str) -> str | None:
    """Return high-energy narration lines for the Mondula form flow."""
    lowered = normalize_text(description).lower()

    if "review summary" in lowered or "submit-ready final state" in lowered:
        return "Grand finale. Review the summary. Everything looks perfect. We came, we automated. Mondula zero, Pavan one."
    if "open the mondula multi-step form demo page" in lowered:
        return "Ladies and gentlemen, fasten your seatbelts. We are about to make a web form feel exciting. Mondula is sleek, green, and suspiciously clean."
    if "move from the intro page" in lowered:
        return "Accept those cookies, om nom nom, and blow past the intro. Hit Next Step and let's get to work."
    if "fill first page text and textarea fields" in lowered:
        return "Section one. Watch the fingers fly. Pavan Demo goes in, and the textarea becomes a tiny manifesto for automation."
    if "go to the next page with additional input fields" in lowered:
        return "Page two, and now we wait. Quick breather. Why do we mash dead remote batteries harder? Nobody knows."
    if "fill text, custom textarea, and date fields on page two" in lowered:
        return "Boom, we're back. Automation field, check. Second value, check. March thirteenth on the calendar. A fine day for destiny."
    if "proceed to radio, checkbox, and dropdown inputs" in lowered:
        return "Next step, please. Loading takes its sweet time, like a cat deciding whether it actually wants to go outside."
    if "select a radio option, multiple checkboxes, and a dropdown value" in lowered:
        return "And we're live. Radio buttons, checkboxes, dropdowns. A digital buffet, and we're sampling like professionals."
    if "open the conditional input section" in lowered:
        return "Now the conditional section opens, and the plot thickens. We choose pizza, because we are not monsters."
    if "fill conditional fields based on the selected dish" in lowered:
        return "Thin crust, obviously. Olives and corn, bold choice. Pesto Rosso sauce, because we're fancy today."
    if "move to the final contact-details page" in lowered:
        return "One last wait. If you're still here, you're a champion. Data immortality is seconds away."
    if "fill final contact page with six required input fields" in lowered:
        return "Final lap. Pavan Kumar goes in, birthday locked, phone, email, and production details all lined up. Big leagues only."
    return None


def indian_visa_fallback_line(description: str, step_num: int, total_steps: int) -> str | None:
    """Return concise fallback lines for the Indian eVisa demo."""
    lowered = normalize_text(description).lower()

    if "open the indian evisa portal home page" in lowered:
        return "Open the Indian eVisa portal."
    if "open the evisa application form start page" in lowered:
        return "Open the application form."
    if "select nationality and passport type" in lowered:
        return "Choose nationality and passport type."
    if "choose the port of arrival" in lowered:
        return "Choose the port of arrival and wait for the portal."
    if "fill date of birth and email confirmation" in lowered:
        return "Fill the birth date and email."
    if "choose visa service" in lowered:
        return "Choose the 30 day tourist visa."
    if "set expected date of arrival and acknowledge instructions" in lowered:
        return "Set the arrival date and acknowledge the instructions."
    if "stop at captcha step" in lowered or "captcha step" in lowered:
        return "Stop safely at the captcha step."

    if step_num == total_steps:
        return "Stop safely at the captcha step."
    return None


def indian_visa_story_line(description: str) -> str | None:
    """Return a punchier story line for the Indian eVisa flow."""
    lowered = normalize_text(description).lower()

    if "open the indian evisa portal home page" in lowered:
        return "Welcome, traveler. Open the Indian eVisa portal. All those colors feel like a bureaucratic rangoli. The quest begins now."
    if "open the evisa application form start page" in lowered:
        return "Hit Apply like it's a win-a-million-dollars link. Boom, the form appears, blue, white, and ready for your life story."
    if "select nationality and passport type" in lowered:
        return "Tell them who you are. United States. Ordinary Passport. Diplomatic passport holders can skip this tutorial."
    if "choose the port of arrival" in lowered:
        return "Choose your Port of Arrival. Today we're catching sea breeze at Agatti Seaport. Fancy. And now the portal enters its meditation break."
    if "fill date of birth and email confirmation" in lowered:
        return "We're back. Add the birth date and your email. Use one you actually check, not batman123 at gmail."
    if "choose visa service" in lowered:
        return "Choose the service: 30-Day e-Tourist Visa. The taster menu of visas. Tourism, recreation, all the hits."
    if "set expected date of arrival and acknowledge instructions" in lowered:
        return "Set the arrival date and tick the instructions box. We are almost at the good part."
    if "stop at captcha step" in lowered or "captcha step" in lowered:
        return "Final boss: captcha. We stop here for safety, but India is right around the corner."
    return None


def indian_visa_waiting_aside(description: str, variant: int = 1) -> str | None:
    """Return custom long-wait lines for the Indian eVisa portal."""
    lowered = normalize_text(description).lower()
    if "port of arrival" not in lowered:
        return None

    if variant == 1:
        return "And now we wait. This blank screen is digital dharma. Check your sunscreen, respect the spice, maybe hydrate. Government loading bars move only after enlightenment."
    if variant == 2:
        return "Still nothing? Not a glitch. A spiritual test. Namaste, loading screen, please have mercy on us. Stay with me."
    return None


def indian_visa_fallback_waiting_aside(description: str, variant: int = 1) -> str | None:
    """Return shorter fallback wait lines for the Indian eVisa portal."""
    lowered = normalize_text(description).lower()
    if "port of arrival" not in lowered:
        return None

    if variant == 1:
        return "The portal is taking a meditation break."
    if variant == 2:
        return "Still waiting, stay with me."
    return None


def ebay_fallback_line(description: str, step_num: int, total_steps: int) -> str | None:
    """Return concise fallback lines for the eBay Advanced Search demo."""
    lowered = normalize_text(description).lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "That wraps the eBay gear grab."
    if "open ebay advanced search" in lowered:
        return "Open eBay Advanced Search."
    if "enter main search keywords" in lowered:
        return "Enter the Sony WH-1000XM5 keywords."
    if "change the keyword match dropdown to exact order" in lowered:
        return "Set the keyword match to exact order."
    if "enter words to exclude from results" in lowered:
        return "Exclude broken parts from the results."
    if "include title and description in the search scope" in lowered:
        return "Search title and description too."
    if "set minimum and maximum price filters" in lowered:
        return "Set the price range from 150 to 400."
    if "filter for new-condition items" in lowered:
        return "Filter for new items only."
    if "run the search and open the filtered results page" in lowered:
        return "Run the search and open the filtered results."

    if step_num == total_steps:
        return "That wraps the eBay gear grab."
    return None


def ebay_story_line(description: str) -> str | None:
    """Return a high-energy narration line for the eBay Advanced Search flow."""
    lowered = normalize_text(description).lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "Search complete. Clean results, solid filters, and zero amateur moves."
    if "open ebay advanced search" in lowered:
        return "Alright team, this is not shopping. Advanced Search is where the real hunt starts."
    if "enter main search keywords" in lowered:
        return "Target acquired: Sony WH-1000XM5. Type it clean and keep it precise."
    if "change the keyword match dropdown to exact order" in lowered:
        return "Exact words, exact order. No batteries, no posters, no nonsense."
    if "enter words to exclude from results" in lowered:
        return "Exclude broken parts. We want headphones, not a glue-gun recovery project."
    if "include title and description in the search scope" in lowered:
        return "Expand to title and description. Hidden deals love hiding in the fine print."
    if "set minimum and maximum price filters" in lowered:
        return "Price window locked: 150 to 400. Steal? Yes. Suspicious envelope listing? No."
    if "filter for new-condition items" in lowered:
        return "Filter for New. Fresh-box energy only."
    if "run the search and open the filtered results page" in lowered:
        return "Hit Search. Boom. Filtered results, pure audio gold, zero junk."
    return None


def ebay_waiting_aside(description: str) -> str | None:
    """Return custom wait-cover lines for slower eBay steps."""
    lowered = normalize_text(description).lower()

    if "open ebay advanced search" in lowered:
        return "Mainframe is loading. The amateurs already got lost at the basic search bar."
    if "run the search and open the filtered results page" in lowered:
        return "There it is. Clean results, no broken plastic, just the serious listings."
    return None


def ebay_fallback_waiting_aside(description: str) -> str | None:
    """Return shorter fallback wait lines for eBay timing gaps."""
    lowered = normalize_text(description).lower()

    if "open ebay advanced search" in lowered:
        return "Advanced Search is loading now."
    if "run the search and open the filtered results page" in lowered:
        return "Results are loading in now."
    return None


def tinkercad_fallback_line(description: str, step_num: int, total_steps: int) -> str | None:
    """Return concise learning-demo lines that fit TinkerCAD windows."""
    lowered = normalize_text(description).lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "That wraps the TinkerCAD speedrun."
    if "open tinkercad" in lowered:
        return "Open TinkerCAD and land on the design home page."
    if "learning center" in lowered:
        return "Open the Learning Center."
    if "search for beginner 3d design tutorials" in lowered:
        return "Search for 3D design basics."
    if "return to 3d design tutorials" in lowered:
        return "Return to the CAD-focused tutorials."
    if "open a tutorial card" in lowered or "select any visible tutorial card" in lowered:
        return "Open a tutorial card."
    if "scroll through the tutorial page" in lowered:
        return "Scroll through the lesson visuals."
    if "open the tinkercad gallery" in lowered:
        return "Open the gallery."
    if "search gallery designs" in lowered or "browse featured gallery designs" in lowered:
        return "Browse featured designs for inspiration."
    if "open a gallery design page" in lowered or "scroll through gallery results" in lowered:
        return "Open the featured Mushroom design."

    if step_num == total_steps:
        return "That wraps the TinkerCAD speedrun."
    return None


def tinkercad_story_line(description: str) -> str | None:
    """Return a cinematic story line for the TinkerCAD exploration flow."""
    lowered = normalize_text(description).lower()

    if "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
        return "Tutorial complete. You skipped the login, found the spark, and now Euclid expects greatness."
    if "open tinkercad" in lowered:
        return "Welcome, future architects. TinkerCAD is open, and free is still the best price in software."
    if "learning center" in lowered:
        return "Step two. Learning Center. The VIP lounge for knowledge with none of the create-an-account drama."
    if "search for beginner 3d design tutorials" in lowered:
        return "Search 3D design basics. Every keystroke is one more brick in the empire."
    if "return to 3d design tutorials" in lowered:
        return "Back to CAD-focused practice. Professional games only. Focus, precision, geometry."
    if "open a tutorial card" in lowered or "select any visible tutorial card" in lowered:
        return "Open a tutorial card. Treasure chest vibes, except the prize is Z-axis wisdom."
    if "scroll through the tutorial page" in lowered:
        return "Scroll through the visuals. Space stations, moon talk, enough inspiration to make NASA curious."
    if "open the tinkercad gallery" in lowered:
        return "Gallery time. Nine million designs, all born while somebody was supposed to be doing taxes."
    if "search gallery designs" in lowered or "browse featured gallery designs" in lowered:
        return "Browse the hits. Mushroom, Retro Diner, drawer caddy. Practicality and chaos in perfect harmony."
    if "open a gallery design page" in lowered or "scroll through gallery results" in lowered:
        return "Open Mushroom by Demirarh. Purple, spotted, Staff Picked. Honestly, life goals."
    return None


def tinkercad_waiting_aside(description: str) -> str | None:
    """Return custom wait-cover lines for the longer TinkerCAD steps."""
    lowered = normalize_text(description).lower()

    if "open tinkercad" in lowered:
        return "Look at that plane. My what-if is a rocket in pajamas. Tiny render break, then we're back."
    if "learning center" in lowered:
        return "The lesson grid is loading. Like a souffle, you do not rush the pixels."
    if "search for beginner 3d design tutorials" in lowered:
        return "TinkerCAD is thinking. Castle, donut, ego monument, whatever you build, creativity gets a second."
    if "open the tinkercad gallery" in lowered:
        return "Short render break. Mushroom or car? The suspense is crushing my ergonomic chair."
    if "search gallery designs" in lowered or "browse featured gallery designs" in lowered:
        return "Almost there. I can feel my brain getting more creative by the second."
    return None


def tinkercad_fallback_waiting_aside(description: str) -> str | None:
    """Return shorter fallback wait lines for TinkerCAD timing gaps."""
    lowered = normalize_text(description).lower()

    if "open tinkercad" in lowered:
        return "The home page is rendering now."
    if "learning center" in lowered:
        return "The lesson grid is loading."
    if "search for beginner 3d design tutorials" in lowered:
        return "Search results are loading now."
    if "open the tinkercad gallery" in lowered:
        return "The gallery page is rendering."
    if "search gallery designs" in lowered or "browse featured gallery designs" in lowered:
        return "Featured designs are still loading."
    return None


def narration_offset_sec(beat: dict) -> float:
    """Place narration slightly inside the step so the screen establishes first."""
    start_sec = float(beat.get("start_elapsed_sec", 0.0) or 0.0)
    duration_sec = max(float(beat.get("duration_sec", 0.0) or 0.0), 0.1)
    description = beat.get("description", "")
    url = beat.get("url", "")

    if is_overpass_step(description, url):
        offset = 0.62 if duration_sec < 6.5 else 0.82
    elif is_screener_step(description, url):
        offset = 0.5 if duration_sec < 6.0 else 0.62
    elif is_zoho_invoice_step(description, url):
        offset = 0.54 if duration_sec < 6.5 else 0.68
    elif is_mondula_step(description, url):
        offset = 0.54 if duration_sec < 6.8 else 0.7
    elif is_tinkercad_step(description, url):
        offset = 0.5 if duration_sec < 6.0 else 0.64
    elif is_ebay_step(description, url):
        offset = 0.5 if duration_sec < 6.2 else 0.66
    else:
        offset = 0.32
    return round(start_sec + offset, 3)


def narration_primary_budget_sec(beat: dict) -> float:
    """Reserve a smaller primary window on long Overpass steps so filler can land later."""
    duration_sec = max(float(beat.get("duration_sec", 0.0) or 0.0), 0.1)
    description = beat.get("description", "")
    url = beat.get("url", "")

    if is_overpass_step(description, url):
        if overpass_waiting_aside(description):
            return round(max(min(duration_sec * 0.48, duration_sec - 3.05), 3.15), 3)
        return round(max(min(duration_sec * 0.9, duration_sec - 0.85), 3.05), 3)
    if is_screener_step(description, url):
        if duration_sec >= SCREENER_FILLER_THRESHOLD_SEC:
            return round(max(min(duration_sec * 0.62, duration_sec - 2.35), 3.1), 3)
        return round(max(duration_sec * 0.78, 2.85), 3)
    if is_zoho_invoice_step(description, url):
        if zoho_waiting_aside(description):
            return round(max(min(duration_sec * 0.58, duration_sec - 2.9), 3.2), 3)
        return round(max(min(duration_sec * 0.9, duration_sec - 0.85), 3.1), 3)
    if is_mondula_step(description, url):
        return round(max(min(duration_sec * 0.9, duration_sec - 0.8), 3.2), 3)
    if is_tinkercad_step(description, url):
        if duration_sec >= TINKERCAD_FILLER_THRESHOLD_SEC:
            return round(max(min(duration_sec * 0.6, duration_sec - 2.6), 3.05), 3)
        return round(max(duration_sec * 0.76, 2.85), 3)
    if is_ebay_step(description, url):
        if ebay_waiting_aside(description):
            return round(max(min(duration_sec * 0.56, duration_sec - 2.7), 3.05), 3)
        return round(max(min(duration_sec * 0.88, duration_sec - 0.75), 2.95), 3)
    return round(max(duration_sec * (0.78 if duration_sec >= 7.0 else 0.93), 2.75), 3)


def should_add_waiting_aside(beat: dict) -> bool:
    """Decide whether a step deserves a second spoken beat during visible waiting."""
    duration_sec = max(float(beat.get("duration_sec", 0.0) or 0.0), 0.1)
    description = beat.get("description", "")
    url = beat.get("url", "")
    if is_overpass_step(description, url):
        return duration_sec >= OVERPASS_FILLER_THRESHOLD_SEC and overpass_waiting_aside(description) is not None
    elif is_screener_step(description, url):
        threshold = SCREENER_FILLER_THRESHOLD_SEC
    elif is_zoho_invoice_step(description, url):
        return duration_sec >= ZOHO_FILLER_THRESHOLD_SEC and zoho_waiting_aside(description) is not None
    elif is_mondula_step(description, url):
        return False
    elif is_tinkercad_step(description, url):
        threshold = TINKERCAD_FILLER_THRESHOLD_SEC
    elif is_indian_visa_step(description, url):
        lowered = description.lower()
        if "port of arrival" not in lowered:
            return False
        threshold = max(INDIAN_VISA_FILLER_THRESHOLD_SEC, 12.0)
    elif is_ebay_step(description, url):
        return duration_sec >= EBAY_FILLER_THRESHOLD_SEC and ebay_waiting_aside(description) is not None
    else:
        threshold = LONG_STEP_FILLER_THRESHOLD_SEC
    return duration_sec >= threshold and "tutorial complete" not in description.lower()


def filler_offset_and_budget(beat: dict, start_sec: float, end_sec: float, duration_sec: float) -> tuple[float, float]:
    """Choose a filler placement that lands in the back half of a long step."""
    description = beat.get("description", "")
    url = beat.get("url", "")

    if is_overpass_step(description, url):
        filler_offset = start_sec + max(duration_sec * 0.58, 4.35)
        filler_budget = max(end_sec - filler_offset - 0.55, 2.2)
        return round(filler_offset, 3), round(filler_budget, 3)
    if is_screener_step(description, url):
        filler_offset = start_sec + max(duration_sec * 0.63, 3.95)
        filler_budget = max(end_sec - filler_offset - 0.45, 2.0)
        return round(filler_offset, 3), round(filler_budget, 3)
    if is_zoho_invoice_step(description, url):
        filler_offset = start_sec + max(duration_sec * 0.54, 4.0)
        filler_budget = max(end_sec - filler_offset - 0.35, 2.6)
        return round(filler_offset, 3), round(filler_budget, 3)
    if is_tinkercad_step(description, url):
        filler_offset = start_sec + max(duration_sec * 0.63, 4.0)
        filler_budget = max(end_sec - filler_offset - 0.45, 2.0)
        return round(filler_offset, 3), round(filler_budget, 3)
    if is_indian_visa_step(description, url):
        filler_offset = start_sec + max(duration_sec * 0.38, 5.0)
        filler_budget = max(end_sec - filler_offset - 0.55, 2.2)
        return round(filler_offset, 3), round(filler_budget, 3)
    if is_ebay_step(description, url):
        filler_offset = start_sec + max(duration_sec * 0.58, 4.1)
        filler_budget = max(end_sec - filler_offset - 0.4, 2.0)
        return round(filler_offset, 3), round(filler_budget, 3)

    filler_offset = start_sec + max(duration_sec * 0.74, 4.0)
    filler_budget = max(end_sec - filler_offset - 0.45, 1.9)
    return round(filler_offset, 3), round(filler_budget, 3)


def extra_waiting_segments(beat: dict, step_num: int, start_sec: float, end_sec: float, duration_sec: float) -> list[dict]:
    """Return extra filler beats for unusually slow steps that need more than one cover line."""
    description = beat.get("description", "")
    url = beat.get("url", "")
    if not is_indian_visa_step(description, url) or duration_sec < 18.0:
        return []

    second_offset = start_sec + max(duration_sec * 0.74, 18.0)
    second_budget = max(end_sec - second_offset - 0.45, 2.0)
    if second_budget < 2.0:
        return []

    custom_text = indian_visa_waiting_aside(description, variant=2)
    fallback_text = indian_visa_fallback_waiting_aside(description, variant=2) or pick_variant(
        INDIAN_VISA_FALLBACK_WAITING_ASIDES,
        step_num + 1,
    )
    return [
        {
            "segment_id": f"step_{step_num:02d}_wait_02",
            "step": step_num,
            "type": "filler",
            "offset_sec": round(second_offset, 3),
            "budget_sec": round(second_budget, 3),
            "text": custom_text or pick_variant(INDIAN_VISA_WAITING_ASIDES, step_num + 1),
            "fallback_text": fallback_text,
            "subtitle": fallback_text,
            "target_window_end_sec": round(end_sec, 3),
        }
    ]


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
    if is_overpass_step(description, url):
        overpass_line = overpass_fallback_line(description, step_num, total_steps)
        if overpass_line:
            return overpass_line
    if is_screener_step(description, url):
        screener_line = screener_fallback_line(description, step_num, total_steps)
        if screener_line:
            return screener_line
    if is_zoho_invoice_step(description, url):
        zoho_line = zoho_fallback_line(description, step_num, total_steps)
        if zoho_line:
            return zoho_line
    if is_mondula_step(description, url):
        mondula_line = mondula_fallback_line(description, step_num, total_steps)
        if mondula_line:
            return mondula_line
    if is_indian_visa_step(description, url):
        indian_visa_line = indian_visa_fallback_line(description, step_num, total_steps)
        if indian_visa_line:
            return indian_visa_line
    if is_ebay_step(description, url):
        ebay_line = ebay_fallback_line(description, step_num, total_steps)
        if ebay_line:
            return ebay_line
    if is_tinkercad_step(description, url):
        tinkercad_line = tinkercad_fallback_line(description, step_num, total_steps)
        if tinkercad_line:
            return tinkercad_line

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
    overpass_primary = overpass_story_line(description) if is_overpass_step(description, url) else None
    screener_primary = screener_story_line(description) if is_screener_step(description, url) else None
    zoho_primary = zoho_story_line(description) if is_zoho_invoice_step(description, url) else None
    mondula_primary = mondula_story_line(description) if is_mondula_step(description, url) else None
    indian_visa_primary = indian_visa_story_line(description) if is_indian_visa_step(description, url) else None
    ebay_primary = ebay_story_line(description) if is_ebay_step(description, url) else None
    tinkercad_primary = tinkercad_story_line(description) if is_tinkercad_step(description, url) else None
    commentary = narration_commentary(description, step_num, url)
    if len(spoken_action.split()) >= 6 and measured_duration_sec < 7.0:
        commentary = ""

    def join_lines(base: str, tail: str = "") -> str:
        if tail:
            return f"{base} {tail}".strip()
        return base.strip()

    if overpass_primary:
        narration = overpass_primary
    elif screener_primary:
        narration = screener_primary
    elif zoho_primary:
        narration = zoho_primary
    elif mondula_primary:
        narration = mondula_primary
    elif indian_visa_primary:
        narration = indian_visa_primary
    elif ebay_primary:
        narration = ebay_primary
    elif tinkercad_primary:
        narration = tinkercad_primary
    elif "tutorial complete" in lowered or lowered.startswith("tutorial complete"):
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
        offset_sec = narration_offset_sec(beat)
        primary_budget = narration_primary_budget_sec(beat)
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

        if not should_add_waiting_aside(beat):
            continue

        filler_offset, filler_budget = filler_offset_and_budget(beat, start_sec, end_sec, duration_sec)
        minimum_budget = 2.2 if is_overpass_step(beat.get("description", ""), beat.get("url", "")) else 1.9
        if filler_budget < minimum_budget:
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

        timeline.extend(extra_waiting_segments(beat, step_num, start_sec, end_sec, duration_sec))

    timeline.sort(key=lambda item: (item["offset_sec"], item["segment_id"]))
    return timeline


def demo_name_from_steps_path(steps_json_path: str) -> str:
    """Infer the demo name from a steps JSON path."""
    file_name = os.path.basename(steps_json_path)
    if file_name.endswith("_steps.json"):
        return file_name[:-11]
    return os.path.splitext(file_name)[0]


def build_custom_screener_timeline(steps: list[dict]) -> list[dict] | None:
    """Use the user-approved screener narration script across grouped step windows."""
    expected_steps = max((int(segment.get("end_step", 0) or 0) for segment in CUSTOM_SCREENER_TIMELINE_SEGMENTS), default=0)
    if len(steps) < expected_steps:
        return None

    timeline = []
    for index, segment in enumerate(CUSTOM_SCREENER_TIMELINE_SEGMENTS, start=1):
        start_step = segment["start_step"]
        end_step = segment["end_step"]
        if start_step < 1 or end_step > len(steps) or start_step > end_step:
            return None

        start_step_payload = steps[start_step - 1]
        end_step_payload = steps[end_step - 1]
        measured_start_sec = step_start_sec(start_step_payload, 0.0)
        measured_end_sec = step_end_sec(end_step_payload, measured_start_sec)
        offset_sec = round(float(segment["target_start_sec"]), 3)
        target_window_end_sec = round(float(segment["target_end_sec"]), 3)
        budget_sec = round(max(target_window_end_sec - offset_sec, 2.8), 3)

        timeline.append(
            {
                "segment_id": f"screener_story_{index:02d}",
                "step": start_step,
                "type": "primary",
                "offset_sec": offset_sec,
                "budget_sec": budget_sec,
                "text": segment["text"],
                "fallback_text": segment.get("fallback_text") or segment["text"],
                "subtitle": segment.get("subtitle") or segment["text"],
                "target_window_end_sec": target_window_end_sec,
                "source_start_step": start_step,
                "source_end_step": end_step,
                "source_start_sec": round(measured_start_sec, 3),
                "source_end_sec": round(measured_end_sec, 3),
            }
        )

    return timeline


def build_custom_zoho_timeline(steps: list[dict]) -> list[dict] | None:
    """Use the user-approved Zoho narration script across grouped step windows."""
    expected_steps = max((int(segment.get("end_step", 0) or 0) for segment in CUSTOM_ZOHO_TIMELINE_SEGMENTS), default=0)
    if len(steps) < expected_steps:
        return None

    timeline = []
    for index, segment in enumerate(CUSTOM_ZOHO_TIMELINE_SEGMENTS, start=1):
        start_step = segment["start_step"]
        end_step = segment["end_step"]
        if start_step < 1 or end_step > len(steps) or start_step > end_step:
            return None

        start_step_payload = steps[start_step - 1]
        end_step_payload = steps[end_step - 1]
        measured_start_sec = step_start_sec(start_step_payload, 0.0)
        measured_end_sec = step_end_sec(end_step_payload, measured_start_sec)
        offset_sec = round(float(segment["target_start_sec"]), 3)
        target_window_end_sec = round(float(segment["target_end_sec"]), 3)
        budget_sec = round(max(target_window_end_sec - offset_sec, 2.8), 3)

        timeline.append(
            {
                "segment_id": f"zoho_story_{index:02d}",
                "step": start_step,
                "type": "primary",
                "offset_sec": offset_sec,
                "budget_sec": budget_sec,
                "text": segment["text"],
                "fallback_text": segment.get("fallback_text") or segment["text"],
                "subtitle": segment.get("subtitle") or segment["text"],
                "target_window_end_sec": target_window_end_sec,
                "disable_compact": True,
                "source_start_step": start_step,
                "source_end_step": end_step,
                "source_start_sec": round(measured_start_sec, 3),
                "source_end_sec": round(measured_end_sec, 3),
            }
        )

    return timeline


def build_custom_tinkercad_timeline(steps: list[dict]) -> list[dict] | None:
    """Use a grouped story-first script for the Tinkercad speedrun."""
    expected_steps = max((int(segment.get("end_step", 0) or 0) for segment in CUSTOM_TINKERCAD_TIMELINE_SEGMENTS), default=0)
    if len(steps) < expected_steps:
        return None

    timeline = []
    for index, segment in enumerate(CUSTOM_TINKERCAD_TIMELINE_SEGMENTS, start=1):
        start_step = segment["start_step"]
        end_step = segment["end_step"]
        if start_step < 1 or end_step > len(steps) or start_step > end_step:
            return None

        start_step_payload = steps[start_step - 1]
        end_step_payload = steps[end_step - 1]
        measured_start_sec = step_start_sec(start_step_payload, 0.0)
        measured_end_sec = step_end_sec(end_step_payload, measured_start_sec)
        offset_sec = round(measured_start_sec, 3)
        target_window_end_sec = round(measured_end_sec, 3)
        budget_sec = round(max(target_window_end_sec - offset_sec, 2.8), 3)

        timeline.append(
            {
                "segment_id": f"tinkercad_story_{index:02d}",
                "step": start_step,
                "type": "primary",
                "offset_sec": offset_sec,
                "budget_sec": budget_sec,
                "text": segment["text"],
                "fallback_text": segment.get("fallback_text") or segment["text"],
                "subtitle": segment.get("subtitle") or segment["text"],
                "target_window_end_sec": target_window_end_sec,
                "source_start_step": start_step,
                "source_end_step": end_step,
                "source_start_sec": round(measured_start_sec, 3),
                "source_end_sec": round(measured_end_sec, 3),
            }
        )

    return timeline


def custom_narration_timeline(demo_name: str, steps: list[dict]) -> list[dict] | None:
    """Return a demo-specific narration timeline override when one is defined."""
    if demo_name == "screener":
        return build_custom_screener_timeline(steps)
    if demo_name == "zoho_invoice":
        return build_custom_zoho_timeline(steps)
    if demo_name == "tinkercad":
        return build_custom_tinkercad_timeline(steps)
    return None


def generate_narration_package(steps_json_path: str) -> dict:
    """Build structured narration beats plus the final script text."""
    with open(steps_json_path, encoding="utf-8") as file:
        steps = json.load(file)

    total_steps = len(steps)
    demo_name = demo_name_from_steps_path(steps_json_path)
    beats = [build_story_beat(step, total_steps) for step in steps]
    custom_timeline = custom_narration_timeline(demo_name, steps)
    timeline = custom_timeline or build_narration_timeline(beats)
    script = "\n\n".join(segment["text"] for segment in timeline)
    if custom_timeline:
        total_duration = max((float(segment.get("target_window_end_sec", 0.0) or 0.0) for segment in timeline), default=0.0)
    else:
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


def generate_audio_elevenlabs_sdk(text: str, output_prefix: str, api_key: str | None = None):
    """Generate narration with the ElevenLabs SDK when it is installed."""
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        return None

    api_key = api_key or elevenlabs_api_key_from_env()
    if not api_key:
        return None

    voice_id = elevenlabs_voice_id_from_env()
    model_id = elevenlabs_model_id_from_env()
    output_format = elevenlabs_output_format_from_env()
    client = ElevenLabs(api_key=api_key)

    try:
        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
        )
        audio_bytes = bytearray()
        if isinstance(audio_stream, (bytes, bytearray)):
            audio_bytes.extend(audio_stream)
        else:
            for chunk in audio_stream:
                if chunk:
                    audio_bytes.extend(chunk)

        if not audio_bytes:
            print("  WARNING: ElevenLabs returned no audio payload.")
            return None

        output_path = f"{output_prefix}{extension_for_output_format(output_format)}"
        with open(output_path, "wb") as audio_file:
            audio_file.write(bytes(audio_bytes))
        print(f"  Audio narration saved: {output_path}")
        return output_path
    except Exception as error:
        global ELEVENLABS_VOICE_UNAVAILABLE
        if is_elevenlabs_voice_unavailable(str(error)):
            ELEVENLABS_VOICE_UNAVAILABLE = True
            print("  WARNING: ElevenLabs rejected this voice on the current plan, switching remaining segments to fallback audio.")
            return None
        print(f"  WARNING: ElevenLabs SDK generation failed: {error}")
        return None


def generate_audio_elevenlabs_http(text: str, output_prefix: str, api_key: str | None = None):
    """Generate narration directly against the ElevenLabs HTTP API."""
    api_key = api_key or elevenlabs_api_key_from_env()
    if not api_key:
        return None

    voice_id = elevenlabs_voice_id_from_env()
    model_id = elevenlabs_model_id_from_env()
    output_format = elevenlabs_output_format_from_env()
    output_path = f"{output_prefix}{extension_for_output_format(output_format)}"
    endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": model_id,
        "output_format": output_format,
    }

    for attempt in range(3):
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                audio_bytes = response.read()

            if not audio_bytes:
                print("  WARNING: ElevenLabs returned no audio payload.")
                return None

            with open(output_path, "wb") as audio_file:
                audio_file.write(audio_bytes)
            print(f"  Audio narration saved: {output_path}")
            return output_path
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="ignore")
            global ELEVENLABS_VOICE_UNAVAILABLE
            if is_elevenlabs_voice_unavailable(body):
                ELEVENLABS_VOICE_UNAVAILABLE = True
                print("  WARNING: ElevenLabs rejected this voice on the current plan, switching remaining segments to fallback audio.")
                return None
            is_retryable = error.code in {408, 409, 425, 429, 500, 502, 503, 504}
            if is_retryable and attempt < 2:
                delay_seconds = 4.0 + (attempt * 2.0)
                print(f"  WARNING: ElevenLabs rate-limited or unavailable. Retrying in {delay_seconds:.1f}s...")
                time.sleep(delay_seconds)
                continue

            print(f"  WARNING: ElevenLabs HTTP generation failed ({error.code}): {body or error.reason}")
            return None
        except Exception as error:
            if attempt < 2:
                delay_seconds = 4.0 + (attempt * 2.0)
                print(f"  WARNING: ElevenLabs request failed. Retrying in {delay_seconds:.1f}s...")
                time.sleep(delay_seconds)
                continue

            print(f"  WARNING: ElevenLabs HTTP generation failed: {error}")
            return None

    return None


def generate_audio_elevenlabs(text: str, output_prefix: str, api_key: str | None = None):
    """Generate narration using ElevenLabs, preferring the SDK when available."""
    global ELEVENLABS_VOICE_UNAVAILABLE
    if ELEVENLABS_VOICE_UNAVAILABLE:
        return None

    api_key = api_key or elevenlabs_api_key_from_env()
    if not api_key:
        print("ERROR: No ElevenLabs API key found.")
        print("Set it in the project .env file as ELEVENLABS_API_KEY=your_key_here")
        return None

    sdk_output = generate_audio_elevenlabs_sdk(text, output_prefix, api_key=api_key)
    if sdk_output:
        return sdk_output
    return generate_audio_elevenlabs_http(text, output_prefix, api_key=api_key)


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


def generate_audio_with_fallbacks(text: str, fallback_text: str, output_prefix: str):
    """Try configured narration providers in order until one succeeds."""
    providers = narration_provider_order()
    primary_text = sanitize_tts_text(text) or text
    fallback_spoken_text = sanitize_tts_text(fallback_text) or fallback_text or primary_text

    for provider in providers:
        if provider == "elevenlabs":
            if not elevenlabs_api_key_from_env():
                continue
            audio_path = generate_audio_elevenlabs(primary_text, output_prefix)
        elif provider == "gemini":
            if not os.environ.get("GEMINI_API_KEY"):
                continue
            audio_path = generate_audio_gemini(primary_text, output_prefix)
        elif provider == "gtts":
            audio_path = generate_audio_gtts_fallback(fallback_spoken_text, output_prefix)
        else:
            continue

        if audio_path:
            return audio_path, provider

    return None, ""


def segment_compact_voice_text(segment: dict) -> str:
    """Build a shorter rescue line when a segment cannot fit at a balanced pace."""
    if segment.get("disable_compact"):
        return ""
    fallback_text = normalize_text(segment.get("fallback_text") or "")
    if not fallback_text:
        return ""
    max_words = 4 if segment.get("type") == "filler" else 6
    compact = trim_words(fallback_text, max_words)
    return compact if compact and compact != fallback_text else fallback_text


def synthesize_segment_variant(text: str, output_prefix: str, budget_sec: float):
    """Generate one narration variant and normalize it into a timing-aware WAV clip."""
    raw_path, provider_name = generate_audio_with_fallbacks(text, text, output_prefix)
    if not raw_path:
        return None

    normalized_path = f"{output_prefix}_normalized.wav"
    normalized = normalize_audio_to_wav(raw_path, normalized_path)
    if not normalized:
        return None

    paced_path = f"{output_prefix}_paced.wav"
    paced, paced_duration = apply_audio_pace(normalized, BALANCED_AUDIO_PACE, paced_path)

    fitted_path = f"{output_prefix}_fitted.wav"
    fitted, fitted_duration = fit_audio_clip_to_duration(
        paced,
        budget_sec,
        fitted_path,
        max_speedup=BALANCED_MAX_AUDIO_SPEEDUP,
    )
    return {
        "clip_path": fitted,
        "provider_name": provider_name,
        "paced_duration_sec": round(paced_duration, 3),
        "clip_duration_sec": round(fitted_duration, 3),
        "required_speedup": round((paced_duration / budget_sec), 3) if budget_sec > 0 else 1.0,
    }


def segment_is_balanced(rendered: dict, budget_sec: float) -> bool:
    """Check whether a rendered clip stays near the target without sounding rushed."""
    if not rendered:
        return False
    if budget_sec <= 0:
        return True
    overflow_sec = max(float(rendered.get("clip_duration_sec", 0.0) or 0.0) - budget_sec, 0.0)
    required_speedup = float(rendered.get("required_speedup", 1.0) or 1.0)
    return overflow_sec <= AUDIO_FIT_TOLERANCE_SEC and required_speedup <= BALANCED_PREFERRED_SPEEDUP


def synthesize_segment_audio(segment: dict, temp_dir: str):
    """Generate one narration clip while keeping speech pace balanced from segment to segment."""
    base_prefix = os.path.join(temp_dir, segment["segment_id"])
    budget_sec = float(segment.get("budget_sec", 0.0) or 0.0)
    primary_text = segment["text"]
    fallback_text = segment.get("fallback_text") or primary_text
    compact_text = segment_compact_voice_text(segment)

    candidates = [("primary", primary_text)]
    if fallback_text and fallback_text != primary_text:
        candidates.append(("fallback", fallback_text))
    if compact_text and compact_text not in {primary_text, fallback_text}:
        candidates.append(("compact", compact_text))

    best_rendered = None
    best_score = None
    chosen_text = primary_text

    for variant_name, candidate_text in candidates:
        rendered = synthesize_segment_variant(
            candidate_text,
            f"{base_prefix}_{variant_name}",
            budget_sec,
        )
        if not rendered:
            continue

        overflow_sec = max(float(rendered["clip_duration_sec"]) - budget_sec, 0.0) if budget_sec > 0 else 0.0
        score = (
            0 if overflow_sec <= AUDIO_FIT_TOLERANCE_SEC else 1,
            max(float(rendered["required_speedup"]) - BALANCED_PREFERRED_SPEEDUP, 0.0),
            overflow_sec,
            len(candidate_text.split()),
        )
        if best_score is None or score < best_score:
            best_rendered = rendered
            best_score = score
            chosen_text = candidate_text

        if segment_is_balanced(rendered, budget_sec):
            best_rendered = rendered
            chosen_text = candidate_text
            break

    if not best_rendered:
        return None

    if segment.get("type") == "filler":
        segment["subtitle"] = chosen_text
    segment["spoken_text"] = chosen_text
    segment["clip_duration_sec"] = round(float(best_rendered["clip_duration_sec"] or 0.0), 3)
    segment["clip_path"] = best_rendered["clip_path"]
    segment["required_speedup"] = float(best_rendered.get("required_speedup", 1.0) or 1.0)
    return best_rendered["clip_path"]


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


def final_script_from_timeline(timeline: list[dict]) -> str:
    """Render the final spoken narration script from the chosen timeline lines."""
    lines = []
    for segment in timeline:
        line = (
            (segment.get("spoken_text") or "").strip()
            or (segment.get("text") or "").strip()
            or (segment.get("subtitle") or "").strip()
        )
        if line:
            lines.append(line)
    return "\n\n".join(lines)


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
        final_script = final_script_from_timeline(timeline)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(final_script)
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
