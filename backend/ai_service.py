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


# ══════════════════════════════════════════
# v3.2: AI 評分與情報生成服務
# ══════════════════════════════════════════

def score_lead(company_name: str, domain: str, description: str, has_email: bool, has_phone: bool, ai_tag: str, has_website: bool, user_keywords: str = "") -> dict:
    """
    根據多維度評估 Lead 品質，分數 0-100。
    
    評分維度：
    - 網站存在 +20
    - Email 成功發現 +25
    - 公司名稱含目標關鍵字 +20
    - 非不相關行業 +15
    - 域名品質（非大型平台） +20
    """
    score = 0
    tags = []
    
    # 1. 網站存在 +20
    if has_website:
        score += 20
        tags.append("有官網")
    else:
        tags.append("無官網")
    
    # 2. Email 發現 +25
    if has_email:
        score += 25
        tags.append("有信箱")
    else:
        tags.append("缺信箱")
    
    # 3. 電話存在 +5
    if has_phone:
        score += 5
        tags.append("有電話")
    
    # 4. 公司名稱含目標關鍵字 +20
    if user_keywords:
        user_keywords_lower = user_keywords.lower()
        company_lower = company_name.lower()
        if any(kw in company_lower for kw in user_keywords_lower.split(",")):
            score += 20
            tags.append("關鍵字匹配")
    
    # 5. 非不相關行業（白名單加分）
    positive_tags = ["IND-", "ELEC-", "CHEM-", "AUTO-", "TECH-", "HEALTH-", "LOGI-", "FOOD-", "PACK-", "CONST-", "TOOL-"]
    if ai_tag and any(tag in ai_tag for tag in positive_tags):
        score += 15
        tags.append("目標行業")
    
    # 6. 域名品質 +20（排除大型平台）
    bad_domains = ["facebook.com", "instagram.com", "linkedin.com", "twitter.com", 
                   "youtube.com", "google.com", "amazon.com", "yelp.com", "bbb.org",
                   "yellowpages.com", "thomasnet.com"]
    if domain and domain not in bad_domains and "." in domain:
        score += 15
        tags.append("獨立域名")
    elif domain and any(bad in domain for bad in bad_domains):
        tags.append("平台頁面")
    
    # 7. 有公司描述 +5
    if description and len(description) > 20:
        score += 5
        tags.append("有描述")
    
    # 評語
    if score >= 80:
        verdict = "高匹配"
    elif score >= 60:
        verdict = "中匹配"
    elif score >= 40:
        verdict = "待確認"
    else:
        verdict = "低優先"
    
    return {
        "score": min(score, 100),
        "tags": tags,
        "verdict": verdict
    }


async def generate_lead_brief(company_name: str, domain: str, description: str, ai_tag: str, db = None, user_id: int = None) -> dict:
    """
    生成公司簡介情報。
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return {
            "brief": f"{company_name} 是一家專注於 {ai_tag} 的公司。",
            "suggestions": ["請設定 OpenAI API Key 以生成詳細情報"]
        }
    
    openai.api_key = api_key
    
    prompt = f"""
你是一個專業的 B2B 業務情報分析師。請根據以下資訊，生成一段簡潔的「開發前情報摘要」。

【公司名稱】: {company_name}
【網站】: {domain if domain else "未知"}
【公司描述】: {description if description else "無詳細描述"}
【AI 分類】: {ai_tag if ai_tag else "未分類"}

請生成：
1. 一段 50-100 字的公司情報摘要（可用於開發信破冰）
2. 2-3 個針對這個公司的具體切入點建議

輸出格式 JSON：
{{
  "brief": "情報摘要...",
  "suggestions": ["切入點1", "切入點2", "切入點3"]
}}
"""
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是專業的 B2B 業務情報分析師，輸出嚴格的 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "brief": f"{company_name} 是一家專注於 {ai_tag or '相關業務'} 的公司。",
            "suggestions": ["請聯繫確認合作需求"]
        }


async def optimize_email_subject(subject: str, company_name: str = "", db = None, user_id: int = None) -> dict:
    """
    優化信件主旨，生成 3 個高開信率版本。
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return {"suggestions": [subject], "message": "請設定 OpenAI API Key"}
    
    openai.api_key = api_key
    
    prompt = f"""
根據以下現有主旨，生成 3 個風格迥異、開信率更高的替代主旨。

【現有主旨】: {subject}
【公司名稱】: {company_name if company_name else "（未指定）"}

要求：
1. 每個主旨控制在 60 字以內，且三個建議必須「截然不同」。
2. 涵蓋不同策略：
   - 建議 A (理性數字型): 強調效益、節省、效率或具體數據。
   - 建議 B (好奇問句型): 引發對方思考或好奇心的提問。
   - 建議 C (極簡個性化): 像真實人類發出的短小、非行銷感的私人郵件風格。
3. 包含公司名稱（如適用）。

輸出 JSON 格式：
{{"suggestions": ["建議A", "建議B", "建議C"]}}
"""
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是 B2B 郵件行銷與心理學專家，擅長撰寫高點擊率的主旨。請嚴格輸出 JSON 格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85
        )
        result = json.loads(response.choices[0].message.content)
        return {"suggestions": result.get("suggestions", [subject])}
    except Exception as e:
        return {"suggestions": [subject], "message": str(e)}


