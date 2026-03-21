"""
Rule-based lead classification (no GPT, saves tokens).
Replaces Prompt 1 from ai_service.py
"""

# Classification rules: keyword matching for each product line
CLASSIFICATION_RULES = {
    "NA-CABLE": {
        "rep": "Johnny",
        "keywords": [
            "cable", "wire", "wiring harness", "electrical cable",
            "connector", "conduit", "fiber optic", "coaxial",
            "cable assembly", "wire harness", "electrical wire",
            "power cable", "data cable", "signal cable", "harness"
        ]
    },
    "NA-NAMEPLATE": {
        "rep": "Richard",
        "keywords": [
            "nameplate", "label", "tag", "badge", "engraving",
            "metal plate", "identification plate", "serial plate",
            "equipment tag", "rating plate", "warning label",
            "metal label", "industrial label", "product label"
        ]
    },
    "NA-PLASTIC": {
        "rep": "Jason",
        "keywords": [
            "plastic", "injection molding", "polymer", "resin",
            "thermoplastic", "abs", "polycarbonate", "nylon", "pvc",
            "plastic parts", "molded parts", "plastic enclosure",
            "plastic housing", "plastic component", "injection moulding",
            "extrusion", "plastic fabrication"
        ]
    }
}

def classify_lead(company_name: str, description: str) -> dict:
    """
    Rule-based classification using keyword matching.
    Returns: {"Tag": str, "BD": str, "Keywords": list, "Reason": str}
    """
    text = (company_name + " " + (description or "")).lower()
    
    best_match = None
    best_count = 0
    matched_keywords = []
    
    for label, config in CLASSIFICATION_RULES.items():
        found = [kw for kw in config["keywords"] if kw.lower() in text]
        if len(found) > best_count:
            best_count = len(found)
            best_match = label
            matched_keywords = found[:4]  # max 4 keywords
            best_rep = config["rep"]
    
    if best_match:
        return {
            "Tag": best_match,
            "BD": best_rep,
            "Keywords": matched_keywords,
            "Reason": f"Matched {best_count} keywords: {', '.join(matched_keywords)}"
        }
    
    return {
        "Tag": "UNKNOWN",
        "BD": "General",
        "Keywords": [],
        "Reason": "No matching keywords found"
    }
