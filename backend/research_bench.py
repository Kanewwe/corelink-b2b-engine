"""
Linkora Research Bench (v3.5)
----------------------------
用於獨立測試探勘策略 (Scraping Strategies) 的模擬器。
不與私有工作區資料掛鉤，僅用於驗證數據來源可靠性。
"""

import asyncio
import time
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from logger import add_log
from scraper_utils import Timer

# ─── Strategy Interface ──────────────────────────────────────────────────────

class ScrapingStrategy:
    def __init__(self, name: str, user_id: Optional[int] = None):
        self.name = name
        self.user_id = user_id

    async def run(self, keyword: str, market: str, pages: int) -> Dict[str, Any]:
        """主入口，子類必須實現"""
        raise NotImplementedError

# ─── Thomasnet Strategy (Apify based) ────────────────────────────────────────

class ThomasnetApifyStrategy(ScrapingStrategy):
    async def run(self, keyword: str, market: str, pages: int) -> Dict[str, Any]:
        from manufacturer_miner import search_via_apify_thomasnet
        from database import SessionLocal
        
        db = SessionLocal()
        with Timer() as t:
            try:
                # 模擬運行
                results = await search_via_apify_thomasnet(
                    keyword, market, max_results=pages * 10, db=db, user_id=self.user_id
                )
                success = len(results) > 0
                return {
                    "strategy": self.name,
                    "success": success,
                    "count": len(results),
                    "execution_time": round(t.interval, 2),
                    "leads": results[:5] if results else [], # 返回前 5 筆 sample
                    "error": None if success else "Returned 0 items"
                }
            except Exception as e:
                return {
                    "strategy": self.name,
                    "success": False,
                    "count": 0,
                    "execution_time": round(t.interval, 2),
                    "error": str(e)
                }
            finally:
                db.close()

# ─── YellowPages Strategy (Apify based) ──────────────────────────────────────

class YellowPagesApifyStrategy(ScrapingStrategy):
    async def run(self, keyword: str, market: str, pages: int) -> Dict[str, Any]:
        from config_utils import get_api_key
        from database import SessionLocal
        from apify_client import ApifyClient
        
        db = SessionLocal()
        apify_token = get_api_key(db, "apify", self.user_id)
        db.close()

        if not apify_token:
            return {"strategy": self.name, "success": False, "error": "APIFY_TOKEN missing"}

        with Timer() as t:
            try:
                client = ApifyClient(apify_token)
                run_input = {
                    "searchTerms": [keyword],
                    "location": "United States" if market == "US" else market,
                    "maxResults": pages * 10
                }
                # 使用目前的 junipr/yellow-pages-scraper
                run = await asyncio.to_thread(client.actor("junipr/yellow-pages-scraper").call, run_input=run_input)
                dataset = client.dataset(run["defaultDatasetId"])
                items = dataset.list_items().items
                
                return {
                    "strategy": self.name,
                    "success": len(items) > 0,
                    "count": len(items),
                    "execution_time": round(t.interval, 2),
                    "error": None if items else "No items found"
                }
            except Exception as e:
                return {"strategy": self.name, "success": False, "error": str(e)}

# ─── Research Bench Runner ───────────────────────────────────────────────────

class ResearchBench:
    def __init__(self, user_id: Optional[int] = None):
        self.strategies = {
            "thomasnet": ThomasnetApifyStrategy("thomasnet", user_id),
            "yellowpages": YellowPagesApifyStrategy("yellowpages", user_id)
        }

    async def run_benchmark(self, keyword: str, market: str = "US", pages: int = 1) -> Dict[str, Any]:
        """同時運行多個策略並對稱比較"""
        results = {}
        for name, strategy in self.strategies.items():
            add_log(f"🔬 [Research] Testing strategy: {name} for '{keyword}'")
            results[name] = await strategy.run(keyword, market, pages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "keyword": keyword,
            "market": market,
            "pages": pages,
            "results": results
        }

# ─── CLI Entry (For developer local testing) ───────────────────────────────

if __name__ == "__main__":
    import sys
    
    async def main():
        keyword = sys.argv[1] if len(sys.argv) > 1 else "cnc machining"
        bench = ResearchBench()
        res = await bench.run_benchmark(keyword)
        
        import json
        print(json.dumps(res, indent=2, ensure_ascii=False))

    asyncio.run(main())
