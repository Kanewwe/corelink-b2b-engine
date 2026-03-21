"""
Rule-based lead classification (no GPT, saves tokens).
Replaces Prompt 1 from ai_service.py
"""

# Classification rules: keyword matching for each product line
CLASSIFICATION_RULES = {
    # 原有分類：線材、銘牌、塑膠
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
    },

    # 新增：汽車零組件行業
    "AUTO-ENGINE": {
        "rep": "General",
        "keywords": ["engine", "motor", "cylinder", "piston", "crankshaft", "camshaft", "valve", "oil pump", "water pump", "timing belt", "combustion", "turbocharger", "supercharger", "engine block", "head gasket"]
    },
    "AUTO-BRAKE": {
        "rep": "General",
        "keywords": ["brake", "braking", "disc brake", "rotor", "caliper", "brake pad", "abs", "master cylinder", "brake drum", "brake line", "brake fluid"]
    },
    "AUTO-SUSPENSION": {
        "rep": "General",
        "keywords": ["suspension", "shock absorber", "strut", "spring", "control arm", "ball joint", "tie rod", "stabilizer", "coilover", "wishbone", "sway bar"]
    },
    "AUTO-ELECTRICAL": {
        "rep": "General",
        "keywords": ["alternator", "starter", "battery", "ignition", "spark plug", "ignition coil", "sensor", "ecu", "wiring harness", "connector", "fuse", "relay", "voltage regulator"]
    },
    "AUTO-BODY": {
        "rep": "General",
        "keywords": ["bumper", "fender", "door panel", "hood", "trunk", "grille", "mirror", "windshield", "headlight", "taillight", "body panel", "quarter panel", "rocker panel"]
    },
    "AUTO-INTERIOR": {
        "rep": "General",
        "keywords": ["seat", "steering wheel", "dashboard", "carpet", "trim", "console", "armrest", "upholstery", "headliner", "door panel interior"]
    },
    "AUTO-TRANSMISSION": {
        "rep": "General",
        "keywords": ["transmission", "gearbox", "clutch", "drive shaft", "differential", "axle", "cvt", "torque converter", "flywheel", "gear shift"]
    },
    "AUTO-EXHAUST": {
        "rep": "General",
        "keywords": ["exhaust", "muffler", "catalytic converter", "exhaust manifold", "exhaust pipe", "tailpipe", "downpipe", "resonator", "emissions"]
    },
    "AUTO-COOLING": {
        "rep": "General",
        "keywords": ["radiator", "thermostat", "coolant", "heater core", "cooling fan", "radiator hose", "water pump", "intercooler", "antifreeze"]
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
