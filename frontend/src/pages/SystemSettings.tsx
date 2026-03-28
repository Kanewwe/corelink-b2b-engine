import * as React from 'react';
import { useState, useEffect } from 'react';
import { Shield, Cpu, Database, Sparkles, Save, RefreshCw, Trash2, Plus, X, Clock, Edit2, Check } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { 
  getSystemSettings, 
  updateSystemSetting, 
  getGlobalPoolStats, 
  clearGlobalPool,
  getAdminProposals,
  resolveProposal,
  getAdminGlobalLeads,
  getAdminAllLeads,
  updateGlobalLead,
  deleteGlobalLead,
  batchDeleteGlobalLeads,
  updateAdminLead,
  deleteAdminLead
} from '../services/api';



interface GlobalProposal {
  id: number;
  user_id: number;
  user_name: string;
  global_id: number;
  global_company_name: string;
  field_name: string;
  current_value: any;
  suggested_value: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  reason?: string;
  created_at: string;
}

// ── Utility: Format UTC ISO to Local time (v2.7.2: 明確指定台灣時區) ──
const formatToLocalTime = (isoString: string) => {
  if (!isoString) return 'N/A';
  try {
    return new Date(isoString).toLocaleString('zh-TW', {
      timeZone: 'Asia/Taipei',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return isoString;
  }
};

const SystemSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'apis' | 'mapping' | 'general' | 'explorer'>('apis');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [globalStats, setGlobalStats] = useState<{total_leads: number, total_domains: number, tags: Record<string, number>} | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  
  // Proposals State
  const [showProposals, setShowProposals] = useState(false);
  const [proposals, setProposals] = useState<GlobalProposal[]>([]);
  const [loadingProposals, setLoadingProposals] = useState(false);

  // Settings State
  const [apiKeys, setApiKeys] = useState({
    openai_key: '',
    openai_model: 'gpt-4o',
    apify_token: '',
    hunter_key: ''
  });

  const [generalSettings, setGeneralSettings] = useState({
    enable_global_sync: true,
    sync_mode: 'domain_only'
  });
  
  const [variableMapping, setVariableMapping] = useState<Record<string, string>>({});
  const [newMappingKey, setNewMappingKey] = useState('');
  const [newMappingLabel, setNewMappingLabel] = useState('');
  
  // Explorer State
  const [globalLeads, setGlobalLeads] = useState<any[]>([]);
  const [allUserLeads, setAllUserLeads] = useState<any[]>([]);
  const [loadingExplorer, setLoadingExplorer] = useState(false);
  const [explorerTab, setExplorerTab] = useState<'global' | 'users'>('global');
  const [searchTerm, setSearchTerm] = useState('');
  
  // CRUD State (v3.7.29)
  const [editingLead, setEditingLead] = useState<any | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [deletingLead, setDeletingLead] = useState<any | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [saving, setSaving] = useState(false);

  const fetchGlobalStats = async () => {
    setRefreshing(true);
    try {
      const resp = await getGlobalPoolStats();
      if (resp.ok) {
        setGlobalStats(await resp.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const resp = await getSystemSettings();
        if (resp.ok) {
          const data = await resp.json();
          setVariableMapping(data.variable_mapping || {});
          setApiKeys((prev: any) => ({ ...prev, ...(data.api_keys || {}) }));
          setGeneralSettings((prev: any) => ({ ...prev, ...(data.general_settings || {}) }));
        }
        await fetchGlobalStats();
      } catch (e) {
        toast.error("讀取系統設定失敗");
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSaveApiKeys = async () => {
    setSaving(true);
    try {
      const resp = await updateSystemSetting('api_keys', apiKeys);
      if (resp.ok) toast.success("API 金鑰已更新");
      else toast.error("儲存失敗");
    } catch (e) { toast.error("連線錯誤"); }
    finally { setSaving(false); }
  };

  const handleSaveGeneral = async () => {
    setSaving(true);
    try {
      const resp = await updateSystemSetting('general_settings', generalSettings);
      if (resp.ok) toast.success("通用設定已儲存");
      else toast.error("儲存失敗");
    } catch (e) { toast.error("連線錯誤"); }
    finally { setSaving(false); }
  };

  const handleClearPool = async () => {
    if (!window.confirm("確定要清空全域隔離池嗎？此操作不可逆，將刪除所有已爬取的全域緩存。")) return;
    setSaving(true);
    try {
      const resp = await clearGlobalPool();
      if (resp.ok) {
        toast.success("全域池已清空");
        fetchGlobalStats();
        // v2.7.2: 清空後也刷新 explorer 資料
        setGlobalLeads([]);
        setAllUserLeads([]);
        if (activeTab === 'explorer') {
          fetchExplorerData();
        }
      }
    } catch (e) { toast.error("清空失敗"); }
    finally { setSaving(false); }
  };

  const handleSaveMapping = async () => {
    setSaving(true);
    try {
      const resp = await updateSystemSetting('variable_mapping', variableMapping);
      if (resp.ok) toast.success("變數映射已儲存");
      else toast.error("儲存失敗");
    } catch (e) { toast.error("連線錯誤"); }
    finally { setSaving(false); }
  };

  const fetchProposals = async () => {
    setLoadingProposals(true);
    try {
      const resp = await getAdminProposals('Pending');
      if (resp.ok) {
        const data = await resp.json();
        setProposals(data);
      }
    } catch (e) {
      toast.error("讀取提案失敗");
    } finally {
      setLoadingProposals(false);
    }
  };

  const handleResolve = async (id: number, status: 'Approved' | 'Rejected') => {
    try {
      const resp = await resolveProposal(id, { status });
      if (resp.ok) {
        toast.success(`提案已${status === 'Approved' ? '核准' : '駁回'}`);
        fetchProposals();
        fetchGlobalStats();
      }
    } catch (e) {
      toast.error("操作失敗");
    }
  };

  useEffect(() => {
    if (showProposals) fetchProposals();
  }, [showProposals]);

  const fetchExplorerData = async () => {
    setLoadingExplorer(true);
    try {
      const [gResp, uResp] = await Promise.all([
        getAdminGlobalLeads(),
        getAdminAllLeads()
      ]);
      if (gResp.ok) setGlobalLeads(await gResp.json());
      if (uResp.ok) setAllUserLeads(await uResp.json());
    } catch (e) {
      toast.error("讀取探勘資料失敗");
    } finally {
      setLoadingExplorer(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'explorer') fetchExplorerData();
  }, [activeTab]);

  // ── CRUD Handlers (v3.7.29) ────────────────────────────────────────────────
  
  const handleEdit = (lead: any) => {
    setEditingLead({ ...lead });
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    if (!editingLead) return;
    setSaving(true);
    try {
      const isGlobal = explorerTab === 'global';
      const apiCall = isGlobal ? updateGlobalLead : updateAdminLead;
      const resp = await apiCall(editingLead.id, editingLead);
      if (resp.ok) {
        toast.success('已更新');
        setShowEditModal(false);
        fetchExplorerData();
      } else {
        const err = await resp.json();
        toast.error(err.detail || '更新失敗');
      }
    } catch (e) {
      toast.error('連線錯誤');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (lead: any) => {
    setDeletingLead(lead);
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!deletingLead) return;
    setSaving(true);
    try {
      const isGlobal = explorerTab === 'global';
      const apiCall = isGlobal ? deleteGlobalLead : deleteAdminLead;
      const resp = await apiCall(deletingLead.id);
      if (resp.ok) {
        toast.success('已刪除');
        setShowDeleteModal(false);
        setDeletingLead(null);
        fetchExplorerData();
        fetchGlobalStats();
      } else {
        const err = await resp.json();
        toast.error(err.detail || '刪除失敗');
      }
    } catch (e) {
      toast.error('連線錯誤');
    } finally {
      setSaving(false);
    }
  };

  const handleSelectOne = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    const leads = explorerTab === 'global' ? globalLeads : allUserLeads;
    const allIds = leads.map((l: any) => l.id);
    if (selectedIds.length === allIds.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(allIds);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) {
      toast.error('請選擇要刪除的資料');
      return;
    }
    if (!window.confirm(`確定要刪除選取的 ${selectedIds.length} 筆資料嗎？`)) return;
    
    setSaving(true);
    try {
      if (explorerTab === 'global') {
        const resp = await batchDeleteGlobalLeads(selectedIds);
        if (resp.ok) {
          const data = await resp.json();
          toast.success(data.message);
          setSelectedIds([]);
          fetchExplorerData();
          fetchGlobalStats();
        }
      } else {
        // 用戶工作區逐筆刪除
        for (const id of selectedIds) {
          await deleteAdminLead(id);
        }
        toast.success(`已刪除 ${selectedIds.length} 筆`);
        setSelectedIds([]);
        fetchExplorerData();
      }
    } catch (e) {
      toast.error('批次刪除失敗');
    } finally {
      setSaving(false);
    }
  };

  const addMapping = () => {
    if (!newMappingKey || !newMappingLabel) {
      toast.error("請輸入完整鍵值與標籤");
      return;
    }
    setVariableMapping(prev => ({ ...prev, [newMappingKey]: newMappingLabel }));
    setNewMappingKey('');
    setNewMappingLabel('');
    toast.success("已暫存新映射");
  };

  const removeMapping = (key: string) => {
    const next = { ...variableMapping };
    delete next[key];
    setVariableMapping(next);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-text-muted gap-4">
        <RefreshCw className="w-8 h-8 animate-spin text-primary" />
        <div className="text-sm font-medium animate-pulse">Loading System Hub...</div>
      </div>
    );
  }

  return (
    <div className="page-wrapper">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              系統控制中心
              <span className="page-title__en">System Hub</span>
            </h1>
            <span className="version-badge">V3.2 (AI Intelligence)</span>
          </div>
          <p className="page-subtitle">管理 Linkora 全球探勘引擎的核心配置，包含 AI 標籤、Lead 隔離池 (Global Pool) 以及 API 連線。</p>
        </div>
      </div>

      {/* ── Tab Nav ── */}
      <div className="tab-nav">
        {[
          { id: 'apis',    label: 'API 接口管理',  icon: Cpu,      disabled: false },
          { id: 'mapping', label: '變數標籤映射',  icon: Database, disabled: false },
          { id: 'general', label: '隔離池設定',  icon: Shield,   disabled: false },
          { id: 'explorer', label: '情資庫檢視器',  icon: Sparkles, disabled: false }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`tab-nav__item ${activeTab === tab.id ? 'active' : ''}`}
          >
            <tab.icon size={14} /> {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      <div>
        {activeTab === 'apis' && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            <div className="card__header">
              <h3 className="card__title">
                <Sparkles size={16} style={{ color: 'var(--color-accent-teal)' }} />
                AI & 外部工具連線配置
              </h3>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 28 }}>
              {/* OpenAI */}
              <div>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-primary)', display: 'inline-block' }} />
                  OpenAI 配置
                </label>
                <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div>
                    <label className="form-label">OpenAI API Key</label>
                    <input type="password" className="form-input" placeholder="sk-..."
                      value={apiKeys.openai_key} onChange={e => setApiKeys({ ...apiKeys, openai_key: e.target.value })} />
                  </div>
                  <div>
                    <label className="form-label">AI 默認模型</label>
                    <select className="form-select" value={apiKeys.openai_model} onChange={e => setApiKeys({ ...apiKeys, openai_model: e.target.value })}>
                      <option value="gpt-4o">GPT-4o（推薦）</option>
                      <option value="gpt-4-turbo">GPT-4 Turbo</option>
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Discovery Section */}
              <div>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-accent-teal)', display: 'inline-block' }} />
                  數據探勘工具 (Discovery)
                </label>
                <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div>
                    <label className="form-label">Apify API Token</label>
                    <input type="password" className="form-input" placeholder="apify_api_..."
                      value={apiKeys.apify_token} onChange={e => setApiKeys({ ...apiKeys, apify_token: e.target.value })} />
                    <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>用於 Yellow Pages 爬蟲</p>
                  </div>
                  <div>
                    <label className="form-label">Hunter.io API Key</label>
                    <input type="password" className="form-input" placeholder="API Key for Email Discovery"
                      value={apiKeys.hunter_key} onChange={e => setApiKeys({ ...apiKeys, hunter_key: e.target.value })} />
                    <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>用於 Email 發現（可選）</p>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: 8 }}>
              <button onClick={handleSaveApiKeys} disabled={saving} className="btn-primary">
                {saving ? <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />儲存中...</> : <><Save size={14} />儲存連線設定</>}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'mapping' && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div className="card__header">
              <h3 className="card__title">採集欄位與系統變數映射</h3>
              <p className="card__subtitle">定義爬蟲吐出的原始 Key 對應到 Linkora 顯示的標籤 (例如: contactEmail 為 聯絡信箱)</p>
            </div>

            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', background: 'var(--color-neutral-glow)', padding: 20, borderRadius: 16 }}>
              <div style={{ flex: 1 }}>
                <label className="form-label">系統變數名</label>
                <input value={newMappingKey} onChange={e => setNewMappingKey(e.target.value)} className="form-input" placeholder="company_name" />
              </div>
              <div style={{ flex: 1 }}>
                <label className="form-label">顯示標籤名</label>
                <input value={newMappingLabel} onChange={e => setNewMappingLabel(e.target.value)} className="form-input" placeholder="公司名稱" />
              </div>
              <button onClick={addMapping} className="btn-outline" style={{ flexShrink: 0 }}>
                <Plus size={14} />新增
              </button>
            </div>

            <div>
              <label className="form-label" style={{ marginBottom: 12 }}>現有映射清單</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {Object.entries(variableMapping).map(([key, label]) => (
                  <div key={key} className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <code style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--color-primary)', background: 'var(--color-primary-glow)', padding: '3px 8px', borderRadius: 4 }}>
                        {'{' + key + '}'}
                      </code>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{label}</span>
                    </div>
                    <button onClick={() => removeMapping(key)} className="btn-icon-sm danger"><Trash2 size={13} /></button>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={handleSaveMapping} disabled={saving} className="btn-primary">
                {saving ? <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />儲存中...</> : <><Save size={14} />儲存映射關係</>}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'general' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="card__header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Shield size={20} style={{ color: 'var(--color-primary)' }} />
                  <div>
                    <h3 className="card__title" style={{ margin: 0 }}>
                      共享領先情報庫 (Shared Lead Intelligence)
                    </h3>
                    <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>v3.1 雙層架構：共享事實層 + 私人覆寫層</p>
                  </div>
                </div>
                <button onClick={fetchGlobalStats} disabled={refreshing} className="btn-icon-sm">
                  <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
                </button>
              </div>

              {/* Pool Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                <div className="card" style={{ padding: '16px', background: 'var(--color-primary-glow)', border: '1px solid var(--color-primary-border)' }}>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>共享公司總數</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--color-primary)' }}>{globalStats?.total_leads || 0}</div>
                </div>
                <div className="card" style={{ padding: '16px', background: 'var(--color-accent-teal-glow)', border: '1px solid var(--color-accent-teal-border)' }}>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>唯一網域 (Domains)</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--color-accent-teal)' }}>{globalStats?.total_domains || 0}</div>
                </div>
                <div className="card" style={{ padding: '16px', background: 'rgba(255, 170, 0, 0.05)', border: '1px solid rgba(255, 170, 100, 0.2)' }}>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>待審核提案</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#ffaa00' }}>{(globalStats as any)?.pending_proposals || 0}</div>
              </div>
              <div className="card" style={{ padding: '16px', background: 'rgba(0, 200, 255, 0.05)', border: '1px solid rgba(0, 200, 255, 0.2)' }}>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>已驗證 Facts</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#00c8ff' }}>{(globalStats as any)?.verified_leads || 0}</div>
              </div>
            </div>

              <div className="page-banner page-banner--info" style={{ margin: 0, padding: '16px 20px', background: 'var(--color-primary-glow)', borderLeft: '4px solid var(--color-primary)' }}>
                <Sparkles size={18} style={{ flexShrink: 0, color: 'var(--color-primary)' }} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
                    從「快取池」進化為「情報庫」
                  </p>
                  <p style={{ margin: 0, fontSize: 12, lineHeight: 1.6, color: 'var(--color-text-muted)' }}>
                    Linkora v3.1 採用雙層模型：優先檢索共享層 (Canonical) 與工作區層 (Overlay) 以降低重複採集點數消耗。
                  </p>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <RefreshCw size={14} /> 共享層同步規則 (Workspace Rules)
                  </h4>
                  
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <p style={{ margin: 0, fontSize: 13 }}>自動同步重複 Domain</p>
                      <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>發現重複網域時，先載入共享層事實 (Canonical Facts)</p>
                    </div>
                    <input 
                      type="checkbox" 
                      style={{ width: 18, height: 18 }}
                      checked={generalSettings.enable_global_sync} 
                      onChange={e => setGeneralSettings({ ...generalSettings, enable_global_sync: e.target.checked })} 
                    />
                  </div>
                </div>

                <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Shield size={14} style={{ color: '#ffaa00' }} /> 數據質量管理 (Data Quality)
                  </h4>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <p style={{ margin: 0, fontSize: 13 }}>修正提案審核機制</p>
                      <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>使用者建議需開發者管理端確認</p>
                    </div>
                    <button onClick={() => setShowProposals(true)} className="btn-outline" style={{ fontSize: 11, padding: '6px 12px' }}>
                      查看提案 ({(globalStats as any)?.pending_proposals || 0})
                    </button>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--color-neutral-glow)', paddingTop: 16 }}>
                    <div>
                      <h4 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--color-danger)' }}>維護全域資料</h4>
                      <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>重置共享事實層（將導致所有 Live Scrape 重新運行）</p>
                    </div>
                    <button onClick={handleClearPool} className="btn-outline danger" style={{ padding: '6px 12px', fontSize: 12 }}>
                      <Trash2 size={12} />重置 SHARED
                    </button>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={handleSaveGeneral} disabled={saving} className="btn-primary">
                  {saving ? <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />儲存中...</> : <><Save size={14} />儲存情報策略</>}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'explorer' && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 className="card__title">管理員情資庫檢視器 (Admin Explorer)</h3>
                <p className="card__subtitle">檢索全系統共享情報與所有成員的工作區名單</p>
              </div>
              <div className="tab-nav" style={{ margin: 0, padding: 4, background: 'var(--color-background-offset)', borderRadius: 12 }}>
                <button 
                  onClick={() => setExplorerTab('global')}
                  className={`tab-nav__item ${explorerTab === 'global' ? 'active' : ''}`}
                  style={{ padding: '6px 16px', fontSize: 12 }}
                >
                  <Database size={12} /> 全域池 (Shared)
                </button>
                <button 
                  onClick={() => setExplorerTab('users')}
                  className={`tab-nav__item ${explorerTab === 'users' ? 'active' : ''}`}
                  style={{ padding: '6px 16px', fontSize: 12 }}
                >
                  <Shield size={12} /> 用戶工作區 (Private)
                </button>
              </div>
            </div>

            <div className="flex gap-4">
              <input 
                type="text" 
                placeholder="搜尋公司名、Domain 或信箱..." 
                className="form-input"
                style={{ flex: 1 }}
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
              <button onClick={fetchExplorerData} className="btn-outline">
                <RefreshCw size={14} className={loadingExplorer ? 'animate-spin' : ''} />
              </button>
            </div>

            {/* Batch Actions (v3.7.29) */}
            {selectedIds.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 16px', background: 'var(--color-primary-glow)', borderRadius: 8, border: '1px solid var(--color-primary-border)' }}>
                <span style={{ fontSize: 13 }}>已選取 {selectedIds.length} 筆</span>
                <button onClick={handleBatchDelete} disabled={saving} className="btn-outline danger" style={{ fontSize: 12, padding: '4px 12px' }}>
                  <Trash2 size={12} /> 批次刪除
                </button>
                <button onClick={() => setSelectedIds([])} className="btn-outline" style={{ fontSize: 12, padding: '4px 12px' }}>
                  取消選取
                </button>
              </div>
            )}

            <div style={{ overflowX: 'auto', border: '1px solid var(--color-neutral-glow)', borderRadius: 12 }}>
              <table className="leads-table">
                <thead>
                  <tr>
                    <th style={{ width: 40 }}>
                      <input 
                        type="checkbox" 
                        checked={selectedIds.length === (explorerTab === 'global' ? globalLeads.length : allUserLeads.length) && selectedIds.length > 0}
                        onChange={handleSelectAll}
                      />
                    </th>
                    <th>公司名稱</th>
                    <th>網域 / 網址</th>
                    <th>聯絡信箱</th>
                    {explorerTab === 'users' && <th>所屬成員</th>}
                    <th>AI 標籤</th>
                    <th>來源/狀態</th>
                    <th style={{ width: 80 }}>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingExplorer ? (
                    <tr><td colSpan={explorerTab === 'users' ? 8 : 7} style={{ textAlign: 'center', padding: '40px 0' }}>載入中...</td></tr>
                  ) : (explorerTab === 'global' ? globalLeads : allUserLeads)
                      .filter((l: any) => 
                        !searchTerm || 
                        l.company_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        l.domain?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        (l.user_email && l.user_email.toLowerCase().includes(searchTerm.toLowerCase()))
                      )
                      .map((lead: any) => (
                    <tr key={lead.id}>
                      <td>
                        <input 
                          type="checkbox"
                          checked={selectedIds.includes(lead.id)}
                          onChange={() => handleSelectOne(lead.id)}
                        />
                      </td>
                      <td className="font-bold">{lead.company_name}</td>
                      <td>
                        <div style={{ fontSize: 12 }}>{lead.domain}</div>
                        <div className="text-text-muted" style={{ fontSize: 10 }}>{lead.website_url}</div>
                      </td>
                      <td>{lead.contact_email || lead.display_email || <span className="text-text-muted italic">無</span>}</td>
                      {explorerTab === 'users' && <td className="text-primary font-medium">{lead.user_email}</td>}
                      <td>
                        <span className={`tag tag--${lead.ai_tag?.toLowerCase() || 'default'}`}>
                          {lead.ai_tag}
                        </span>
                      </td>
                      <td>
                        <div style={{ fontSize: 11 }}>{lead.source || lead.status}</div>
                        <div className="text-text-muted" style={{ fontSize: 10 }}>
                          {formatToLocalTime(lead.created_at)}
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <button onClick={() => handleEdit(lead)} className="btn-icon-sm" title="編輯">
                            <Edit2 size={12} />
                          </button>
                          <button onClick={() => handleDelete(lead)} className="btn-icon-sm danger" title="刪除">
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Proposals Modal */}
      {showProposals && (
        <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-slate-800 border border-white/10 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[80vh]">
            <div className="p-6 border-b border-white/10 flex justify-between items-center">
              <h3 className="text-xl font-bold text-white flex items-center gap-3">
                <Database className="text-primary" /> 數據修正提案審核
              </h3>
              <button onClick={() => setShowProposals(false)} className="p-2 hover:bg-white/10 rounded-lg text-text-muted">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loadingProposals ? (
                <div className="text-center py-12 text-text-muted">載入中...</div>
              ) : proposals.length === 0 ? (
                <div className="text-center py-12 text-text-muted italic">目前沒有待處理的提案</div>
              ) : (
                proposals.map((p: GlobalProposal) => (
                  <div key={p.id} className="card p-4 space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-xs font-bold text-primary uppercase tracking-wider">{p.field_name}</span>
                        <h4 className="font-bold text-white">{p.global_company_name || '未知公司'}</h4>
                        <div className="text-[10px] text-text-muted mt-1">
                          <Clock size={10} style={{ display: 'inline', marginRight: 4 }} />
                          {formatToLocalTime(p.created_at)}
                        </div>
                      </div>
                      <div className="text-right text-xs text-text-muted">
                        提交者: {p.user_name} (ID: #{p.user_id})
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 pt-2">
                      <div className="p-3 bg-red-500/5 border border-red-500/10 rounded-lg">
                        <div className="text-[10px] text-red-400 uppercase font-bold mb-1">目前數值</div>
                        <div className="text-sm text-white opacity-60 line-through">{p.current_value || '無'}</div>
                      </div>
                      <div className="p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-lg">
                        <div className="text-[10px] text-emerald-400 uppercase font-bold mb-1">提案建議值</div>
                        <div className="text-sm text-emerald-400 font-bold">{p.suggested_value}</div>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-2">
                        <button onClick={() => handleResolve(p.id, 'Rejected')} className="btn-outline-sm danger">駁回建議</button>
                        <button onClick={() => handleResolve(p.id, 'Approved')} className="btn-primary-sm">核准並更新事實層</button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal (v3.7.29) */}
      {showEditModal && editingLead && (
        <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-slate-800 border border-white/10 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[80vh]">
            <div className="p-6 border-b border-white/10 flex justify-between items-center">
              <h3 className="text-xl font-bold text-white flex items-center gap-3">
                <Edit2 className="text-primary" /> 編輯公司資料
              </h3>
              <button onClick={() => setShowEditModal(false)} className="p-2 hover:bg-white/10 rounded-lg text-text-muted">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-text-muted mb-1 block">公司名稱</label>
                  <input 
                    className="form-input"
                    value={editingLead.company_name || ''}
                    onChange={e => setEditingLead({ ...editingLead, company_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs text-text-muted mb-1 block">網域</label>
                  <input 
                    className="form-input"
                    value={editingLead.domain || ''}
                    onChange={e => setEditingLead({ ...editingLead, domain: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-text-muted mb-1 block">網站</label>
                <input 
                  className="form-input"
                  value={editingLead.website_url || ''}
                  onChange={e => setEditingLead({ ...editingLead, website_url: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-text-muted mb-1 block">聯絡信箱</label>
                  <input 
                    className="form-input"
                    value={editingLead.contact_email || ''}
                    onChange={e => setEditingLead({ ...editingLead, contact_email: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs text-text-muted mb-1 block">電話</label>
                  <input 
                    className="form-input"
                    value={editingLead.phone || ''}
                    onChange={e => setEditingLead({ ...editingLead, phone: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-text-muted mb-1 block">地址</label>
                <input 
                  className="form-input"
                  value={editingLead.address || ''}
                  onChange={e => setEditingLead({ ...editingLead, address: e.target.value })}
                />
              </div>
              {explorerTab === 'users' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-text-muted mb-1 block">狀態</label>
                    <select 
                      className="form-input"
                      value={editingLead.status || 'new'}
                      onChange={e => setEditingLead({ ...editingLead, status: e.target.value })}
                    >
                      <option value="new">新名單</option>
                      <option value="contacted">已聯繫</option>
                      <option value="replied">已回覆</option>
                      <option value="converted">已成交</option>
                      <option value="lost">已流失</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-text-muted mb-1 block">評分 (0-100)</label>
                    <input 
                      type="number"
                      className="form-input"
                      value={editingLead.lead_score || 0}
                      onChange={e => setEditingLead({ ...editingLead, lead_score: parseInt(e.target.value) })}
                    />
                  </div>
                </div>
              )}
            </div>
            <div className="p-6 border-t border-white/10 flex justify-end gap-3">
              <button onClick={() => setShowEditModal(false)} className="btn-outline">取消</button>
              <button onClick={handleSaveEdit} disabled={saving} className="btn-primary">
                {saving ? '儲存中...' : <><Check size={14} /> 儲存變更</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal (v3.7.29) */}
      {showDeleteModal && deletingLead && (
        <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-slate-800 border border-white/10 rounded-2xl w-full max-w-md shadow-2xl">
            <div className="p-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-3 mb-4">
                <Trash2 className="text-red-400" /> 確認刪除
              </h3>
              <p className="text-text-muted mb-4">確定要刪除這筆資料嗎？此操作無法復原。</p>
              <div className="bg-slate-700/50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-text-muted">公司：</span>
                  <span className="text-white font-medium">{deletingLead.company_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">網域：</span>
                  <span className="text-white">{deletingLead.domain || 'N/A'}</span>
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-white/10 flex justify-end gap-3">
              <button onClick={() => setShowDeleteModal(false)} className="btn-outline">取消</button>
              <button onClick={handleConfirmDelete} disabled={saving} className="btn-primary danger">
                {saving ? '刪除中...' : '確認刪除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemSettings;
