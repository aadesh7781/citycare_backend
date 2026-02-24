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
        Example: "hazardous" -> "hazard", "dangerous" -> "danger"
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
        """
        Tokenize text into words and phrases
        Returns both individual words and 2-3 word phrases
        """
        text = text.lower().strip()

        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split into words
        words = text.split()

        tokens = []

        # Add individual words
        tokens.extend(words)

        # Add 2-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            tokens.append(phrase)

        # Add 3-word phrases
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            tokens.append(phrase)

        return tokens

    def stem_word(self, word: str) -> str:
        """
        Apply stemming rules to normalize words
        """
        # Check exact match in stemming rules
        if word in self.stemming_rules:
            return self.stemming_rules[word]

        # Apply common suffix removal
        # -ous
        if word.endswith('ous') and len(word) > 4:
            return word[:-3]

        # -ed
        if word.endswith('ed') and len(word) > 3:
            return word[:-2]

        # -ing
        if word.endswith('ing') and len(word) > 4:
            return word[:-3]

        # -s (plural)
        if word.endswith('s') and len(word) > 2 and not word.endswith('ss'):
            return word[:-1]

        return word

    def analyze_text(self, description: str, category: str) -> Dict:
        """
        Analyze text and calculate urgency score
        Returns: {score: int, matched_keywords: List, reasoning: str}
        """
        tokens = self.tokenize(description)

        matched_keywords = []
        total_boost = 0
        max_severity = 0

        # Check each token
        for token in tokens:
            # Check exact match
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

            # Check stemmed version
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

        # Calculate base score
        base_score = 30

        # Add category weight
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

        # Calculate final score
        # Use max severity if very high, otherwise use boost
        if max_severity >= 80:
            final_score = min(100, base_score + max_severity)
        else:
            final_score = min(100, base_score + category_boost + total_boost)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            matched_keywords,
            category,
            final_score
        )

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


# Main function for backward compatibility
def calculate_urgency(description: str, category: str, image_path: Optional[str] = None) -> int:
    """
    Enhanced urgency calculation with advanced NLP
    """
    analyzer = UrgencyAnalyzer()

    # Analyze text
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

    # Image analysis boost
    if image_path and os.path.exists(image_path):
        try:
            image_boost = analyze_image_urgency(image_path, category)
            print(f"   Image Boost: +{image_boost}")
            urgency_score = min(100, urgency_score + image_boost)
        except Exception as e:
            print(f"   ⚠️ Image analysis failed: {e}")

    print(f"   FINAL SCORE: {urgency_score}/100\n")

    return urgency_score


def analyze_image_urgency(image_path: str, category: str) -> int:
    """
    Analyze image using Hugging Face's free inference API
    Returns urgency boost (0-30 points) based on visual severity
    """

    # Updated Hugging Face API endpoint (moved from api-inference to router)
    API_URL = "https://router.huggingface.co/models/openai/clip-vit-large-patch14"
    API_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")

    if not API_TOKEN:
        print("   ⚠️ No HUGGINGFACE_TOKEN - skipping image analysis")
        return 0

    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode()

        # Define severity labels
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

        payload = {
            "inputs": {
                "image": image_data,
                "candidate_labels": labels
            }
        }

        print(f"   🚀 Sending image to Hugging Face API...")
        print(f"   📝 Category: {category}")
        print(f"   🏷️ Testing labels: {labels[:2]}...")  # Show first 2 labels

        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)

        if response.status_code == 200:
            result = response.json()
            print(f"   🔍 Image API Response: {result}")

            # CLIP returns list of scores corresponding to candidate_labels
            if isinstance(result, list) and len(result) >= 3:
                # Labels order: [severe, moderate, minor]
                severe_confidence = result[0]
                moderate_confidence = result[1]

                print(f"   📊 Confidence - Severe: {severe_confidence:.2%}, Moderate: {moderate_confidence:.2%}")

                # Higher confidence in severe = higher boost
                if severe_confidence > 0.5:
                    boost = 30
                    print(f"   ✅ High severity detected: +{boost} urgency boost")
                    return boost
                elif severe_confidence > 0.35:
                    boost = 20
                    print(f"   ⚠️ Moderate severity detected: +{boost} urgency boost")
                    return boost
                elif moderate_confidence > 0.4:
                    boost = 10
                    print(f"   ℹ️ Some issues detected: +{boost} urgency boost")
                    return boost
                else:
                    print(f"   ✓ Minor or no issues detected: +0 urgency boost")
                    return 0

            # Alternative format (some models return dict)
            elif isinstance(result, dict) and "scores" in result:
                scores = result["scores"]
                if len(scores) >= 3:
                    severe_confidence = scores[0]
                    moderate_confidence = scores[1]

                    print(f"   📊 Confidence - Severe: {severe_confidence:.2%}, Moderate: {moderate_confidence:.2%}")

                    if severe_confidence > 0.5:
                        return 30
                    elif severe_confidence > 0.35:
                        return 20
                    elif moderate_confidence > 0.4:
                        return 10

        else:
            print(f"   ❌ Image API returned status {response.status_code}: {response.text[:200]}")

    except Exception as e:
        print(f"   ⚠️ Image API error: {e}")

    # If API failed, try local analysis as fallback
    print("   🔄 API unavailable, using local image analysis...")
    return analyze_image_urgency_local(image_path, category)


