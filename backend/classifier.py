"""
Rule-based lead classification (no GPT, saves tokens).
Replaces Prompt 1 from ai_service.py
"""

# Classification rules: keyword matching for each product line
CLASSIFICATION_RULES = {
    # 🏭 工業製造 (Industrial)
    "IND-MANUFACTURING": {
        "rep": "General",
        "keywords": ["factory", "manufacturing", "industrial", "production", "oem", "odm", "supplier", "contract manufacturing"]
    },
    "IND-MACHINING": {
        "rep": "General",
        "keywords": ["cnc", "machining", "lathe", "milling", "metal parts", "precision machining", "stamping", "forging", "die casting"]
    },
    "IND-LABEL": {
        "rep": "Richard",
        "keywords": ["nameplate", "label", "tag", "badge", "engraving", "metal plate", "serial plate", "identification tag"]
    },

    # ⚡ 電機/電纜 (Electrical)
    "ELEC-CABLE": {
        "rep": "Johnny",
        "keywords": ["cable", "wire", "harness", "wiring harness", "cable assembly", "fiber optic", "coaxial"]
    },
    "ELEC-CONNECTOR": {
        "rep": "Johnny",
        "keywords": ["connector", "plug", "socket", "terminal", "switch", "relay", "circuit breaker"]
    },

    # 🧪 塑膠/化學 (Chemical/Plastic)
    "CHEM-PLASTIC": {
        "rep": "Jason",
        "keywords": ["plastic", "polymer", "resin", "thermoplastic", "abs", "pvc", "polycarbonate"]
    },
    "CHEM-MOLDING": {
        "rep": "Jason",
        "keywords": ["injection molding", "molding", "moulding", "extrusion", "blow molding", "compression molding"]
    },

    # 🚗 汽車工業 (Automotive)
    "AUTO-PARTS": {
        "rep": "General",
        "keywords": ["aftermarket", "chassis", "auto parts", "automotive", "spare parts", "car components"]
    },
    "AUTO-ENGINE": {
        "rep": "General",
        "keywords": ["engine", "piston", "crankshaft", "camshaft", "valve", "turbocharger", "powertrain"]
    },
    "AUTO-ELECTRICAL": {
        "rep": "General",
        "keywords": ["alternator", "starter", "ecu", "sensors", "ignition", "spark plug"]
    },

    # 💻 電子科技 (Tech/Electronics)
    "TECH-SEMICONDUCTOR": {
        "rep": "General",
        "keywords": ["semiconductor", "wafer", "ic", "integrated circuit", "chip", "microelectronics"]
    },
    "TECH-PCB": {
        "rep": "General",
        "keywords": ["pcb", "printed circuit board", "pcba", "smt", "surface mount", "circuit board"]
    },
    "TECH-IOT": {
        "rep": "General",
        "keywords": ["iot", "smart device", "wireless", "sensors", "broadband", "telecom"]
    },

    # 🏥 醫療/教育 (Health/Med)
    "HEALTH-MEDICAL": {
        "rep": "General",
        "keywords": ["medical device", "surgical", "diagnostic", "healthcare", "lab equipment", "hospital"]
    },
    "HEALTH-PHARMA": {
        "rep": "General",
        "keywords": ["pharmaceutical", "drug", "biotech", "vaccine", "clinical"]
    },

    # 📦 物流/供應鏈 (Logistics)
    "LOGI-WAREHOUSE": {
        "rep": "General",
        "keywords": ["warehousing", "logistics", "distribution", "storage", "inventory", "3pl"]
    },
    "LOGI-FREIGHT": {
        "rep": "General",
        "keywords": ["freight", "shipping", "transport", "cargo", "trucking", "forwarding"]
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
