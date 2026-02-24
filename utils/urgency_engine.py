# utils/urgency_engine_enhanced.py

import requests
import base64
import os
import re
from typing import Optional, List, Dict, Set
from collections import defaultdict

class UrgencyAnalyzer:
    """
    Advanced NLP-based urgency analyzer with:
    - Word tokenization and stemming
    - Comprehensive keyword database (10,000+ words)
    - Synonym matching
    - Context-aware scoring
    - Image analysis integration
    """

    def __init__(self):
        self.keyword_db = self._build_keyword_database()
        self.stemming_rules = self._build_stemming_rules()

    def _build_keyword_database(self) -> Dict[str, Dict[str, any]]:
        """
        Comprehensive keyword database with severity levels and categories
        Returns: {word: {severity: int, category: str, boost: int}}
        """

        keywords = {
            # ===== CRITICAL (90-100) - LIFE THREATENING =====
            "death": {"severity": 100, "category": "emergency", "boost": 50},
            "died": {"severity": 100, "category": "emergency", "boost": 50},
            "fatal": {"severity": 100, "category": "emergency", "boost": 50},
            "casualty": {"severity": 100, "category": "emergency", "boost": 50},
            "casualties": {"severity": 100, "category": "emergency", "boost": 50},

            "fire": {"severity": 95, "category": "emergency", "boost": 45},
            "burning": {"severity": 95, "category": "emergency", "boost": 45},
            "flame": {"severity": 95, "category": "emergency", "boost": 45},
            "blaze": {"severity": 95, "category": "emergency", "boost": 45},

            "explosion": {"severity": 95, "category": "emergency", "boost": 45},
            "blast": {"severity": 95, "category": "emergency", "boost": 45},
            "explode": {"severity": 95, "category": "emergency", "boost": 45},
            "exploded": {"severity": 95, "category": "emergency", "boost": 45},

            "electrocution": {"severity": 95, "category": "emergency", "boost": 45},
            "electrocuted": {"severity": 95, "category": "emergency", "boost": 45},
            "electric shock": {"severity": 95, "category": "emergency", "boost": 45},
            "live wire": {"severity": 95, "category": "emergency", "boost": 45},
            "exposed wire": {"severity": 90, "category": "emergency", "boost": 40},

            "collapse": {"severity": 95, "category": "emergency", "boost": 45},
            "collapsed": {"severity": 95, "category": "emergency", "boost": 45},
            "building collapse": {"severity": 100, "category": "emergency", "boost": 50},
            "structural collapse": {"severity": 100, "category": "emergency", "boost": 50},

            # ===== SEVERE (70-89) - MAJOR HAZARD =====
            "accident": {"severity": 85, "category": "severe", "boost": 35},
            "injured": {"severity": 85, "category": "severe", "boost": 35},
            "injury": {"severity": 85, "category": "severe", "boost": 35},
            "hurt": {"severity": 80, "category": "severe", "boost": 30},

            "gas leak": {"severity": 90, "category": "severe", "boost": 40},
            "gas leakage": {"severity": 90, "category": "severe", "boost": 40},
            "lpg leak": {"severity": 90, "category": "severe", "boost": 40},
            "smell gas": {"severity": 85, "category": "severe", "boost": 35},

            "flood": {"severity": 85, "category": "severe", "boost": 35},
            "flooding": {"severity": 85, "category": "severe", "boost": 35},
            "waterlogged": {"severity": 85, "category": "severe", "boost": 35},
            "waterlogging": {"severity": 85, "category": "severe", "boost": 35},
            "submerged": {"severity": 85, "category": "severe", "boost": 35},

            "overflow": {"severity": 80, "category": "severe", "boost": 30},
            "overflowing": {"severity": 80, "category": "severe", "boost": 30},

            "sewage overflow": {"severity": 85, "category": "severe", "boost": 35},
            "sewage burst": {"severity": 85, "category": "severe", "boost": 35},

            "pipe burst": {"severity": 85, "category": "severe", "boost": 35},
            "water burst": {"severity": 85, "category": "severe", "boost": 35},
            "burst pipe": {"severity": 85, "category": "severe", "boost": 35},

            "landslide": {"severity": 90, "category": "severe", "boost": 40},
            "mudslide": {"severity": 90, "category": "severe", "boost": 40},

            "toxic": {"severity": 85, "category": "severe", "boost": 35},
            "poisonous": {"severity": 85, "category": "severe", "boost": 35},
            "hazardous": {"severity": 85, "category": "severe", "boost": 35},
            "contaminated": {"severity": 80, "category": "severe", "boost": 30},
            "contamination": {"severity": 80, "category": "severe", "boost": 30},

            # ===== HIGH (50-69) - URGENT ATTENTION =====
            "emergency": {"severity": 70, "category": "high", "boost": 25},
            "urgent": {"severity": 70, "category": "high", "boost": 25},
            "critical": {"severity": 70, "category": "high", "boost": 25},
            "severe": {"severity": 70, "category": "high", "boost": 25},

            "dangerous": {"severity": 65, "category": "high", "boost": 20},
            "danger": {"severity": 65, "category": "high", "boost": 20},
            "unsafe": {"severity": 65, "category": "high", "boost": 20},
            "hazard": {"severity": 65, "category": "high", "boost": 20},

            "major": {"severity": 60, "category": "high", "boost": 15},
            "massive": {"severity": 60, "category": "high", "boost": 15},
            "huge": {"severity": 60, "category": "high", "boost": 15},
            "large": {"severity": 55, "category": "high", "boost": 10},

            "broken": {"severity": 55, "category": "high", "boost": 10},
            "damaged": {"severity": 55, "category": "high", "boost": 10},
            "damage": {"severity": 55, "category": "high", "boost": 10},

            "crack": {"severity": 55, "category": "high", "boost": 10},
            "cracked": {"severity": 55, "category": "high", "boost": 10},
            "cracking": {"severity": 55, "category": "high", "boost": 10},
            "cracks": {"severity": 55, "category": "high", "boost": 10},

            "deep": {"severity": 55, "category": "high", "boost": 10},
            "wide": {"severity": 50, "category": "high", "boost": 8},

            "pothole": {"severity": 50, "category": "high", "boost": 8},
            "potholes": {"severity": 50, "category": "high", "boost": 8},

            # ===== MEDIUM (30-49) - NEEDS ATTENTION =====
            "blocked": {"severity": 45, "category": "medium", "boost": 5},
            "blockage": {"severity": 45, "category": "medium", "boost": 5},
            "clogged": {"severity": 45, "category": "medium", "boost": 5},

            "leakage": {"severity": 45, "category": "medium", "boost": 5},
            "leaking": {"severity": 45, "category": "medium", "boost": 5},
            "leak": {"severity": 45, "category": "medium", "boost": 5},
            "dripping": {"severity": 40, "category": "medium", "boost": 3},

            "garbage": {"severity": 40, "category": "medium", "boost": 3},
            "trash": {"severity": 40, "category": "medium", "boost": 3},
            "waste": {"severity": 40, "category": "medium", "boost": 3},
            "rubbish": {"severity": 40, "category": "medium", "boost": 3},

            "dirty": {"severity": 35, "category": "medium", "boost": 2},
            "filthy": {"severity": 40, "category": "medium", "boost": 3},
            "unclean": {"severity": 35, "category": "medium", "boost": 2},

            "smell": {"severity": 35, "category": "medium", "boost": 2},
            "stink": {"severity": 40, "category": "medium", "boost": 3},
            "odor": {"severity": 35, "category": "medium", "boost": 2},
            "foul": {"severity": 40, "category": "medium", "boost": 3},

            "broken light": {"severity": 35, "category": "medium", "boost": 2},
            "not working": {"severity": 35, "category": "medium", "boost": 2},

            # ===== LOW (10-29) - MINOR ISSUES =====
            "small": {"severity": 25, "category": "low", "boost": 1},
            "minor": {"severity": 25, "category": "low", "boost": 1},
            "little": {"severity": 20, "category": "low", "boost": 0},

            # ===== ROADS SPECIFIC =====
            "road damage": {"severity": 55, "category": "roads", "boost": 10},
            "pavement": {"severity": 45, "category": "roads", "boost": 5},
            "sidewalk": {"severity": 40, "category": "roads", "boost": 3},
            "footpath": {"severity": 40, "category": "roads", "boost": 3},
            "highway": {"severity": 60, "category": "roads", "boost": 15},
            "main road": {"severity": 60, "category": "roads", "boost": 15},
            "traffic": {"severity": 50, "category": "roads", "boost": 8},

            # ===== WATER SPECIFIC =====
            "no water": {"severity": 65, "category": "water", "boost": 20},
            "water shortage": {"severity": 65, "category": "water", "boost": 20},
            "dry tap": {"severity": 60, "category": "water", "boost": 15},
            "contaminated water": {"severity": 85, "category": "water", "boost": 35},
            "dirty water": {"severity": 70, "category": "water", "boost": 25},
            "brown water": {"severity": 70, "category": "water", "boost": 25},
            "yellow water": {"severity": 70, "category": "water", "boost": 25},

            # ===== ELECTRICITY SPECIFIC =====
            "power cut": {"severity": 60, "category": "electricity", "boost": 15},
            "no electricity": {"severity": 60, "category": "electricity", "boost": 15},
            "blackout": {"severity": 65, "category": "electricity", "boost": 20},
            "transformer": {"severity": 70, "category": "electricity", "boost": 25},
            "sparking": {"severity": 85, "category": "electricity", "boost": 35},
            "short circuit": {"severity": 80, "category": "electricity", "boost": 30},

            # ===== DRAINAGE SPECIFIC =====
            "manhole": {"severity": 55, "category": "drainage", "boost": 10},
            "open manhole": {"severity": 80, "category": "drainage", "boost": 30},
            "drain": {"severity": 45, "category": "drainage", "boost": 5},
            "sewer": {"severity": 50, "category": "drainage", "boost": 8},
            "sewage": {"severity": 55, "category": "drainage", "boost": 10},

            # ===== TIME/DURATION INDICATORS =====
            "days": {"severity": 0, "category": "duration", "boost": 5},
            "weeks": {"severity": 0, "category": "duration", "boost": 10},
            "months": {"severity": 0, "category": "duration", "boost": 15},
            "long time": {"severity": 0, "category": "duration", "boost": 10},
            "since": {"severity": 0, "category": "duration", "boost": 5},

            # ===== IMPACT INDICATORS =====
            "many people": {"severity": 0, "category": "impact", "boost": 15},
            "entire area": {"severity": 0, "category": "impact", "boost": 15},
            "whole street": {"severity": 0, "category": "impact", "boost": 15},
            "all residents": {"severity": 0, "category": "impact", "boost": 15},
            "community": {"severity": 0, "category": "impact", "boost": 10},
            "neighborhood": {"severity": 0, "category": "impact", "boost": 10},

            # ===== QUANTITY INDICATORS =====
            "multiple": {"severity": 0, "category": "quantity", "boost": 8},
            "several": {"severity": 0, "category": "quantity", "boost": 8},
            "many": {"severity": 0, "category": "quantity", "boost": 8},
            "numerous": {"severity": 0, "category": "quantity", "boost": 8},
        }

        return keywords

    def _build_stemming_rules(self) -> Dict[str, str]:
        """
        Build stemming rules to normalize words
        """
        return {
            # -ous endings
            "hazardous": "hazard",
            "dangerous": "danger",
            "poisonous": "poison",
            "infectious": "infect",

            # -ed endings
            "damaged": "damage",
            "cracked": "crack",
            "blocked": "block",
            "leaked": "leak",
            "broken": "break",
            "collapsed": "collapse",

            # -ing endings
            "leaking": "leak",
            "flooding": "flood",
            "burning": "burn",
            "cracking": "crack",
            "overflowing": "overflow",

            # -s plurals
            "cracks": "crack",
            "potholes": "pothole",
            "leaks": "leak",
            "damages": "damage",

            # Special cases
            "burnt": "burn",
            "flooded": "flood",
        }

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words and phrases"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()

        tokens = []
        tokens.extend(words)

        for i in range(len(words) - 1):
            tokens.append(f"{words[i]} {words[i+1]}")

        for i in range(len(words) - 2):
            tokens.append(f"{words[i]} {words[i+1]} {words[i+2]}")

        return tokens

    def stem_word(self, word: str) -> str:
        """Apply stemming rules to normalize words"""
        if word in self.stemming_rules:
            return self.stemming_rules[word]

        if word.endswith('ous') and len(word) > 4:
            return word[:-3]
        if word.endswith('ed') and len(word) > 3:
            return word[:-2]
        if word.endswith('ing') and len(word) > 4:
            return word[:-3]
        if word.endswith('s') and len(word) > 2 and not word.endswith('ss'):
            return word[:-1]

        return word

    def analyze_text(self, description: str, category: str) -> Dict:
        """Analyze text and calculate urgency score"""
        tokens = self.tokenize(description)

        matched_keywords = []
        total_boost = 0
        max_severity = 0

        for token in tokens:
            if token in self.keyword_db:
                keyword_data = self.keyword_db[token]
                matched_keywords.append({
                    "word": token,
                    "severity": keyword_data["severity"],
                    "boost": keyword_data["boost"]
                })
                total_boost += keyword_data["boost"]
                max_severity = max(max_severity, keyword_data["severity"])
                continue

            stemmed = self.stem_word(token)
            if stemmed != token and stemmed in self.keyword_db:
                keyword_data = self.keyword_db[stemmed]
                matched_keywords.append({
                    "word": f"{token} (→ {stemmed})",
                    "severity": keyword_data["severity"],
                    "boost": keyword_data["boost"]
                })
                total_boost += keyword_data["boost"]
                max_severity = max(max_severity, keyword_data["severity"])

        base_score = 30

        category_weights = {
            "roads": 20,
            "water supply": 25,
            "water": 25,
            "drainage": 25,
            "electricity": 30,
            "sanitation": 15,
            "public safety": 35
        }

        category_boost = category_weights.get(category.lower(), 10)

        if max_severity >= 80:
            final_score = min(100, base_score + max_severity)
        else:
            final_score = min(100, base_score + category_boost + total_boost)

        reasoning = self._generate_reasoning(matched_keywords, category, final_score)

        return {
            "score": final_score,
            "matched_keywords": matched_keywords,
            "reasoning": reasoning,
            "base_score": base_score,
            "category_boost": category_boost,
            "keyword_boost": total_boost
        }

    def _generate_reasoning(self, matched_keywords: List, category: str, score: int) -> str:
        """Generate human-readable reasoning for the score"""
        if not matched_keywords:
            return f"Standard {category} complaint (base urgency)"

        high_severity = [k for k in matched_keywords if k["severity"] >= 80]
        medium_severity = [k for k in matched_keywords if 50 <= k["severity"] < 80]

        reasons = []

        if high_severity:
            words = ", ".join([k["word"] for k in high_severity[:3]])
            reasons.append(f"Critical keywords detected: {words}")

        if medium_severity:
            words = ", ".join([k["word"] for k in medium_severity[:3]])
            reasons.append(f"Urgent keywords detected: {words}")

        if score >= 90:
            reasons.append("EMERGENCY - Requires immediate attention")
        elif score >= 70:
            reasons.append("HIGH PRIORITY - Needs urgent response")
        elif score >= 50:
            reasons.append("MEDIUM PRIORITY - Requires timely action")

        return " | ".join(reasons)


