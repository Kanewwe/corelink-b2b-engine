import os
import openai
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI (Set dynamically per request)
from config_utils import get_api_key, get_openai_model

# Import rule-based classifier (saves tokens)
from classifier import classify_lead as rule_classify

def analyze_company_and_tag(company_name: str, description: str, use_gpt: bool = False, db = None, user_id: int = None) -> dict:
    """
    Classify lead and extract keywords.
    Default: use rule-based classification (no GPT, saves tokens)
    Set use_gpt=True to fallback to GPT-4o-mini for complex cases
    """
    if not use_gpt:
        return rule_classify(company_name, description)
    
    # GPT fallback (only if explicitly requested)
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return {"Tag": "UNKNOWN", "BD": "General", "Reason": "OpenAI API Key not set", "Keywords": []}

    openai.api_key = api_key
    
    prompt = f"""
    你是一個 B2B 採購與供應鏈專家。我會提供一家位於北美的中小企業製造商簡介。請分析他們的主要業務，並嚴格按照規則分類，最後輸出 JSON。

    【公司名稱】: {company_name}
    【公司簡介】: {description}

    分類規則：
    1. 工業製造: IND-MANUFACTURING (工廠), IND-MACHINING (加工), IND-LABEL (標籤/銘牌)
    2. 電機電線: ELEC-CABLE (線束), ELEC-CONNECTOR (連接器)
    3. 塑膠化學: CHEM-PLASTIC (材料), CHEM-MOLDING (射出成型)
    4. 汽車工業: AUTO-PARTS (零件), AUTO-ENGINE (引擎), AUTO-ELECTRICAL (電系)
    5. 電子科技: TECH-SEMICONDUCTOR (半導體), TECH-PCB (電路板), TECH-IOT (物聯網)
    6. 醫療健康: HEALTH-MEDICAL (醫材), HEALTH-PHARMA (製藥)
    7. 物流快遞: LOGI-WAREHOUSE (倉儲), LOGI-FREIGHT (貨運)
    
    技術關鍵字：
    也請從【公司簡介】中精準萃取 2 到 4 個技術或終端應用的「核心業務關鍵字」。

    輸出格式要求：
    {"Tag": "[對應標籤]", "BD": "[對應的BD]", "Keywords": ["關鍵字1", "關鍵字2"], "Reason": "[解釋為何分到此類]"}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API (Tagging): {e}")
        return {"Tag": "UNKNOWN", "BD": "General", "Reason": str(e), "Keywords": []}

def generate_outreach_email(company_name: str, description: str, tag: str, bd_name: str, keywords: list, db = None, user_id: int = None) -> dict:
    """
    Generate personalized outreach email using GPT-4o-mini.
    This is Prompt 2 - kept because it needs creative writing.
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return {"Subject": "Error", "Body": "OpenAI API Key not set"}
    
    openai.api_key = api_key

    prompt = f"""
    你是一位頂尖的 B2B 業務代表，代表台灣客製化工業件採購公司 "Corelink"。
    請根據以下提供的【客戶資訊】與【產品線策略】，撰寫一封簡潔、專業且具備高轉換率的開發信。

    【客戶資訊】
    公司名稱: {company_name}
    業務內容: {description}
    標籤: {tag}
    核心關鍵字: {', '.join(keywords)}

    【產品線策略與指定模板】
    若為 ELEC-CABLE 或 ELEC-CONNECTOR (BD: Johnny):
    - 署名：Johnny
    - 核心模板：We support industrial equipment manufacturers with custom cable assemblies and high-reliability connectors from Taiwan. ✔ Flexible MOQ ✔ Fast turnaround ✔ UL/IPC certified.
    
    若為 IND-LABEL (BD: Richard):
    - 署名：Richard
    - 核心模板：We provide industrial-grade identification solutions, including metal nameplates, serial tags, and warning labels that withstand harsh environments.
    
    若為 CHEM-PLASTIC 或 CHEM-MOLDING (BD: Jason):
    - 署名：Jason
    - 核心模板：Specializing in custom plastic injection molding and precision parts for OEM applications. From prototyping to bulk production, we deliver high-quality components.

    【撰寫指示】：
    1. 信件主旨（Subject）必須具有吸引力，並包含客戶的公司名稱。
    2. 第一段直接結合對方的【核心關鍵字】與【業務內容】進行破冰 (Personalization)，讓客戶感受到我們有深入了解他們的特定需求。
    3. 中段無縫銜接指定的【核心模板】內容。
    4. 信件結尾必須包含 Slogan: "Corelink From Concept to Connect" 以及對應的 BD 署名。

    請以 JSON 輸出：{{"Subject": "...", "Body": "..."}}
    (注意 Body 段落需保留換行符號 \\n)
    """

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful B2B sales assistant that strictly outputs JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API (Email): {e}")
        return {"Subject": "Error generating email", "Body": str(e)}


