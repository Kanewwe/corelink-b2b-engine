import { getDashboardStats, getLeads, triggerScrapeSimple, generateAiKeywords } from '../services/api';
import { Users, Send, BarChart3, ShieldAlert, Cpu, Search, Sparkles, Zap, ShieldCheck, Mail, Globe } from 'lucide-react';
import { toast } from 'react-hot-toast';

const LeadEngine: React.FC = () => {
  const [kpi, setKpi] = useState({ total: 0, sentMonth: 0, openRate: '0%', bounceRate: '0%' });
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Scraper Form State
  const [market, setMarket] = useState('US');
  const [location, setLocation] = useState('');
  const [keyword, setKeyword] = useState('');
  const [pages, setPages] = useState('3');
  const [minerMode, setMinerMode] = useState('manufacturer');
  const [emailStrategy, setEmailStrategy] = useState<'free' | 'hunter'>('free');
  const [miningStatus, setMiningStatus] = useState<string | null>(null);
  const [isMining, setIsMining] = useState(false);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [statsResp, leadsResp] = await Promise.all([
        getDashboardStats(),
        getLeads()
      ]);
      
      if (statsResp.ok) {
        const stats = await statsResp.json();
        setKpi({
          total: stats.total_leads || 0,
          sentMonth: stats.sent_month || 0,
          openRate: stats.open_rate || '0%',
          bounceRate: stats.bounce_rate || '0%'
        });
      }
      
      if (leadsResp.ok) {
        setLeads(await leadsResp.json());
      }
    } catch (e) {
      console.error("Failed to fetch dashboard data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword) {
      toast.error("請輸入產業關鍵字");
      return;
    }
    
    setIsMining(true);
    setMiningStatus('探勘任務已啟動！請查看系統日誌或稍後重整列表。');
    const loadingToast = toast.loading("正在啟動 AI 探勘引擎...");
    
    try {
      const resp = await triggerScrapeSimple({
        market,
        pages: parseInt(pages),
        keyword,
        location,
        miner_mode: minerMode,
        email_strategy: emailStrategy
      });
      
      if (resp.ok) {
        toast.success("探勘背景任務已成功啟動！", { id: loadingToast });
        // Optionally clear form or keep for next search
      } else {
        const err = await resp.json();
        toast.error(err.detail || "啟動失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("網路連線錯誤", { id: loadingToast });
    } finally {
      setIsMining(false);
    }
  };

  const handleAiKeywords = async () => {
    if (!keyword) {
      toast.error("請先輸入一個基礎關鍵字");
      return;
    }
    const loadingToast = toast.loading("AI 正在擴展相關關鍵字...");
    try {
      const resp = await generateAiKeywords(keyword);
      const data = await resp.json();
      if (data.success && data.keywords && data.keywords.length > 0) {
        toast.success(`AI 已為您找到 ${data.keywords.length} 個相關關鍵字`, { id: loadingToast });
        setKeyword(data.keywords[0]); // 取第一個最相關的
      } else {
        toast.error("AI 關鍵字生成失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("AI 服務暫時不可用", { id: loadingToast });
    }
  };

  if (loading && leads.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-text-muted">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mr-3"></div>
        載入中...
      </div>
    );
  }

  const kpiData = [
    { label: '客戶總數', value: kpi.total, sub: '無上限', color: 'text-primary', bg: 'bg-primary/10', icon: Users },
    { label: '本月寄信', value: kpi.sentMonth, sub: '無上限', color: 'text-accent', bg: 'bg-accent/10', icon: Send },
    { label: '開信率', value: kpi.openRate, sub: '統計開發中', color: 'text-warning', bg: 'bg-warning/10', icon: BarChart3 },
    { label: '退信率', value: kpi.bounceRate, sub: '統計開發中', color: 'text-error', bg: 'bg-error/10', icon: ShieldAlert },
  ];

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="glass-panel p-4 flex items-center gap-4 hover:bg-white/[0.03] transition-all border border-white/5 group">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${card.bg} ${card.color} group-hover:scale-110 transition-transform`}>
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white leading-none mb-1">{card.value}</div>
                <div className="text-[11px] text-text-muted font-medium">{card.label}</div>
                <div className="text-[9px] text-text-muted/50 mt-1 uppercase tracking-tighter">{card.sub}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-2 gap-6 flex-1 min-h-[500px]">
        {/* Left Column: Miner Form */}
        <section className="glass-panel p-6 overflow-y-auto">
          <h3 className="text-xl font-semibold mb-2">🕷️ 全自動化探勘引擎 (Auto-Miner)</h3>
          <p className="text-sm text-text-muted mb-6">直接爬取黃頁網站，自動發現採購/負責人 Email</p>

          <form onSubmit={handleScrape} className="flex flex-col gap-5">
            <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl">
              <div className="text-[11px] font-bold text-emerald-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                <Mail className="w-3.5 h-3.5" /> Email 發現策略 (Discovery)
              </div>
              <div className="flex gap-4">
                <label className="flex-1 flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer transition-colors group">
                  <input 
                    type="radio" name="email-strategy" value="free" 
                    checked={emailStrategy === 'free'} onChange={() => setEmailStrategy('free')}
                    className="accent-emerald-500"
                  />
                  <div className="flex items-center gap-2">
                    <span className="bg-emerald-500/10 text-emerald-500 text-[10px] px-1.5 py-0.5 rounded border border-emerald-500/20 font-bold">FREE</span>
                    <span className="text-xs text-text-muted group-hover:text-white transition-colors">免費模式</span>
                  </div>
                </label>
                <label className="flex-1 flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer transition-colors group">
                  <input 
                    type="radio" name="email-strategy" value="hunter" 
                    checked={emailStrategy === 'hunter'} onChange={() => setEmailStrategy('hunter')}
                    className="accent-warning"
                  />
                  <div className="flex items-center gap-2">
                    <Zap className="w-3 h-3 text-warning fill-warning" />
                    <span className="text-xs text-text-muted group-hover:text-white transition-colors">Hunter.io</span>
                  </div>
                </label>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-bold text-text-muted uppercase tracking-widest mb-2 ml-1">目標市場 (Market)</label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <select 
                    className="w-full pl-10 pr-3 py-2.5 bg-black/40 border border-white/10 rounded-xl text-sm text-white focus:border-primary/50 outline-none transition-all appearance-none"
                    value={market} onChange={e => setMarket(e.target.value)}
                  >
                    <option value="US">美國 (US)</option>
                    <option value="EU">歐洲 (EU)</option>
                    <option value="TW">台灣 (TW)</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-[11px] font-bold text-text-muted uppercase tracking-widest mb-2 ml-1">爬取深度 (Pages)</label>
                <select 
                  className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-xl text-sm text-white focus:border-primary/50 outline-none transition-all"
                  value={pages} onChange={e => setPages(e.target.value)}
                >
                  <option value="1">1 頁 (10筆)</option>
                  <option value="3">3 頁 (30筆)</option>
                  <option value="5">5 頁 (50筆)</option>
                  <option value="10">10 頁 (100筆)</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-[11px] font-bold text-text-muted uppercase tracking-widest mb-2 ml-1">探勘所在地區 (Location)</label>
              <input 
                type="text" placeholder="例如: California, Seattle..."
                className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-sm text-white focus:border-primary/50 outline-none transition-all"
                value={location} onChange={e => setLocation(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-[11px] font-bold text-text-muted uppercase tracking-widest mb-2 ml-1">產業關鍵字 (Keyword) *</label>
              <div className="flex gap-2">
                <input 
                  type="text" required placeholder="例如: Plastic Manufacturer"
                  className="flex-1 px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-sm text-white focus:border-primary/50 outline-none transition-all"
                  value={keyword} onChange={e => setKeyword(e.target.value)}
                />
                <button 
                  type="button" 
                  onClick={handleAiKeywords}
                  className="bg-primary/10 hover:bg-primary/20 text-primary px-4 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 border border-primary/20 shadow-lg shadow-primary/5"
                >
                  <Sparkles className="w-3.5 h-3.5" /> AI 建議
                </button>
              </div>
            </div>

            <div className="p-4 bg-primary/5 border border-primary/10 rounded-xl">
              <div className="text-[11px] font-bold text-primary uppercase tracking-widest mb-4 flex items-center gap-2">
                <Search className="w-3.5 h-3.5" /> 探勘模式 (Mining Mode)
              </div>
              <div className="flex flex-col gap-3">
                <label className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer border transition-all ${minerMode === 'manufacturer' ? 'bg-primary/10 border-primary/30' : 'bg-white/5 border-transparent hover:bg-white/10'}`}>
                  <input 
                    type="radio" name="miner-mode" value="manufacturer" 
                    checked={minerMode === 'manufacturer'} onChange={e => setMinerMode(e.target.value)}
                    className="mt-1 accent-primary"
                  />
                  <div>
                    <div className="text-xs font-bold text-white flex items-center gap-2">
                      製造商模式 (推薦) <span className="bg-primary/20 text-primary text-[9px] px-1.5 py-0.5 rounded font-black italic">PRO</span>
                    </div>
                    <div className="text-[10px] text-text-muted mt-1 leading-relaxed">搜尋 B2B 製造商目錄 (Thomasnet / Google)。適合工業品、OEM、零件及原料供應商。</div>
                  </div>
                </label>
                <label className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer border transition-all ${minerMode === 'yellowpages' ? 'bg-warning/10 border-warning/30' : 'bg-white/5 border-transparent hover:bg-white/10'}`}>
                  <input 
                    type="radio" name="miner-mode" value="yellowpages" 
                    checked={minerMode === 'yellowpages'} onChange={e => setMinerMode(e.target.value)}
                    className="mt-1 accent-warning"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">黃頁模式 (原版)</div>
                    <div className="text-[10px] text-text-muted mt-1 leading-relaxed">搜尋 Yellowpages / Yelp。適合本地服務業、維修店、各類 B2C 零售商。</div>
                  </div>
                </label>
              </div>
            </div>

            {miningStatus && (
              <div className="text-[11px] p-3 rounded-xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-medium animate-in fade-in slide-in-from-top-1">
                {miningStatus}
              </div>
            )}

            <button 
              type="submit" 
              disabled={isMining}
              className="w-full flex justify-center items-center py-4 bg-gradient-to-br from-primary to-primary-dark hover:scale-[1.02] active:scale-[0.98] rounded-2xl font-black text-white shadow-xl shadow-primary/30 transition-all disabled:opacity-50"
            >
              {isMining ? (
                 <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  <Cpu className="w-5 h-5 mr-3" /> ⚡ 立即啟動 AI 自動探勘
                </>
              )}
            </button>
          </form>
        </section>

        {/* Right Column: Leads Table */}
        <section className="glass-panel p-6 flex flex-col h-[600px]">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold">客戶列表 <span className="text-sm font-normal text-text-muted">{leads.length} 筆</span></h3>
            <div className="flex gap-2">
              <input 
                type="text" placeholder="搜尋公司..."
                value={search} onChange={e => setSearch(e.target.value)}
                className="px-3 py-1.5 bg-black/25 border border-glass-border rounded-lg text-sm w-32 focus:w-48 transition-all outline-none focus:border-primary"
              />
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-3">
            {leads.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-text-muted">
                <Search className="w-12 h-12 mb-4 opacity-20" />
                <div className="text-lg mb-2">尚無客戶資料</div>
                <div className="text-sm">在左側設定條件後開始探勘</div>
              </div>
            ) : (
              leads.map((lead: any, idx: number) => (
                <div key={idx} className="p-4 bg-white/[0.02] border border-white/5 rounded-xl hover:bg-white/[0.05] hover:-translate-y-0.5 transition-all group flex justify-between items-center">
                  <div>
                    <div className="font-bold text-white text-sm group-hover:text-primary transition-colors">{lead.company_name}</div>
                    <div className="text-[10px] text-text-muted font-mono mt-1 opacity-70">{lead.email || lead.email_candidates || '無聯絡信箱'}</div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                     <button title="查看詳情" className="p-1.5 hover:bg-white/10 rounded-md text-text-muted hover:text-white transition-colors">
                        <Search className="w-3.5 h-3.5" />
                     </button>
                     <button title="立即寄信" className="p-1.5 hover:bg-primary/20 rounded-md text-primary hover:scale-110 transition-all">
                        <Send className="w-3.5 h-3.5" />
                     </button>
                     <button title="刪除客戶" className="p-1.5 hover:bg-error/20 rounded-md text-error/60 hover:text-error transition-colors">
                        <ShieldAlert className="w-3.5 h-3.5" />
                     </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default LeadEngine;
