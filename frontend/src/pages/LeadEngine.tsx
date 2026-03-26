import React, { useState, useEffect } from 'react';
import { getDashboardStats, getLeads, triggerScrapeSimple, generateAiKeywords } from '../services/api';
import { Users, Send, BarChart3, ShieldAlert, Cpu, Search, Sparkles, Zap, Mail, Globe } from 'lucide-react';
import { toast } from 'react-hot-toast';

const LeadEngine: React.FC = () => {
  const [kpi, setKpi] = useState({ total: 0, sentMonth: 0, openRate: '0%', bounceRate: '0%' });
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Scraper Form State
  const [market, setMarket] = useState('US');
  const [location, setLocation] = useState('');
  const [keywordInput, setKeywordInput] = useState('');
  const [activeKeywords, setActiveKeywords] = useState<string[]>([]);
  const [suggestedKeywords, setSuggestedKeywords] = useState<string[]>([]);
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

  const addKeyword = (k: string) => {
    const trimmed = k.trim();
    if (trimmed && !activeKeywords.includes(trimmed)) {
      setActiveKeywords([...activeKeywords, trimmed]);
      setKeywordInput('');
    }
  };

  const removeKeyword = (k: string) => {
    setActiveKeywords(activeKeywords.filter(item => item !== k));
  };

  const handleScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalKeywords = [...activeKeywords];
    if (keywordInput.trim()) finalKeywords.push(keywordInput.trim());

    if (finalKeywords.length === 0) {
      toast.error("請輸入產業關鍵字");
      return;
    }
    
    setIsMining(true);
    setMiningStatus('探勘任務已啟動！請查看系統日誌隨時查看進度。');
    const loadingToast = toast.loading("正在啟動 AI 探勘引擎...");
    
    try {
      const resp = await triggerScrapeSimple({
        market,
        pages: parseInt(pages),
        keyword: finalKeywords.join(', '),
        location,
        miner_mode: minerMode,
        email_strategy: emailStrategy
      });
      
      if (resp.ok) {
        toast.success("探勘背景任務已成功啟動！", { id: loadingToast });
        setActiveKeywords([]);
        setKeywordInput('');
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
    const base = keywordInput || activeKeywords[0];
    if (!base) {
      toast.error("請先輸入一個基礎關鍵字");
      return;
    }
    const loadingToast = toast.loading("AI 正在擴展相關關鍵字...");
    try {
      const resp = await generateAiKeywords(base);
      const data = await resp.json();
      if (data.success && data.keywords && data.keywords.length > 0) {
        toast.success(`AI 已為您找到 ${data.keywords.length} 個建議`, { id: loadingToast });
        setSuggestedKeywords(data.keywords);
      } else {
        toast.error("AI 關鍵字生成失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("AI 服務暫時不可用", { id: loadingToast });
    }
  };

  if (loading && leads.length === 0) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <span>載入中...</span>
      </div>
    );
  }

  const kpiData = [
    { label: '客戶總數',  value: kpi.total,      note: '無上限',    iconColor: 'var(--color-primary)',  bg: 'rgba(91,127,255,0.15)',  icon: Users },
    { label: '本月寄信',  value: kpi.sentMonth,  note: '無上限',    iconColor: 'var(--color-accent-teal)', bg: 'rgba(78,205,196,0.15)', icon: Send },
    { label: '開信率',    value: kpi.openRate,   note: '統計開發中', iconColor: 'var(--color-warning)',  bg: 'rgba(245,158,11,0.15)', icon: BarChart3 },
    { label: '退信率',    value: kpi.bounceRate, note: '統計開發中', iconColor: 'var(--color-danger)',   bg: 'rgba(239,68,68,0.15)',  icon: ShieldAlert },
  ];

  return (
    <div className="page-wrapper">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              精準開發雷達
              <span className="page-title__en">Precision Radar</span>
            </h1>
            <span className="version-badge">LINKORA V2</span>
          </div>
          <p className="page-subtitle">AI 驅動的全自動 B2B 客戶探勘引擎，精準發現潛在採購商。</p>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      <div className="stats-grid">
        {kpiData.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="stat-card">
              <div className="stat-card__icon" style={{ background: card.bg }}>
                <Icon size={20} style={{ color: card.iconColor }} />
              </div>
              <div>
                <div className="stat-card__value" style={{ color: card.iconColor }}>{card.value}</div>
                <div className="stat-card__label">{card.label}</div>
                <div className="stat-card__note">{card.note}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1 min-h-[500px] lead-engine-grid">
        {/* Left Column: Miner Form */}
        <section className="card" style={{ overflowY: 'auto' }}>
          <div className="card__header">
            <h3 className="card__title">🕷️ 全自動化探勘引擎 (Auto-Miner)</h3>
          </div>
          <p className="card__subtitle" style={{ marginBottom: 20 }}>直接爬取黃頁網站，自動發現採購/負責人 Email</p>

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
                    className="input-field pl-10 appearance-none"
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
                  className="input-field appearance-none"
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
                className="input-field"
                value={location} onChange={e => setLocation(e.target.value)}
              />
            </div>
            
            <div className="space-y-3">
              <label className="block text-[11px] font-bold text-text-muted uppercase tracking-widest mb-2 ml-1 flex items-center justify-between">
                <span>產業關鍵字 (Keyword Chips)</span>
                <span className="text-[9px] text-primary underline decoration-primary/30">支援多關鍵字探勘</span>
              </label>
              
              {/* Active Keywords */}
              <div className="flex flex-wrap gap-2 mb-2">
                {activeKeywords.map((k, idx) => (
                  <div key={idx} className="bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-bold border border-primary/30 flex items-center gap-2 animate-in zoom-in duration-200">
                    {k}
                    <button type="button" onClick={() => removeKeyword(k)} className="hover:text-white transition-colors">×</button>
                  </div>
                ))}
              </div>

              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input 
                    type="text" placeholder="輸入關鍵字後按 Enter..."
                    className="input-field"
                    value={keywordInput} 
                    onChange={e => setKeywordInput(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addKeyword(keywordInput);
                      }
                    }}
                  />
                </div>
                <button 
                  type="button" 
                  onClick={handleAiKeywords}
                  className="bg-primary/10 hover:bg-primary/20 text-primary px-4 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 border border-primary/20 shadow-lg shadow-primary/5"
                >
                  <Sparkles className="w-3.5 h-3.5" /> AI 聯想
                </button>
              </div>

              {/* AI Suggestions */}
              {suggestedKeywords.length > 0 && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3 animate-in fade-in slide-in-from-top-2">
                  <div className="text-[10px] text-text-muted font-bold uppercase mb-2 flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-warning" /> AI 選項建議 (點選加入):
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {suggestedKeywords.map((sk, idx) => (
                      <button 
                        key={idx} 
                        type="button"
                        onClick={() => {
                          addKeyword(sk);
                          setSuggestedKeywords(suggestedKeywords.filter(k => k !== sk));
                        }}
                        className="bg-white/5 hover:bg-primary/20 hover:text-white px-2.5 py-1 rounded-lg text-[11px] text-text-muted border border-white/10 transition-all"
                      >
                        + {sk}
                      </button>
                    ))}
                  </div>
                </div>
              )}
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
        <section className="card" style={{ display: 'flex', flexDirection: 'column', height: 600 }}>
          <div className="card__header">
            <h3 className="card__title">
              客戶列表
              <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)' }}>{leads.length} 筆</span>
            </h3>
            <div className="form-input-wrapper" style={{ width: 160 }}>
              <Search size={13} className="input-icon" />
              <input
                type="text" placeholder="搜尋公司..."
                value={search} onChange={e => setSearch(e.target.value)}
                className="form-input" style={{ padding: '7px 10px 7px 32px', fontSize: 12 }}
              />
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {leads.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state__icon"><Search size={40} style={{ opacity: 0.3 }} /></div>
                <p className="empty-state__title">尚無客戶資料</p>
                <p className="empty-state__desc">在左側設定條件後開始探勘</p>
              </div>
            ) : (
              leads
                .filter((l: any) => !search || l.company_name?.toLowerCase().includes(search.toLowerCase()))
                .map((lead: any, idx: number) => (
                  <div key={idx} className="card" style={{ padding: '12px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-text-primary)' }}>{lead.company_name}</div>
                        {lead.global_id ? (
                          <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 4, background: 'var(--color-primary-glow)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 700 }}>
                            <Globe size={10} /> GLOBAL SYNC
                          </span>
                        ) : (
                          <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 4, background: 'var(--color-accent-teal-glow)', color: 'var(--color-accent-teal)', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 700 }}>
                            <Zap size={10} /> LIVE SCRAPE
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace', marginTop: 2 }}>
                        {lead.contact_email || lead.email || lead.email_candidates || '無聯絡信箱'}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button className="btn-icon-sm" title="查看詳情"><Search size={13} /></button>
                      <button className="btn-icon-sm" title="立即寄信" style={{ color: 'var(--color-primary)', borderColor: 'rgba(91,127,255,0.3)' }}><Send size={13} /></button>
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
