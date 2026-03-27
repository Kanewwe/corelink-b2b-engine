import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  getDashboardStats, 
  getLeads, 
  triggerScrapeSimple, 
  generateAiKeywords, 
  updateLead, 
  proposeCorrection,
  scoreLeads,
  generateLeadBrief
} from '../services/api';
import { 
  Users, Send, BarChart3, ShieldAlert, Cpu, Search, Sparkles, 
  Zap, Mail, Globe, Edit3, Save, X, User, Star, Brain, TrendingUp
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Lead {
  id: number;
  global_id?: number;
  company_name: string;
  display_name: string;
  contact_email?: string;
  display_email?: string;
  domain?: string;
  personal_notes?: string;
  override_name?: string;
  override_email?: string;
  custom_tags?: string[];
  is_overridden?: boolean;
  scrape_location?: string;
  // v3.2: AI 評分
  ai_score?: number;
  ai_score_tags?: string;
  ai_brief?: string;
  ai_suggestions?: string;
}

// ── Lead Detail Drawer Component ──
interface LeadDetailDrawerProps {
  lead: Lead;
  onClose: () => void;
  onUpdate: () => void;
}

const LeadDetailDrawer: React.FC<LeadDetailDrawerProps> = ({ lead, onClose, onUpdate }: LeadDetailDrawerProps) => {
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    override_name: lead.override_name || '',
    override_email: lead.override_email || '',
    personal_notes: lead.personal_notes || '',
    custom_tags: lead.custom_tags || []
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const resp = await updateLead(lead.id, formData);
      if (resp.ok) {
        toast.success("個人覆寫已儲存");
        setEditMode(false);
        onUpdate();
      }
    } catch (e) {
      toast.error("儲存失敗");
    } finally {
      setSaving(false);
    }
  };

  const handlePropose = async (field: string, value: string) => {
    if (!lead.global_id) {
      toast.error("此 Lead 尚未與全域池連結，無法提出建議");
      return;
    }
    const loadingToast = toast.loading("正在送出全域修正建議...");
    try {
      const resp = await proposeCorrection({
        global_id: lead.global_id,
        field_name: field,
        suggested_value: value
      });
      if (resp.ok) {
        toast.success("建議已送出，待管理員審核", { id: loadingToast });
      }
    } catch (e) {
      toast.error("送出建議失敗", { id: loadingToast });
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-[450px] bg-slate-900 border-l border-white/10 shadow-2xl z-50 animate-in slide-in-from-right duration-300 flex flex-col">
      <div className="p-6 border-b border-white/10 flex justify-between items-center bg-slate-800/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
            <User size={20} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{lead.display_name}</h3>
            <p className="text-xs text-text-muted">Lead ID: #{lead.id}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors text-text-muted">
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Layer Distinction Banner */}
        <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 flex items-start gap-3">
          <Sparkles size={16} className="text-primary mt-1" />
          <div className="text-xs leading-relaxed">
            <span className="font-bold text-primary block mb-1">v3.0 雙層架構說明</span>
            您可以針對此 Lead 進行<b>個人覆寫 (Workspace Overlay)</b>，這僅會影響您的視圖。如果您發現全域事實有誤，請點擊「建議全域修正」。
          </div>
        </div>

        {/* Basic Info */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-text-muted uppercase tracking-wider">資訊屬性</h4>
            <button 
              onClick={() => setEditMode(!editMode)}
              className="text-xs flex items-center gap-1.5 text-primary hover:underline"
            >
              {editMode ? <><Save size={12}/> 取消</> : <><Edit3 size={12}/> 編輯個人參數</>}
            </button>
          </div>

          <div className="space-y-5">
            {/* Company Name */}
            <div>
              <label className="text-[11px] font-bold text-text-muted block mb-1.5">公司名稱</label>
              {editMode ? (
                <div className="space-y-2">
                  <input 
                    type="text" className="input-field py-1.5 text-sm"
                    value={formData.override_name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, override_name: e.target.value})}
                    placeholder={lead.company_name}
                  />
                  <div className="flex justify-end">
                    <button 
                      onClick={() => handlePropose('company_name', formData.override_name || lead.company_name)}
                      className="text-[10px] text-accent-teal hover:underline flex items-center gap-1"
                    >
                      <Globe size={10} /> 建議作為全域事實
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-white">{lead.display_name}</div>
                  {lead.is_overridden && <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20">已覆寫</span>}
                </div>
              )}
            </div>

            {/* Email */}
            <div>
              <label className="text-[11px] font-bold text-text-muted block mb-1.5">聯絡信箱 (Email)</label>
              {editMode ? (
                <input 
                  type="text" className="input-field py-1.5 text-sm"
                  value={formData.override_email}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, override_email: e.target.value})}
                  placeholder={lead.contact_email}
                />
              ) : (
                <div className="text-sm font-mono text-emerald-400">{lead.display_email || '尚未探勘'}</div>
              )}
            </div>

            {/* Notes */}
            <div>
              <label className="text-[11px] font-bold text-text-muted block mb-1.5">私人筆記 (Notes)</label>
              {editMode ? (
                <textarea 
                  className="input-field min-h-[100px] py-2 text-sm"
                  value={formData.personal_notes}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({...formData, personal_notes: e.target.value})}
                  placeholder="只有您看得到的備註..."
                />
              ) : (
                <div className="text-sm text-text-muted italic bg-white/5 p-3 rounded-lg border border-white/5 min-h-[60px]">
                  {lead.personal_notes || '尚無筆記'}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sync Info */}
        <div className="pt-6 border-t border-white/5">
          <div className="flex items-center gap-2 mb-4">
            <Globe size={14} className="text-text-muted" />
            <h4 className="text-sm font-bold text-text-muted uppercase tracking-wider">共享資料層 (Canonical Facts)</h4>
          </div>
          <div className="grid grid-cols-2 gap-4 text-[11px]">
            <div className="p-3 rounded-lg bg-white/5 border border-white/5">
              <div className="text-text-muted mb-1">網域 (Domain)</div>
              <div className="text-white font-mono">{lead.domain || 'N/A'}</div>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/5">
              <div className="text-text-muted mb-1">探勘來源 (Source)</div>
              <div className="text-white">{lead.scrape_location || 'Manual'}</div>
            </div>
          </div>
        </div>
      </div>

      {editMode && (
        <div className="p-6 border-t border-white/10 bg-slate-800/80 flex gap-3">
          <button 
            onClick={handleSave}
            disabled={saving}
            className="flex-1 bg-primary py-2.5 rounded-xl text-sm font-bold text-white hover:scale-[1.02] transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
          >
            {saving ? <div className="spinner w-4 h-4 border-2" /> : <><Save size={16}/> 儲存私有變動</>}
          </button>
          <button 
            onClick={() => setEditMode(false)}
            className="px-6 py-2.5 rounded-xl border border-white/10 text-sm font-bold text-text-muted hover:bg-white/5 transition-all"
          >
            取消
          </button>
        </div>
      )}
    </div>
  );
};

