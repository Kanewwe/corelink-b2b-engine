import React, { useState, useEffect } from 'react';
import { 
  Database, Search, Globe, Tag, CheckCircle, 
  Edit, Trash2, Filter, ChevronRight, Layers,
  AlertCircle, History, RefreshCw
} from 'lucide-react';
import { 
  getAdminGlobalLeads, deleteGlobalLead, 
  getIndustryTree, getAdminProposals, 
  resolveProposal 
} from '../services/api';
import { toast } from 'react-hot-toast';

interface GlobalLead {
  id: number;
  company_name: string;
  domain: string;
  website_url?: string;
  industry_name?: string;
  industry_code?: string;
  sub_industry_name?: string;
  confidence_score: number;
  is_verified: boolean;
  contact_email?: string;
  created_at: string;
}

interface IndustryNode {
  id: number;
  code: string;
  name_en: string;
  name_zh: string;
  level: number;
  children?: IndustryNode[];
}

const Intelligence: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'leads' | 'taxonomy' | 'proposals'>('leads');
  const [leads, setLeads] = useState<GlobalLead[]>([]);
  const [loading, setLoading] = useState(false);
  const [industryTree, setIndustryTree] = useState<IndustryNode[]>([]);
  const [proposals, setProposals] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [page] = useState(0); 

  // Fetch Data
  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'leads') {
        const resp = await getAdminGlobalLeads(page * 50, 50);
        if (resp.ok) setLeads(await resp.json());
      } else if (activeTab === 'taxonomy') {
        const resp = await getIndustryTree();
        if (resp.ok) setIndustryTree(await resp.json());
      } else if (activeTab === 'proposals') {
        const resp = await getAdminProposals('Pending');
        if (resp.ok) setProposals(await resp.json());
      }
    } catch (e) {
      toast.error("載入數據失敗");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab, page]);

  const handleDeleteLead = async (id: number) => {
    if (!confirm("確定要從全域池刪除此公司嗎？這將影響所有同步此資料的用戶。")) return;
    try {
      const resp = await deleteGlobalLead(id);
      if (resp.ok) {
        toast.success("已移除全域資料");
        setLeads(leads.filter(l => l.id !== id));
      }
    } catch {
      toast.error("刪除失敗");
    }
  };

  const handleResolveProposal = async (id: number, action: 'Approved' | 'Rejected') => {
    const reason = action === 'Rejected' ? prompt("請輸入拒絕理由") : undefined;
    if (action === 'Rejected' && reason === null) return;

    try {
      const resp = await resolveProposal(id, { status: action, reason: reason || '' });
      if (resp.ok) {
        toast.success(`提案已${action === 'Approved' ? '核准' : '駁回'}`);
        setProposals(proposals.filter(p => p.id !== id));
      }
    } catch {
      toast.error("處置失敗");
    }
  };

  return (
    <div className="page-wrapper flex flex-col h-full">
      <div className="page-header shrink-0">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              情資庫管理中心
              <span className="page-title__en">Intelligence Repository</span>
            </h1>
            <span className="version-badge">V3.5 ARCHITECTURE</span>
          </div>
          <p className="page-subtitle">管理 Linkora 全域資料池（Canonical Pool）與產業標籤體系，確保數據事實的唯一性與高品質。</p>
        </div>

        <div className="flex gap-2 bg-white/5 p-1 rounded-xl border border-white/10 shrink-0">
          <button 
            onClick={() => setActiveTab('leads')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'leads' ? 'bg-primary text-white shadow-lg' : 'text-text-muted hover:text-white'}`}
          >
            <Globe size={14} /> 全域公司池
          </button>
          <button 
            onClick={() => setActiveTab('taxonomy')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'taxonomy' ? 'bg-primary text-white shadow-lg' : 'text-text-muted hover:text-white'}`}
          >
            <Tag size={14} /> 產業分類體系
          </button>
          <button 
            onClick={() => setActiveTab('proposals')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'proposals' ? 'bg-primary text-white shadow-lg relative' : 'text-text-muted hover:text-white'}`}
          >
            <History size={14} /> 修正提案
            {proposals.length > 0 && <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] flex items-center justify-center border-2 border-bg-dark">{proposals.length}</span>}
          </button>
        </div>
      </div>

      <div className="flex-1 min-h-0 mt-6 flex flex-col gap-6">
        {activeTab === 'leads' && (
          <>
            <div className="flex items-center justify-between gap-4 bg-white/5 p-4 rounded-2xl border border-white/5">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={16} />
                <input 
                  type="text" 
                  placeholder="搜尋公司名稱、網域或產業..." 
                  className="input-field pl-10 h-10 text-sm"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-3">
                <button onClick={() => fetchData()} className="btn-outline btn--sm">
                  <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> 重新整理
                </button>
                <div className="h-6 w-px bg-white/10 mx-2" />
                <div className="flex items-center gap-2 text-xs font-medium text-text-muted">
                  <Filter size={14} />
                  共 {leads.length} 筆樣本
                </div>
              </div>
            </div>

            <div className="flex-1 card p-0 overflow-hidden flex flex-col shadow-2xl border-white/5">
              <div className="overflow-x-auto flex-1 custom-scrollbar">
                <table className="w-full text-left border-collapse">
                  <thead className="sticky top-0 bg-slate-900/90 backdrop-blur-md z-10">
                    <tr className="border-b border-white/10">
                      <th className="px-6 py-4 text-[11px] font-black text-text-muted uppercase tracking-widest">公司 / 網域</th>
                      <th className="px-6 py-4 text-[11px] font-black text-text-muted uppercase tracking-widest">產業分類</th>
                      <th className="px-6 py-4 text-[11px] font-black text-text-muted uppercase tracking-widest">主權信賴度</th>
                      <th className="px-6 py-4 text-[11px] font-black text-text-muted uppercase tracking-widest">建立時間</th>
                      <th className="px-6 py-4 text-right text-[11px] font-black text-text-muted uppercase tracking-widest">維修操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {loading && leads.length === 0 ? (
                      <tr><td colSpan={5} className="py-20 text-center"><div className="spinner mx-auto mb-4" /><span className="text-sm text-text-muted">載入全域精華中...</span></td></tr>
                    ) : leads.filter(l => !search || l.company_name.toLowerCase().includes(search.toLowerCase()) || l.domain.includes(search)).map(lead => (
                      <tr key={lead.id} className="hover:bg-white/[0.02] transition-colors group">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                              <Globe size={18} />
                            </div>
                            <div>
                              <div className="text-sm font-bold text-white flex items-center gap-2">
                                {lead.company_name}
                                {lead.is_verified && <CheckCircle size={12} className="text-accent-teal" />}
                              </div>
                              <div className="text-xs text-text-muted font-mono">{lead.domain}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-1">
                            <span className="text-xs font-bold text-slate-300">{lead.industry_name || '未分類'}</span>
                            <span className="text-[10px] text-text-muted">{lead.sub_industry_name || lead.industry_code || '---'}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex-1 h-1.5 w-24 bg-white/5 rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${lead.confidence_score > 80 ? 'bg-emerald-500' : lead.confidence_score > 50 ? 'bg-amber-500' : 'bg-slate-500'}`}
                                style={{ width: `${lead.confidence_score}%` }}
                              />
                            </div>
                            <span className="text-xs font-black text-white">{lead.confidence_score}%</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-xs text-text-muted">
                          {new Date(lead.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-2">
                            <button className="p-2 hover:bg-white/10 rounded-lg text-text-muted hover:text-primary transition-all">
                              <Edit size={16} />
                            </button>
                            <button 
                              onClick={() => handleDeleteLead(lead.id)}
                              className="p-2 hover:bg-red-500/10 rounded-lg text-text-muted hover:text-red-500 transition-all"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {activeTab === 'taxonomy' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1 min-h-0">
            <div className="lg:col-span-4 flex flex-col gap-6">
              <section className="card p-6 border-white/5 bg-primary/5">
                <div className="flex items-center gap-2 mb-4 text-primary">
                  <Layers size={18} />
                  <h3 className="font-bold text-sm uppercase tracking-wider">體系維護說明</h3>
                </div>
                <p className="text-xs text-text-muted leading-relaxed">
                  Linkora 採用三層級產業標籤體系：<br/><br/>
                  1. <b>核心域 (Root)</b>: 如 製造業 (MFG)<br/>
                  2. <b>細分子類 (Branch)</b>: 如 電子製造 (MFG-ELEC)<br/>
                  3. <b>微標籤 (Leaf)</b>: 語法分析自動產生的標籤組合。
                </p>
              </section>
              <button className="btn-primary py-4 flex items-center justify-center gap-2 shadow-lg shadow-primary/20">
                <Tag size={16} /> 新增根節點分類
              </button>
            </div>

            <div className="lg:col-span-8 card p-6 border-white/5 overflow-y-auto custom-scrollbar">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-sm uppercase tracking-wider flex items-center gap-2">
                  <Database size={16} className="text-accent-teal" /> 當前體系樹
                </h3>
              </div>
              
              <div className="space-y-2">
                {industryTree.map(node => (
                  <div key={node.id} className="p-4 rounded-xl bg-white/5 border border-white/5 hover:border-primary/30 transition-all cursor-pointer group">
                    <div className="flex items-center justify-between text-sm font-bold text-white mb-2">
                      <div className="flex items-center gap-2 text-primary">
                         <span className="text-[10px] bg-primary/20 px-1.5 py-0.5 rounded font-mono uppercase tracking-tighter">{node.code}</span>
                         {node.name_zh} / {node.name_en}
                      </div>
                      <ChevronRight size={14} className="text-text-muted group-hover:translate-x-1 transition-transform" />
                    </div>
                    {node.children && node.children.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-2 border-t border-white/5 mt-2">
                        {node.children.map(child => (
                          <span key={child.id} className="text-[10px] px-2 py-1 rounded-md bg-white/5 text-text-muted border border-white/5 hover:text-white transition-colors">
                            {child.name_zh}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'proposals' && (
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {proposals.length === 0 ? (
              <div className="card py-20 flex flex-col items-center justify-center border-dashed border-white/10 opacity-50">
                <CheckCircle size={48} className="text-emerald-500 mb-4 opacity-70" />
                <p className="text-lg font-bold">目前無待處理提案</p>
                <p className="text-xs text-text-muted mt-2">所有用戶提交的資料修正已全數處置完畢。</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {proposals.map(prop => (
                  <div key={prop.id} className="card p-6 border-white/5 hover:bg-white/[0.02] transition-colors relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-1 h-full bg-primary" />
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500">
                          <AlertCircle size={24} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-bold text-white text-base">{prop.global_company_name}</h4>
                            <span className="text-[10px] bg-slate-800 text-text-muted px-2 py-0.5 rounded uppercase font-bold tracking-widest">PROP #{prop.id}</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-text-muted mb-4">
                            <span className="text-primary font-bold">{prop.user_name}</span> 提出於 {new Date(prop.created_at).toLocaleString()}
                          </div>

                          <div className="grid grid-cols-2 gap-4 bg-white/5 p-4 rounded-xl border border-white/5 w-[500px]">
                            <div>
                              <div className="text-[10px] font-black text-text-muted uppercase mb-1">欄位修正: {prop.field_name}</div>
                              <div className="text-sm line-through text-red-400 opacity-60 font-mono">{prop.current_value || '(空值)'}</div>
                            </div>
                            <div>
                               <div className="text-[10px] font-black text-accent-teal uppercase mb-1">建議新值</div>
                               <div className="text-sm text-accent-teal font-bold font-mono">{prop.suggested_value}</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <button 
                          onClick={() => handleResolveProposal(prop.id, 'Approved')}
                          className="px-6 py-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl text-xs font-bold hover:bg-emerald-500 hover:text-white transition-all shadow-lg shadow-emerald-500/10"
                        >
                          核准套用
                        </button>
                        <button 
                          onClick={() => handleResolveProposal(prop.id, 'Rejected')}
                          className="px-6 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded-xl text-xs font-bold hover:bg-red-500 hover:text-white transition-all"
                        >
                          駁回提案
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Intelligence;
