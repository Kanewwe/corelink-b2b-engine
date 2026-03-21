import os
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI Client (Make sure OPENAI_API_KEY is in .env)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import rule-based classifier (saves tokens)
from classifier import classify_lead as rule_classify

def analyze_company_and_tag(company_name: str, description: str, use_gpt: bool = False) -> dict:
    """
    Classify lead and extract keywords.
    Default: use rule-based classification (no GPT, saves tokens)
    Set use_gpt=True to fallback to GPT-4o-mini for complex cases
    """
    if not use_gpt:
        return rule_classify(company_name, description)
    
    # GPT fallback (only if explicitly requested)
    prompt = f"""
    你是一個 B2B 採購與供應鏈專家。我會提供一家位於北美的中小企業製造商簡介。請分析他們的主要業務，並嚴格按照規則分類，最後輸出 JSON。

    【公司名稱】: {company_name}
    【公司簡介】: {description}

    分類規則：
    1. 若需要客製化線束或電纜組件（wire, harness, cable assembly），請標籤為 NA-CABLE, BD 填 Johnny。
    2. 若生產設備需要銘牌或識別標籤（label, tag, metal marker, identification），請標籤為 NA-NAMEPLATE, BD 填 Richard。
    3. 若開發新產品需要塑膠射出成型或外殼零件（molding, parts, prototyping），請標籤為 NA-PLASTIC, BD 填 Jason。

    此外，也請從【公司簡介】中精準萃取 2 到 4 個技術或終端應用的「核心業務關鍵字」 (例如: wire harness, UL certified, plastic parts 等)，以陣列回傳。

    輸出格式要求：
    {{"Tag": "[對應標籤]", "BD": "[對應的BD]", "Keywords": ["關鍵字1", "關鍵字2"], "Reason": "[解釋為何分到此類]"}}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API (Tagging): {e}")
        return {"Tag": "UNKNOWN", "BD": "General", "Reason": str(e), "Keywords": []}

def generate_outreach_email(company_name: str, description: str, tag: str, bd_name: str, keywords: list) -> dict:
    """
    Generate personalized outreach email using GPT-4o-mini.
    This is Prompt 2 - kept because it needs creative writing.
    """
    prompt = f"""
    你是一位頂尖的 B2B 業務代表，代表台灣客製化工業件採購公司 "Corelink"。
    請根據以下提供的【客戶資訊】與【產品線策略】，撰寫一封簡潔、專業且具備高轉換率的開發信。

    【客戶資訊】
    公司名稱: {company_name}
    業務內容: {description}
    標籤: {tag}
    核心關鍵字: {', '.join(keywords)}

    【產品線策略與指定模板】
    若為 NA-CABLE (訴求：Urgent):
    - 署名：Johnny
    - 核心模板：We support industrial equipment and system manufacturers with custom cable assemblies from Taiwan, helping improve sourcing flexibility. ✔ Custom wire harness ✔ Flexible MOQ ✔ Fast turnaround for urgent projects. If you have any ongoing builds, feel free to share drawings.
    
    若為 NA-NAMEPLATE (訴求：Stable):
    - 署名：Richard
    - 核心模板：We support OEM manufacturers with custom industrial nameplates from Taiwan, ensuring consistent quality. ✔ Metal & plastic nameplates ✔ Durable materials ✔ Flexible MOQ. If you have equipment projects requiring nameplates, we'd be glad to support.

    若為 NA-PLASTIC (訴求：Development):
    - 署名：Jason
    - 核心模板：We support product teams with custom plastic parts (injection molding / enclosures) from Taiwan. ✔ Prototype to low-volume ✔ Flexible tooling ✔ Fast sampling and iteration support. If you have new product projects, we'd be happy to assist.

    【撰寫指示】：
    1. 信件主旨（Subject）必須具有吸引力，並包含客戶的公司名稱。
    2. 第一段直接結合對方的【核心關鍵字】與【業務內容】進行破冰 (Personalization)，讓客戶感受到我們有深入了解他們的特定需求。
    3. 中段無縫銜接指定的【核心模板】內容。
    4. 信件結尾必須包含 Slogan: "Corelink From Concept to Connect" 以及對應的 BD 署名。

    請以 JSON 輸出：{{"Subject": "...", "Body": "..."}}
    (注意 Body 段落需保留換行符號 \\n)
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful B2B sales assistant that strictly outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API (Email): {e}")
        return {"Subject": "Error generating email", "Body": str(e)}