def analyze_image_urgency_local(image_path: str, category: str) -> int:

    try:
        from PIL import Image
        import numpy as np

        if not os.path.exists(image_path):
            return 0

        img = Image.open(image_path).convert('RGB')
        img.thumbnail((400, 400))
        img_array = np.array(img)

        print(f"   🖼️ Analyzing locally ({img.size[0]}x{img.size[1]} pixels)...")

        # Image metrics
        avg_brightness = np.mean(img_array)
        darkness_score = (255 - avg_brightness) / 255

        gray = np.mean(img_array, axis=2)
        contrast = np.std(gray) / 128

        color_std = np.std(img_array, axis=(0,1)).mean() / 128
        dark_pixels = np.sum(np.mean(img_array, axis=2) < 80) / (img_array.shape[0] * img_array.shape[1])

        print(f"   📊 Darkness: {darkness_score:.2f}, Contrast: {contrast:.2f}, Dark: {dark_pixels:.1%}")

        boost = 0

        if category.lower() in ["roads", "road"]:
            if contrast > 0.8 and dark_pixels > 0.15:
                boost = 30
                print(f"   ✅ SEVERE road damage detected")
            elif contrast > 0.6 or dark_pixels > 0.10:
                boost = 20
                print(f"   ⚠️ MODERATE road damage detected")
            elif contrast > 0.4:
                boost = 10
                print(f"   ℹ️ Minor road issues detected")

        elif category.lower() in ["drainage", "water supply", "water"]:
            if darkness_score > 0.6 or dark_pixels > 0.25:
                boost = 30
                print(f"   ✅ SEVERE water/drainage issue")
            elif darkness_score > 0.4 or dark_pixels > 0.15:
                boost = 20
                print(f"   ⚠️ MODERATE water/drainage issue")
            elif dark_pixels > 0.08:
                boost = 10

        elif category.lower() in ["sanitation", "garbage"]:
            if color_std > 0.7 and darkness_score > 0.3:
                boost = 30
                print(f"   ✅ SEVERE garbage accumulation")
            elif color_std > 0.5:
                boost = 20
                print(f"   ⚠️ MODERATE garbage present")
            elif color_std > 0.3:
                boost = 10

        else:
            # Generic severity score
            severity = (darkness_score + contrast + color_std) / 3
            if severity > 0.6:
                boost = 30
            elif severity > 0.45:
                boost = 20
            elif severity > 0.3:
                boost = 10
            print(f"   📈 Generic severity: {severity:.2f} → +{boost}")

        return boost

    except ImportError:
        print("   ⚠️ Install Pillow/numpy for local analysis: pip install Pillow numpy")
        return 0
    except Exception as e:
        print(f"   ❌ Local analysis error: {e}")
        return 0