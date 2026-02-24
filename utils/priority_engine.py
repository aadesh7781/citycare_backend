# utils/priority_engine.py

import re

# Keywords mapped to urgency weight
KEYWORD_WEIGHTS = {
    "accident": 30,
    "fire": 35,
    "flood": 30,
    "overflow": 25,
    "blocked": 20,
    "leak": 20,
    "burst": 30,
    "danger": 25,
    "health": 20,
    "garbage": 15,
    "sewage": 25,
    "electric": 30,
    "pothole": 20,
}

# Category base urgency
CATEGORY_BASE_SCORE = {
    "Roads": 20,
    "Sanitation": 25,
    "Water Supply": 30,
    "Electricity": 35,
    "Drainage": 30,
}

def calculate_urgency(category: str, description: str) -> int:
    """
    Calculate urgency score (0–100)
    based on category + NLP keyword analysis
    """

    score = 0

    # 1️⃣ Category base score
    score += CATEGORY_BASE_SCORE.get(category, 10)

    # 2️⃣ Keyword matching (simple NLP)
    desc = description.lower()

    for keyword, weight in KEYWORD_WEIGHTS.items():
        if re.search(rf"\b{keyword}\b", desc):
            score += weight

    # 3️⃣ Length-based severity (long complaints = more serious)
    if len(description) > 100:
        score += 10
    elif len(description) > 50:
        score += 5

    # 4️⃣ Clamp score between 0–100
    score = max(0, min(score, 100))

    return score
