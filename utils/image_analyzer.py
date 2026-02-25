# utils/image_analyzer.py

import google.generativeai as genai
import requests
import os
from PIL import Image
from io import BytesIO

# ── Configure Gemini ──────────────────────────────────────────────
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
gemini = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """
You are an AI analyzing a civic complaint image for a municipal system.

Respond in EXACTLY this format (no extra text):
SEVERITY: [low/medium/high/critical]
BOOST: [number 0-30]
ISSUE: [one line of what you see]

Scoring guide:
- low      → BOOST 0-5   (minor damage, cosmetic issues)
- medium   → BOOST 6-15  (potholes, blocked drains, garbage pile)
- high     → BOOST 16-22 (flooding, major damage, broken poles)
- critical → BOOST 23-30 (fire, exposed wires, collapse, gas leak)
"""

def analyze_complaint_image(image_url: str) -> dict:
    """
    Takes Cloudinary image URL, analyzes with Gemini Vision.
    Returns boost (0-30) and analysis text.
    """
    if not image_url:
        return {"boost": 0, "analysis": "No image", "severity": "none"}

    try:
        # Download image from Cloudinary
        resp  = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(resp.content))

        # Send to Gemini
        result = gemini.generate_content([PROMPT, image])
        text   = result.text.strip()

        # Parse response
        boost    = 0
        analysis = "Image analyzed"
        severity = "low"

        for line in text.split('\n'):
            line = line.strip()
            if line.startswith("BOOST:"):
                try:
                    boost = int(line.split(":")[1].strip())
                    boost = max(0, min(30, boost))
                except:
                    boost = 0
            elif line.startswith("ISSUE:"):
                analysis = line.split(":", 1)[1].strip()
            elif line.startswith("SEVERITY:"):
                severity = line.split(":", 1)[1].strip().lower()

        print(f"🖼️  Image → severity={severity}, boost=+{boost}, issue={analysis}")
        return {"boost": boost, "analysis": analysis, "severity": severity}

    except Exception as e:
        print(f"⚠️  Image analysis error: {e}")
        return {"boost": 0, "analysis": "Analysis failed", "severity": "unknown"}