async def generate_ab_test_versions(company_name: str, tag: str, keywords: list, db = None, user_id: int = None) -> dict:
    """
    生成 A/B 測試雙版本：A = 理性數據型，B = 故事情感型。
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return {
            "version_a": {"subject": "合作提案", "body": "請設定 OpenAI API Key"},
            "version_b": {"subject": "合作提案", "body": "請設定 OpenAI API Key"}
        }
    
    openai.api_key = api_key
    
    prompt = f"""
請為以下公司生成 A/B 測試版本的開發信。

【公司名稱】: {company_name}
【AI 分類】: {tag}
【核心關鍵字】: {', '.join(keywords)}

版本 A（理性/數據型）：
- 使用數據、具體數字、專業術語
- 直接說明價值主張
- 主旨包含具體數字或效益

版本 B（故事/情感型）：
- 以一個情境或問題開始
- 喚起情感共鳴
- 主旨更具故事性或好奇心

每封信控制在 150 字以內，輸出 JSON：
{{
  "version_a": {{"subject": "主旨", "body": "信件內容"}},
  "version_b": {{"subject": "主旨", "body": "信件內容"}}
}}
"""
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是頂尖 B2B 開發信專家，輸出嚴格 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "version_a": {"subject": "合作提案", "body": str(e)},
            "version_b": {"subject": "合作提案", "body": str(e)}
        }


async def generate_weekly_report_summary(stats: dict, period_start: str, period_end: str, db = None, user_id: int = None) -> dict:
    """
    生成 AI 成效摘要報告。
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return {
            "summary": f"期間：{period_start} ~ {period_end}。寄送 {stats.get('sent', 0)} 封，開信率 {stats.get('open_rate', 0)}%。",
            "insights": ["請設定 OpenAI API Key 以生成詳細報告"]
        }
    
    openai.api_key = api_key
    
    prompt = f"""
你是 Linkora 的 AI 成效分析師。請根據以下數據，生成一份自然語言的成效摘要報告。

【統計期間】: {period_start} ~ {period_end}
【寄送總數】: {stats.get('sent', 0)} 封
【開信數】: {stats.get('opened', 0)} 封
【開信率】: {stats.get('open_rate', 0)}%
【點擊數】: {stats.get('clicked', 0)} 封
【點擊率】: {stats.get('click_rate', 0)}%
【退信數】: {stats.get('bounced', 0)} 封
【退信率】: {stats.get('bounce_rate', 0)}%
【回覆數】: {stats.get('replied', 0)} 封
【AI 分析標籤】: {stats.get('top_tags', [])}

請生成：
1. 一段成效摘要（2-3 句話）
2. 2-3 個具體改善建議
3. 1 個本週亮點

輸出 JSON：
{{
  "summary": "摘要...",
  "insights": ["建議1", "建議2", "建議3"],
  "highlight": "本週亮點..."
}}
"""
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是 Linkora 的 AI 成效分析師，輸出嚴格 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "summary": f"期間寄送 {stats.get('sent', 0)} 封，開信率 {stats.get('open_rate', 0)}%。",
            "insights": ["數據不足，請持續累積後再看趨勢"]
        }