def generate_related_keywords(seed_keyword: str, count: int = 5, db = None, user_id: int = None) -> list:
    """
    Generate related B2B industry keywords with actual parts/components focus.
    Used for auto-mining with specific part variations.
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return [seed_keyword + " parts", seed_keyword + " supplier"]
    
    openai.api_key = api_key
    
    prompt = f"""Given the B2B industry/product keyword "{seed_keyword}", generate {count} related keywords that are SPECIFIC PARTS or COMPONENTS related to this industry.

Requirements:
1. Focus on actual parts, components, or assemblies - NOT generic variations
2. Each keyword should describe a specific type of part or component
3. Suitable for Yellowpages/B2B business searches
4. Include part names, component types, or assembly variations

Examples:
- "cable" → ["cable assembly", "wire harness", "cable connector", "cable gland", "heat shrink cable"]
- "plastic injection" → ["plastic molding", "injection mold", "plastic housing", "molded parts", "plastic component"]
- "brake" → ["brake pad", "brake rotor", "brake caliper", "brake line", "brake assembly"]

Return ONLY a JSON array of {count} strings, nothing else."""

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful B2B sourcing assistant specializing in parts and components. Output ONLY JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        result = response.choices[0].message.content.strip()
        keywords = json.loads(result)
        if isinstance(keywords, list):
            return keywords[:count]
        return [seed_keyword]
    except Exception as e:
        print(f"Error generating keywords: {e}")
        # Fallback to part-focused variations
        return [
            seed_keyword + " parts",
            seed_keyword + " components",
            seed_keyword + " assembly",
            seed_keyword + " supplier",
            seed_keyword + " manufacturer"
        ][:count]

def generate_html_template(prompt: str, style: str = "formal", language: str = "English", db = None, user_id: int = None) -> dict:
    """
    Generate a professional HTML email template based on user prompt.
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return {"subject": "Error", "html": "OpenAI API Key not set"}
    
    openai.api_key = api_key
    
    style_hints = {
        "formal": "Professional, corporate, respectfull, B2B focused. Use clear headings.",
        "friendly": "Warm, welcoming, personal, approachable. Use conversational tone.",
        "urgent": "Time-sensitive, high-impact, direct call-to-action. Focus on benefits of immediate response.",
        "followup": "Gentle reminder, providing value, keeping the door open. Refer to previous contact."
    }
    
    system_prompt = f"""You are a world-class B2B email marketing expert. Your goal is to write a highly converting HTML email template in {language} language.
    
The template MUST be:
1. Professional and modern HTML (inline CSS only).
2. Fully responsive and visually appealing.
3. Include placeholders like {{company_name}}, {{bd_name}}, {{contact_name}}, {{keywords}}, {{description}}.
4. Tone should be: {style_hints.get(style, "Formal")}.

Output ONLY JSON format:
{{
  "subject": "A compelling email subject",
  "html": "<html>...</html>"
}}"""

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a template for: {prompt}"}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        # Handle cases where GPT might wrap in ```json
        if content.startswith("```"):
            chunks = content.split("```")
            content = chunks[1]
            if content.startswith("json"):
                content = content[4:]
        
        return json.loads(content)
    except Exception as e:
        print(f"Error generating HTML template: {e}")
        return {
            "subject": "Special Offer for {{company_name}}",
            "html": f"<html><body><h1>Hello!</h1><p>We are interested in your business activities. (Error: {str(e)})</p></body></html>"
        }