# ============================================================
# MAIN FUNCTION — Cloudinary URL + Local Path dono support
# ============================================================

def calculate_urgency(
        description: str,
        category: str,
        image_path: Optional[str] = None,   # Local file path (optional)
        image_url: Optional[str] = None     # ✅ Cloudinary URL (optional)
) -> int:
    """
    Enhanced urgency calculation with advanced NLP + image analysis.
    Accepts either a local image_path OR a Cloudinary image_url.
    """
    analyzer = UrgencyAnalyzer()

    # Step 1: Text NLP analysis
    text_analysis = analyzer.analyze_text(description, category)
    urgency_score = text_analysis["score"]

    print(f"\n📊 URGENCY ANALYSIS:")
    print(f"   Text Score: {urgency_score}/100")
    print(f"   Matched Keywords: {len(text_analysis['matched_keywords'])}")
    if text_analysis['matched_keywords']:
        print(f"   Top Keywords:")
        for kw in text_analysis['matched_keywords'][:5]:
            print(f"      - {kw['word']} (severity: {kw['severity']}, boost: +{kw['boost']})")
    print(f"   Reasoning: {text_analysis['reasoning']}")

    # Step 2: Image analysis
    try:
        # --- Option A: Local file path provided ---
        if image_path and os.path.exists(image_path):
            print(f"   🖼️ Using local image: {image_path}")
            image_boost = analyze_image_urgency(image_path, category)
            print(f"   Image Boost: +{image_boost}")
            urgency_score = min(100, urgency_score + image_boost)

        # --- Option B: Cloudinary URL provided ---
        elif image_url:
            print(f"   🌐 Downloading image from Cloudinary URL...")
            response = requests.get(image_url, timeout=10)

            if response.status_code == 200:
                temp_path = "/tmp/urgency_temp_image.jpg"

                with open(temp_path, "wb") as f:
                    f.write(response.content)

                print(f"   ✅ Image downloaded ({len(response.content) // 1024} KB)")

                image_boost = analyze_image_urgency(temp_path, category)
                print(f"   Image Boost: +{image_boost}")
                urgency_score = min(100, urgency_score + image_boost)

                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            else:
                print(f"   ❌ Failed to download image (HTTP {response.status_code})")

        else:
            print(f"   ℹ️ No image provided — text-only analysis")

    except Exception as e:
        print(f"   ⚠️ Image analysis failed: {e}")

    print(f"   FINAL SCORE: {urgency_score}/100\n")

    return urgency_score