async def recommend_optimal_send_time(db, user_id: int) -> dict:
    """
    v3.2: 分析用戶歷史數據，推薦最佳寄信時間。
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    from models import EmailLog
    from datetime import datetime, timezone
    
    # 分析歷史數據
    email_logs = db.query(EmailLog).filter(
        EmailLog.user_id == user_id,
        EmailLog.opened == True,
        EmailLog.created_at.isnot(None)
    ).all()
    
    # 統計各時段開信率
    hour_counts = {}
    day_counts = {}
    
    for log in email_logs:
        if log.created_at:
            local_ts = log.created_at.astimezone(timezone.utc) if log.created_at.tzinfo else log.created_at
            hour = local_ts.hour
            weekday = local_ts.strftime('%A')
            
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
            day_counts[weekday] = day_counts.get(weekday, 0) + 1
    
    if not hour_counts:
        return {
            "best_day": "Tuesday",
            "best_hour": 9,
            "confidence": "low",
            "reason": "數據不足，請累積至少 10 封開信記錄後再分析",
            "recommendation": "一般建議：週二至週四、上午 9-11 點"
        }
    
    # 找出最佳時段
    best_hour = max(hour_counts, key=hour_counts.get)
    best_day = max(day_counts, key=day_counts.get) if day_counts else "Tuesday"
    
    confidence = "high" if len(email_logs) >= 30 else "medium" if len(email_logs) >= 10 else "low"
    
    # 格式化時段
    hour_display = f"{best_hour:02d}:00"
    if best_hour < 12:
        period = "上午"
    elif best_hour < 17:
        period = "下午"
    else:
        period = "晚間"
    
    return {
        "best_day": best_day,
        "best_hour": best_hour,
        "best_time_display": f"{best_day} {hour_display} ({period})",
        "confidence": confidence,
        "total_opened": len(email_logs),
        "hour_breakdown": dict(sorted(hour_counts.items())),
        "reason": f"根據您過去 {len(email_logs)} 封開信記錄分析，{best_day} {hour_display} 的開信率最高"
    }


async def analyze_reply_intent(email_body: str, db = None, user_id: int = None) -> dict:
    """
    v3.2: 分析回信意圖，分類為：有興趣 / 需要更多資訊 / 拒絕 / 需要跟進
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return {"intent": "unknown", "confidence": "low", "analysis": "請設定 OpenAI API Key"}
    
    openai.api_key = api_key
    
    prompt = f"""
分析以下這封回信的意圖，並給出分類與後續建議。

【回信內容】：
{email_body[:1000]}

分類選項：
- positive：有興趣，想進一步瞭解或安排會議
- needs_info：需要更多資訊或報價
- declined：明確拒絕或表示不需要
- follow_up：表示有興趣但時機不對，需要後續跟進
- out_of_office：出差/不在辦公室

輸出 JSON：
{{"intent": "分類", "confidence": "高/中/低", "analysis": "一句話分析", "next_action": "建議的後續動作"}}
"""
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是 B2B 銷售分析師，輸出嚴格 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"intent": "unknown", "confidence": "low", "analysis": str(e)}


async def generate_reply_draft(original_body: str, intent: str, db = None, user_id: int = None) -> str:
    """
    v3.7: 根據回信內容與意圖，產生 AI 回覆草稿
    """
    api_key = get_api_key(db, "openai", user_id)
    model = get_openai_model(db, user_id)
    
    if not api_key:
        return "OpenAI API Key 未設定，無法產生草稿。"
    
    openai.api_key = api_key

    # 針對不同意圖設定建議語氣
    tone_guides = {
        "positive": "熱情、專業且直接。提議安排 15 分鐘的短暫會議或提供行事曆連結。",
        "needs_info": "專業且提供價值。承諾會提供所需資訊，並詢問是否有特定的產品規格。",
        "follow_up": "有禮貌、體諒。表示感謝，並詢問適合再次聯繫的時間（通常是幾個月後）。",
        "declined": "得體、感激。感謝對方的回覆，並表示如果未來有需求歡迎隨時聯繫。",
        "out_of_office": "告知性質。表示收到訊息，將在對方返回後再次聯繫。"
    }

    prompt = f"""
你是一位專業的 B2B 業務代表，代表 Corelink 公司（台灣客製化工業件採購專家）。
請根據客戶發來的【原信內容】與分析出的【意圖】，撰寫一封精確且專業的回覆草稿。

【原信內容】：
{original_body[:1000]}

【意圖標籤】：{intent}
【撰寫建議】：{tone_guides.get(intent, "專業、商業化")}

【要求】：
1. 輸出**僅包含**郵件內容（不含主旨、不含 JSON）。
2. 使用 Professional English。
3. 採用簡潔、易讀的段落。
4. 結尾請固定包含 "Corelink Sales Team"。
"""

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional B2B Sales Assistant. Output ONLY the email body text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(AI 草稿生成失敗: {str(e)})"