const LeadEngine: React.FC = () => {
  const [kpi, setKpi] = useState({ total: 0, sentMonth: 0, openRate: '0%', bounceRate: '0%' });
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [scoring, setScoring] = useState(false); // v3.2
  
  // Scraper Form State
  const [market, setMarket] = useState('US');
  const [location, setLocation] = useState('');
  const [keywordInput, setKeywordInput] = useState('');
  const [activeKeywords, setActiveKeywords] = useState<string[]>([]);
  const [pages, setPages] = useState('3');
  const [minerMode, setMinerMode] = useState('manufacturer');
  const [emailStrategy, setEmailStrategy] = useState<'free' | 'hunter'>('free');
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
        const result = await resp.json();
        // 使用後端傳回的精確訊息 (包含即時恢復與背景進度)
        toast.success(result.message || "探勘背景任務已啟動！", { id: loadingToast, duration: 6000 });
        
        setActiveKeywords([]);
        setKeywordInput('');
        fetchDashboardData();
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
        setActiveKeywords([...activeKeywords, ...data.keywords].slice(0, 10)); // Auto-add first 10
      } else {
        toast.error("AI 關鍵字生成失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("AI 服務暫時不可用", { id: loadingToast });
    }
  };

  // v3.2: AI 評分
  const handleAiScore = async () => {
    if (leads.length === 0) {
      toast.error("尚無 Leads 可評分");
      return;
    }
    setScoring(true);
    const loadingToast = toast.loading("AI 正在評分所有 Leads...");
    try {
      const resp = await scoreLeads();
      const data = await resp.json();
      if (data.success) {
        toast.success(`評分完成！共 ${data.count} 筆`, { id: loadingToast });
        if (data.results) {
          setLeads(prev => prev.map(lead => {
            const scored = data.results.find((r: any) => r.id === lead.id);
            if (scored) {
              return { ...lead, ai_score: scored.score, ai_score_tags: JSON.stringify(scored.tags) };
            }
            return lead;
          }));
        }
      } else {
        toast.error("評分失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("評分服務暫時不可用", { id: loadingToast });
    } finally {
      setScoring(false);
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
    <div className="page-wrapper relative overflow-hidden">
      
      {/* ── Detail Drawer ── */}
      {selectedLead && (
        <>
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 animate-in fade-in" onClick={() => setSelectedLead(null)} />
          <LeadDetailDrawer 
            lead={selectedLead} 
            onClose={() => setSelectedLead(null)} 
            onUpdate={fetchDashboardData}
          />
        </>
      )}

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              精準開發雷達
              <span className="page-title__en">Precision Radar</span>
            </h1>
            <span className="version-badge">LINKORA V3.2 (AI Intelligence)</span>
          </div>
          <p className="page-subtitle">AI 驅動的全自動 B2B 客戶探勘引擎，精準發現潛在採購商並實現情報共享。</p>
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

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 lead-engine-grid">
        {/* Left Column: Miner Form */}
        <section className="card lg:col-span-5 h-fit shadow-xl border-white/5">
          <div className="card__header">
            <h3 className="card__title">🕷️ 全自動化探勘引擎 (Auto-Miner)</h3>
          </div>

          <form onSubmit={handleScrape} className="flex flex-col gap-5 mt-4">
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
                    value={market} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMarket(e.target.value)}
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
                  value={pages} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setPages(e.target.value)}
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
                value={location} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocation(e.target.value)}
              />
            </div>
            
            <div className="space-y-3">
              <label className="block text-[11px] font-bold text-text-muted uppercase tracking-widest mb-2 ml-1 flex items-center justify-between">
                <span>產業關鍵字 (Keyword Chips)</span>
                <span className="text-[9px] text-primary underline decoration-primary/30">支援多關鍵字探勘</span>
              </label>
              
              <div className="flex flex-wrap gap-2 mb-2">
                {activeKeywords.map((k, idx) => (
                  <div key={idx} className="bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-bold border border-primary/30 flex items-center gap-2">
                    {k}
                    <button type="button" onClick={() => removeKeyword(k)} className="hover:text-white transition-colors">×</button>
                  </div>
                ))}
              </div>

              <div className="flex gap-2">
                <input 
                  type="text" placeholder="輸入關鍵字後按 Enter..."
                  className="input-field flex-1"
                  value={keywordInput} 
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setKeywordInput(e.target.value)}
                  onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addKeyword(keywordInput);
                    }
                  }}
                />
                <button 
                  type="button" 
                  onClick={handleAiKeywords}
                  className="btn-outline px-4 text-xs font-bold flex items-center gap-1.5"
                >
                  <Sparkles size={14} /> AI 聯想
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
                    checked={minerMode === 'manufacturer'} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMinerMode(e.target.value)}
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
                    checked={minerMode === 'yellowpages'} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMinerMode(e.target.value)}
                    className="mt-1 accent-warning"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">黃頁模式 (原版)</div>
                    <div className="text-[10px] text-text-muted mt-1 leading-relaxed">搜尋 Yellowpages / Yelp。適合本地服務業、維修店、客路型 B2C 零售商。</div>
                  </div>
                </label>
              </div>
            </div>

            <button 
              type="submit" 
              disabled={isMining}
              className="btn-primary w-full py-4 text-base font-black shadow-lg shadow-primary/20"
            >
              {isMining ? <div className="spinner w-5 h-5 border-2" /> : <><Cpu className="w-5 h-5 mr-2" /> 立即啟動 AI 探勘</>}
            </button>
          </form>
        </section>

        {/* Right Column: Leads Table */}
        <section className="card lg:col-span-7 flex flex-col h-[750px] shadow-xl border-white/5">
          <div className="card__header">
            <h3 className="card__title">
              客戶清單 (Leads)
              <span className="text-xs font-normal text-text-muted ml-2">{leads.length} 筆資料</span>
            </h3>
            <div className="flex items-center gap-2">
              {/* v3.2: AI 評分按鈕 */}
              <button
                onClick={handleAiScore}
                disabled={scoring || leads.length === 0}
                className="btn-outline btn--sm flex items-center gap-1.5"
                style={{ borderColor: 'var(--color-primary)', color: 'var(--color-primary)' }}
                title="AI 評分"
              >
                {scoring ? <div className="spinner w-3 h-3" /> : <Brain size={13} />}
                {scoring ? '評分中...' : '✨ AI 評分'}
              </button>
              <div className="relative w-48">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text" placeholder="關鍵字搜尋..."
                  value={search} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
                  className="form-input pl-9 py-1.5 text-xs"
                />
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto mt-4 px-1 space-y-3 custom-scrollbar">
            {leads.length === 0 ? (
              <div className="empty-state py-20">
                <Search size={40} className="text-white/10 mb-4" />
                <p className="text-white font-medium">尚無探勘結果</p>
                <p className="text-xs text-text-muted mt-1">調整左側參數並啟動引擎</p>
              </div>
            ) : (
              leads
                .filter((l: Lead) => !search || l.display_name?.toLowerCase().includes(search.toLowerCase()))
                .map((lead: Lead) => (
                  <div 
                    key={lead.id} 
                    className="group card p-4 hover:border-primary/40 hover:bg-primary/[0.02] cursor-pointer transition-all flex items-center justify-between"
                    onClick={() => setSelectedLead(lead)}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${lead.is_overridden ? 'bg-amber-500/20 text-amber-500' : 'bg-slate-800 text-text-muted'}`}>
                        {lead.is_overridden ? <User size={18} /> : (lead.global_id ? <Globe size={18} /> : <Zap size={18} />)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="font-bold text-sm text-white group-hover:text-primary transition-colors">{lead.display_name}</span>
                          {lead.is_overridden && (
                            <span className="text-[9px] font-black bg-amber-500/20 text-amber-500 px-1.5 py-0.5 rounded uppercase tracking-tighter">Personal</span>
                          )}
                          {lead.global_id && (
                            <span className="text-[9px] font-black bg-primary/20 text-primary px-1.5 py-0.5 rounded uppercase tracking-tighter flex items-center gap-1">
                              <Globe size={8} /> Shared
                            </span>
                          )}
                          {/* v3.2: AI 評分顯示 */}
                          {lead.ai_score !== undefined && lead.ai_score > 0 && (
                            <span className={`text-[9px] font-black px-1.5 py-0.5 rounded flex items-center gap-1 ${
                              lead.ai_score >= 80 ? 'bg-emerald-500/20 text-emerald-400' :
                              lead.ai_score >= 60 ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-slate-500/20 text-slate-400'
                            }`}>
                              <Star size={8} /> {lead.ai_score}
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-text-muted flex items-center gap-2">
                          <span className="text-emerald-400 font-mono">{lead.display_email || 'No email discovered'}</span>
                          <span className="opacity-20">•</span>
                          <span>{lead.domain}</span>
                        </div>
                        {/* v3.2: AI 評分標籤 */}
                        {lead.ai_score_tags && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {(JSON.parse(lead.ai_score_tags) as string[]).slice(0, 3).map((tag: string, i: number) => (
                              <span key={i} className="text-[8px] bg-slate-700/60 text-slate-300 px-1 py-0.5 rounded">{tag}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="btn-icon-sm" onClick={(e: React.MouseEvent) => { e.stopPropagation(); setSelectedLead(lead); }}><Edit3 size={13}/></button>
                      <button className="btn-icon-sm" onClick={(e: React.MouseEvent) => { e.stopPropagation(); }} style={{ color: 'var(--color-primary)' }}><Send size={13}/></button>
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
