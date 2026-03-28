import React, { useState } from 'react';
import { 
  FlaskConical, 
  Search, 
  Cpu, 
  Zap, 
  CheckCircle2, 
  AlertCircle, 
  Play, 
  Timer,
  Network,
  Code2
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { testStrategy } from '../services/api';

const CrawlerResearch: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [keyword, setKeyword] = useState('cnc machining');
  const [strategy, setStrategy] = useState('thomasnet');
  const [result, setResult] = useState<any>(null);

  const handleTest = async () => {
    if (!keyword.trim()) return toast.error("請輸入關鍵字");
    
    setLoading(true);
    setResult(null);
    const id = toast.loading(`正在調研策略: ${strategy}...`);
    
    try {
      const resp = await testStrategy({
        keyword,
        strategy,
        market: 'US',
        pages: 1
      });
      
      if (resp.ok) {
        const data = await resp.json();
        setResult(data.result);
        if (data.result.success) {
          toast.success("策略調研完成", { id });
        } else {
          toast.error(`策略執行失敗: ${data.result.error}`, { id });
        }
      } else {
        toast.error("API 連線失敗", { id });
      }
    } catch (e) {
      toast.error("網路錯誤", { id });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              爬蟲調研實驗室
              <span className="page-title__en">Research Bench</span>
            </h1>
            <span className="version-badge">LINKORA V3.5 RESEARCH</span>
          </div>
          <p className="page-subtitle">在隔離環境中測試與調製探勘策略，確保資料採購引擎的穩定性與高品質。</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form */}
        <div className="lg:col-span-4 space-y-6">
          <section className="card p-6 border-white/5 shadow-xl">
            <div className="flex items-center gap-2 mb-6 text-primary">
              <FlaskConical size={18} />
              <h3 className="font-bold text-sm uppercase tracking-wider">策略測試參數 (Bench Config)</h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-[11px] font-bold text-text-muted block mb-2 uppercase tracking-widest">目標關鍵字</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={14} />
                  <input 
                    type="text" 
                    className="input-field pl-10 h-10 text-sm"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="例如: cnc machining..."
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-text-muted block mb-2 uppercase tracking-widest">探勘策略 (Strategy)</label>
                <div className="grid grid-cols-1 gap-2">
                  <button 
                    onClick={() => setStrategy('thomasnet')}
                    className={`flex items-center justify-between p-3 rounded-xl border transition-all text-left ${strategy === 'thomasnet' ? 'bg-primary/10 border-primary/40 text-white' : 'bg-white/5 border-transparent text-text-muted hover:bg-white/10'}`}
                  >
                    <div className="flex items-center gap-3">
                      <Cpu size={16} className={strategy === 'thomasnet' ? 'text-primary' : ''} />
                      <div className="text-xs font-bold">Thomasnet Apify</div>
                    </div>
                    {strategy === 'thomasnet' && <CheckCircle2 size={12} className="text-primary" />}
                  </button>
                  <button 
                    onClick={() => setStrategy('yellowpages')}
                    className={`flex items-center justify-between p-3 rounded-xl border transition-all text-left ${strategy === 'yellowpages' ? 'bg-amber-500/10 border-amber-500/40 text-white' : 'bg-white/5 border-transparent text-text-muted hover:bg-white/10'}`}
                  >
                    <div className="flex items-center gap-3">
                      <Zap size={16} className={strategy === 'yellowpages' ? 'text-amber-500' : ''} />
                      <div className="text-xs font-bold">YellowPages Primary</div>
                    </div>
                    {strategy === 'yellowpages' && <CheckCircle2 size={12} className="text-amber-500" />}
                  </button>
                </div>
              </div>

              <button 
                onClick={handleTest}
                disabled={loading}
                className="btn-primary w-full py-3 mt-4 flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
              >
                {loading ? <div className="spinner w-4 h-4 border-2" /> : <><Play size={16} /> 啟動調研測試</>}
              </button>
            </div>
          </section>

          <section className="card p-5 bg-primary/5 border-primary/20">
            <div className="flex items-center gap-2 mb-3 text-primary">
              <Network size={16} />
              <h4 className="text-xs font-bold">調研模式說明</h4>
            </div>
            <p className="text-[11px] leading-relaxed text-text-muted">
              調研測試不會扣除您的正式點數，也不會將數據寫入您的客戶清單。此功能僅供確認 Apify Actor 是否正常運作、網頁結構是否變動以及數據發現率。
            </p>
          </section>
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-8 flex flex-col min-h-[500px]">
          <section className="card flex-1 p-6 border-white/5 shadow-xl flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Code2 size={18} className="text-accent-teal" />
                <h3 className="font-bold text-sm uppercase tracking-wider">即時執行日誌 (Real-time Result)</h3>
              </div>
              {result && (
                <div className={`px-3 py-1 rounded-full text-[10px] font-bold flex items-center gap-1.5 ${result.success ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                  {result.success ? <CheckCircle2 size={12}/> : <AlertCircle size={12}/>}
                  {result.success ? '策略有效' : '策略失效'}
                </div>
              )}
            </div>

            {result ? (
              <div className="space-y-6 flex-1 overflow-y-auto pr-2 custom-scrollbar">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-2 text-[10px] text-text-muted font-bold uppercase mb-1">
                      <Timer size={12} /> 執行耗時
                    </div>
                    <div className="text-xl font-black text-white">{result.execution_time} s</div>
                  </div>
                  <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-2 text-[10px] text-text-muted font-bold uppercase mb-1">
                      <Search size={12} /> 發現 Lead 數
                    </div>
                    <div className="text-xl font-black text-white">{result.count} 筆</div>
                  </div>
                </div>

                {result.error && (
                  <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
                    ERROR: {result.error}
                  </div>
                )}

                {result.leads && result.leads.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-[11px] font-bold text-text-muted uppercase tracking-widest pl-1">數據樣本 (Sample Leads)</h4>
                    {result.leads.map((lead: any, idx: number) => (
                      <div key={idx} className="p-4 rounded-xl bg-slate-800/50 border border-white/5 flex flex-col gap-1">
                        <div className="text-sm font-bold text-white">{lead.company_name}</div>
                        <div className="text-xs text-primary underline truncate">{lead.website}</div>
                        {lead.email && <div className="text-[10px] font-mono text-emerald-400 mt-1">{lead.email}</div>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center py-20 bg-white/[0.02] rounded-3xl border border-dashed border-white/5">
                <FlaskConical size={40} className="text-white/5 mb-4" />
                <p className="text-sm font-medium text-text-muted">等待策略啟動...</p>
                <p className="text-[11px] text-text-muted/60 mt-1">請在左側選擇關鍵字與模式，觀察執行狀況。</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};

export default CrawlerResearch;