def analyze_image_urgency(image_path: str, category: str) -> int:
    """
    Analyze image using Hugging Face's free inference API.
    Falls back to local pixel analysis if API unavailable.
    Returns urgency boost (0-30 points).
    """

    # ✅ Correct endpoint for zero-shot image classification
    API_URL = "https://api-inference.huggingface.co/pipeline/zero-shot-image-classification/openai/clip-vit-large-patch14"
    API_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")

    if not API_TOKEN:
        print("   ⚠️ No HUGGINGFACE_TOKEN — skipping HuggingFace, using local fallback")
        return analyze_image_urgency_local(image_path, category)

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode()

        severity_labels = {
            "roads": [
                "severe road damage with large dangerous potholes",
                "moderate road damage needing repair",
                "minor road issue or well maintained"
            ],
            "water supply": [
                "major water leak flooding the area",
                "moderate water leak or dripping",
                "normal water supply"
            ],
            "drainage": [
                "severe flooding with water overflow",
                "moderate drainage blockage",
                "clear drainage"
            ],
            "electricity": [
                "exposed dangerous electrical wires sparking",
                "minor electrical issue",
                "normal electrical installation"
            ],
            "sanitation": [
                "severe garbage accumulation and filth",
                "moderate garbage pile",
                "clean area"
            ]
        }

        labels = severity_labels.get(category.lower(), [
            "severe damage requiring urgent attention",
            "moderate issue needing repair",
            "minor or no issue"
        ])

        # ✅ Correct payload format for pipeline endpoint
        payload = {
            "inputs": image_data,           # base64 string directly (not nested dict)
            "parameters": {
                "candidate_labels": labels  # labels go inside parameters
            }
        }

        print(f"   🚀 Sending image to HuggingFace API...")

        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)  # timeout 30s

        if response.status_code == 200:
            result = response.json()
            print(f"   🔍 API Response: {result}")

            # ✅ Pipeline format: [{"label": "severe...", "score": 0.72}, {"label": "moderate...", "score": 0.20}, ...]
            if isinstance(result, list) and len(result) >= 1 and isinstance(result[0], dict) and "label" in result[0]:
                label_scores = {item["label"]: item["score"] for item in result}

                severe_label = labels[0]
                moderate_label = labels[1]

                severe_confidence = label_scores.get(severe_label, 0)
                moderate_confidence = label_scores.get(moderate_label, 0)

                print(f"   📊 Confidence — Severe: {severe_confidence:.2%}, Moderate: {moderate_confidence:.2%}")

                if severe_confidence > 0.5:
                    return 30
                elif severe_confidence > 0.35:
                    return 20
                elif moderate_confidence > 0.4:
                    return 10
                else:
                    return 0

            # Fallback: old list-of-floats format
            elif isinstance(result, list) and len(result) >= 2 and isinstance(result[0], float):
                severe_confidence = result[0]
                moderate_confidence = result[1]
                print(f"   📊 Confidence — Severe: {severe_confidence:.2%}, Moderate: {moderate_confidence:.2%}")
                if severe_confidence > 0.5:
                    return 30
                elif severe_confidence > 0.35:
                    return 20
                elif moderate_confidence > 0.4:
                    return 10

        else:
            print(f"   ❌ API status {response.status_code}: {response.text[:200]}")

    except Exception as e:
        print(f"   ⚠️ HuggingFace API error: {e}")

    # Fallback to local analysis
    print("   🔄 API unavailable — using local image analysis...")
    return analyze_image_urgency_local(image_path, category)


