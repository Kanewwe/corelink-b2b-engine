import React, { useState, useEffect } from 'react';
import { getDashboardStats, getLeads } from '../services/api';
import { Users, Send, BarChart3, ShieldAlert, Cpu, Search, Sparkles } from 'lucide-react';

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
  const [miningStatus, setMiningStatus] = useState<string | null>(null);

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
    setMiningStatus('探勘任務已啟動！請查看下方系統日誌。');
    // Scraper implementation logic...
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
            <div>
              <label className="block text-sm text-text-muted mb-2">目標市場 (Target Market)</label>
              <select 
                className="w-full p-3 bg-black/25 border border-glass-border rounded-lg text-white"
                value={market} onChange={e => setMarket(e.target.value)}
              >
                <option value="US">美國 (US) - Yellowpages, Yelp</option>
                <option value="EU">歐洲 (EU) - Yell, Europages</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-text-muted mb-2">目標地區 (Location)</label>
              <input 
                type="text" placeholder="例如: California, New York, Texas"
                className="w-full p-3 bg-black/25 border border-glass-border rounded-lg text-white"
                value={location} onChange={e => setLocation(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm text-text-muted mb-2">產業關鍵字 (Industry Keyword)</label>
              <div className="flex gap-2">
                <input 
                  type="text" required placeholder="例如: Cable Manufacturer"
                  className="flex-1 p-3 bg-black/25 border border-glass-border rounded-lg text-white"
                  value={keyword} onChange={e => setKeyword(e.target.value)}
                />
                <button type="button" className="bg-primary/20 hover:bg-primary/30 text-primary px-3 rounded-lg text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1 shrink-0 border border-primary/20">
                  <Sparkles className="w-3 h-3" /> AI 建議
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm text-text-muted mb-2">爬取頁數</label>
              <select 
                className="w-full p-3 bg-black/25 border border-glass-border rounded-lg text-white"
                value={pages} onChange={e => setPages(e.target.value)}
              >
                <option value="1">1 頁 (約 10 筆)</option>
                <option value="2">2 頁 (約 20 筆)</option>
                <option value="3">3 頁 (約 30 筆)</option>
                <option value="5">5 頁 (約 50 筆)</option>
              </select>
            </div>

            <div className="mt-2 p-4 bg-primary/10 border-l-4 border-primary rounded-lg">
              <div className="text-xs font-semibold mb-3">🏭 探勘模式 (Mining Mode)</div>
              <div className="flex flex-col gap-3">
                <label className="flex items-start gap-2 cursor-pointer">
                  <input 
                    type="radio" name="miner-mode" value="manufacturer" 
                    checked={minerMode === 'manufacturer'} onChange={e => setMinerMode(e.target.value)}
                    className="mt-1 accent-primary"
                  />
                  <div>
                    <div className="text-xs font-semibold text-primary">製造商模式 (推薦)</div>
                    <div className="text-[11px] text-text-muted">搜尋 B2B 製造商目錄。適合工業品、OEM、零件及原料供應商。</div>
                  </div>
                </label>
                <label className="flex items-start gap-2 cursor-pointer">
                  <input 
                    type="radio" name="miner-mode" value="yellowpages" 
                    checked={minerMode === 'yellowpages'} onChange={e => setMinerMode(e.target.value)}
                    className="mt-1 accent-warning"
                  />
                  <div>
                    <div className="text-xs font-semibold text-warning">黃頁模式 (原版)</div>
                    <div className="text-[11px] text-text-muted">搜尋 Yellowpages / Yelp。適合本地服務業、維修店、零售商。</div>
                  </div>
                </label>
              </div>
            </div>

            {miningStatus && (
              <div className="text-sm p-3 rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                {miningStatus}
              </div>
            )}

            <button type="submit" className="btn-primary mt-2 flex justify-center items-center py-3 font-bold tracking-wide">
              <Cpu className="w-4 h-4 mr-2" /> 開始自動探勘
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
