import React, { useState, useEffect } from 'react';
import { Settings, Shield, Cpu, Database, Sparkles, Save, Info, RefreshCw, Trash2, Plus } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { getSystemSettings, updateSystemSetting } from '../services/api';

const SystemSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'apis' | 'mapping' | 'general'>('apis');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Settings State
  const [apiKeys, setApiKeys] = useState({
    openai_key: '',
    openai_model: 'gpt-4o',
    google_cse_id: '',
    google_api_key: '',
    hunter_key: ''
  });
  
  const [variableMapping, setVariableMapping] = useState<Record<string, string>>({});
  const [newMappingKey, setNewMappingKey] = useState('');
  const [newMappingLabel, setNewMappingLabel] = useState('');

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const resp = await getSystemSettings();
        if (resp.ok) {
          const data = await resp.json();
          // Backend returns: { "api_keys": {...}, "variable_mapping": {...} }
          const mapping = data.variable_mapping || {};
          const keys = data.api_keys || {};

          setVariableMapping(mapping);
          setApiKeys(prev => ({ ...prev, ...keys }));
        }
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
      if (resp.ok) {
        toast.success("API 金鑰已更新");
      } else {
        toast.error("儲存失敗");
      }
    } catch (e) {
      toast.error("連線錯誤");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMapping = async () => {
    setSaving(true);
    try {
      const resp = await updateSystemSetting('variable_mapping', variableMapping);
      if (resp.ok) {
        toast.success("變數映射已儲存");
      } else {
        toast.error("儲存失敗");
      }
    } catch (e) {
      toast.error("連線錯誤");
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
            <span className="version-badge">LINKORA V2</span>
          </div>
          <p className="page-subtitle">管理 Linkora 全球探勘引擎的核心配置，包含 AI 驅動模型、外部數據接口連線以及系統變數映射定義。</p>
        </div>
      </div>

      {/* ── Tab Nav（統一元件）── */}
      <div className="tab-nav">
        {[
          { id: 'apis',    label: 'API 接口管理',  icon: Cpu },
          { id: 'mapping', label: '變數標籤映射',  icon: Database },
          { id: 'general', label: '通用系統參數',  icon: Shield }
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
              <div className="space-y-4">
                <label className="text-xs font-black text-text-muted uppercase tracking-widest flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-accent" /> 數據探勘工具 (Discovery)
                </label>
                <div className="space-y-4 bg-black/20 p-6 rounded-2xl border border-white/5">
                  <div className="space-y-2">
                  <div>
                    <label className="form-label">Hunter.io API Key</label>
                    <input type="password" className="form-input" placeholder="API Key for Email Discovery"
                      value={apiKeys.hunter_key} onChange={e => setApiKeys({ ...apiKeys, hunter_key: e.target.value })} />
                  </div>
                  <div>
                    <label className="form-label">Google CSE ID</label>
                    <input className="form-input" placeholder="Search Engine ID"
                      value={apiKeys.google_cse_id} onChange={e => setApiKeys({ ...apiKeys, google_cse_id: e.target.value })} />
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

            {/* Info Banner */}
            <div className="page-banner page-banner--info" style={{ margin: 0 }}>
              <Info size={15} style={{ flexShrink: 0 }} />
              <p style={{ margin: 0, fontSize: 12, lineHeight: 1.6 }}>
                在這裡定義標籤名稱，系統會在「行銷模板」編輯器中顯示您的自定義標籤（例如：<code>公司名稱</code>），而在發送時自動轉換回系統標準變數（例如：<code>{'{{company_name}}'}</code>）。
              </p>
            </div>

            {/* Add New Mapping */}
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

            {/* Mapping List */}
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
                {Object.keys(variableMapping).length === 0 && (
                  <div style={{ gridColumn: '1/-1' }}>
                    <div className="empty-state" style={{ padding: '32px 20px' }}>
                      <p className="empty-state__title">尚無映射設定</p>
                    </div>
                  </div>
                )}
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
          <div className="card">
            <div className="empty-state" style={{ padding: '80px 20px' }}>
              <div className="empty-state__icon"><Shield size={48} style={{ opacity: 0.3 }} /></div>
              <p className="empty-state__title">通用參數即將推出</p>
              <p className="empty-state__desc">包含語系切換、時區設定及預設登入偏好。</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemSettings;