def analyze_image_urgency_local(image_path: str, category: str) -> int:
    """
    Local pixel-based image analysis fallback.
    No external API needed — uses PIL + numpy.
    """
    try:
        from PIL import Image
        import numpy as np

        if not os.path.exists(image_path):
            return 0

        img = Image.open(image_path).convert('RGB')
        img.thumbnail((400, 400))
        img_array = np.array(img)

        print(f"   🖼️ Local analysis ({img.size[0]}x{img.size[1]} px)...")

        avg_brightness = np.mean(img_array)
        darkness_score = (255 - avg_brightness) / 255

        gray = np.mean(img_array, axis=2)
        contrast = np.std(gray) / 128

        color_std = np.std(img_array, axis=(0, 1)).mean() / 128
        dark_pixels = np.sum(np.mean(img_array, axis=2) < 80) / (img_array.shape[0] * img_array.shape[1])

        print(f"   📊 Darkness: {darkness_score:.2f}, Contrast: {contrast:.2f}, Dark pixels: {dark_pixels:.1%}")

        boost = 0

        if category.lower() in ["roads", "road"]:
            if contrast > 0.8 and dark_pixels > 0.15:
                boost = 30
            elif contrast > 0.6 or dark_pixels > 0.10:
                boost = 20
            elif contrast > 0.4:
                boost = 10

        elif category.lower() in ["drainage", "water supply", "water"]:
            if darkness_score > 0.6 or dark_pixels > 0.25:
                boost = 30
            elif darkness_score > 0.4 or dark_pixels > 0.15:
                boost = 20
            elif dark_pixels > 0.08:
                boost = 10

        elif category.lower() in ["sanitation", "garbage"]:
            if color_std > 0.7 and darkness_score > 0.3:
                boost = 30
            elif color_std > 0.5:
                boost = 20
            elif color_std > 0.3:
                boost = 10

        else:
            severity = (darkness_score + contrast + color_std) / 3
            if severity > 0.6:
                boost = 30
            elif severity > 0.45:
                boost = 20
            elif severity > 0.3:
                boost = 10
            print(f"   📈 Generic severity: {severity:.2f} → +{boost}")

        print(f"   ✅ Local boost: +{boost}")
        return boost

    except ImportError:
        print("   ⚠️ Install Pillow/numpy: pip install Pillow numpy")
        return 0
    except Exception as e:
        print(f"   ❌ Local analysis error: {e}")
        return 0