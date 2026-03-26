import React, { useState, useEffect } from 'react';
import { Shield, Cpu, Database, Sparkles, Save, Info, RefreshCw, Trash2, Plus } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { getSystemSettings, updateSystemSetting, getGlobalPoolStats, clearGlobalPool } from '../services/api';

const SystemSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'apis' | 'mapping' | 'general'>('apis');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [globalStats, setGlobalStats] = useState<{total_leads: number, total_domains: number, tags: Record<string, number>} | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  
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
            <span className="version-badge">LINKORA V2.7.1</span>
          </div>
          <p className="page-subtitle">管理 Linkora 全球探勘引擎的核心配置，包含 AI 標籤、Lead 隔離池 (Global Pool) 以及 API 連線。</p>
        </div>
      </div>

      {/* ── Tab Nav ── */}
      <div className="tab-nav">
        {[
          { id: 'apis',    label: 'API 接口管理',  icon: Cpu,      disabled: false },
          { id: 'mapping', label: '變數標籤映射',  icon: Database, disabled: false },
          { id: 'general', label: '隔離池與通用參數',  icon: Shield,   disabled: false }
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
              <h3 className="card__title">
                <Database size={16} style={{ color: 'var(--color-primary)' }} />
                變數與標籤自動化映射
              </h3>
            </div>

            <div className="page-banner page-banner--info" style={{ margin: 0 }}>
              <Info size={15} style={{ flexShrink: 0 }} />
              <p style={{ margin: 0, fontSize: 12, lineHeight: 1.6 }}>
                在這裡定義標籤名稱，系統會在「行銷模板」編輯器中顯示您的自定義標籤（例如：<code>公司名稱</code>），而在發送時自動轉換回系統標準變數（例如：<code>{'{{company_name}}'}</code>）。
              </p>
            </div>

            <div className="card" style={{ display: 'flex', alignItems: 'flex-end', gap: 12 }}>
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
                <h3 className="card__title">
                  <Shield size={16} style={{ color: 'var(--color-accent-teal)' }} />
                  全域隔離資料池 (Lead Isolation Pool)
                </h3>
                <button onClick={fetchGlobalStats} disabled={refreshing} className="btn-icon-sm">
                  <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
                </button>
              </div>

              {/* Pool Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                <div className="card" style={{ padding: '16px', background: 'var(--color-primary-glow)' }}>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>總緩存筆數</div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-primary)' }}>{globalStats?.total_leads || 0}</div>
                </div>
                <div className="card" style={{ padding: '16px', background: 'var(--color-accent-teal-glow)' }}>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>唯一網域分布</div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-accent-teal)' }}>{globalStats?.total_domains || 0}</div>
                </div>
              </div>

              <div className="page-banner page-banner--info" style={{ margin: 0 }}>
                <Info size={15} style={{ flexShrink: 0 }} />
                <p style={{ margin: 0, fontSize: 12, lineHeight: 1.6 }}>
                  全域池會緩存系統中所有已採集的非私有資料。當「全域同步開關」開啟時，新探勘的資料若 Domain 重複，系統將自動從全域池同步而非重新爬取，大幅節省 <b>Apify API 消耗</b>。
                </p>
              </div>

              {/* Sync Controls */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 20, border: '1px border-neutral-glow' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <h4 style={{ margin: 0, fontWeight: 600 }}>全域同步模式 (Global Discovery)</h4>
                    <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>允許系統在探勘前搜尋歷史採集庫中已存在的企業資訊。</p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{generalSettings.enable_global_sync ? '開啟' : '關閉'}</span>
                    <input 
                      type="checkbox" 
                      style={{ width: 40, height: 20 }}
                      checked={generalSettings.enable_global_sync} 
                      onChange={e => setGeneralSettings({ ...generalSettings, enable_global_sync: e.target.checked })} 
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--color-neutral-glow)', paddingTop: 16 }}>
                  <div>
                    <h4 style={{ margin: 0, fontWeight: 600, color: 'var(--color-danger)' }}>維護與管理</h4>
                    <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>手動清理全域緩存池，這將強制所有使用者重新進行 Live Scrape。</p>
                  </div>
                  <button onClick={handleClearPool} className="btn-outline danger">
                    <Trash2 size={14} />清空全域池
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={handleSaveGeneral} disabled={saving} className="btn-primary">
                  {saving ? <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />儲存中...</> : <><Save size={14} />儲存通用參數</>}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemSettings;
