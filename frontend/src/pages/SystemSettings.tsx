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
    <div className="flex flex-col h-full gap-6 animate-in fade-in duration-500 overflow-y-auto pb-20 pr-2 custom-scrollbar">
      {/* Header Panel */}
      <div className="bg-glass-panel p-8 rounded-2xl border border-white/5 relative overflow-hidden group">
        <div className="absolute -right-10 -top-10 opacity-5 group-hover:opacity-10 transition-opacity">
          <Settings size={200} />
        </div>
        <div className="relative z-10">
          <h2 className="text-3xl font-black text-white flex items-center gap-3">
             <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center border border-primary/20 shadow-inner">
                <Settings className="w-7 h-7 text-primary" />
             </div>
             系統控制中心 (System Hub)
          </h2>
          <p className="text-text-muted mt-2 max-w-2xl text-sm leading-relaxed">
            管理 Linkora 全球探勘引擎的核心配置，包含 AI 驅動模型、外部數據接口連線以及系統變數映射定義。
          </p>
        </div>
      </div>

      {/* Main Tabs */}
      <div className="flex gap-4">
        {[
          { id: 'apis', label: 'API 接口管理', icon: Cpu },
          { id: 'mapping', label: '變數標籤映射', icon: Database },
          { id: 'general', label: '通用系統參數', icon: Shield }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-6 py-3 rounded-xl text-sm font-bold flex items-center gap-3 transition-all border ${
              activeTab === tab.id 
                ? 'bg-primary/20 text-white border-primary/30 shadow-lg shadow-primary/10' 
                : 'bg-white/5 text-text-muted border-white/5 hover:bg-white/10'
            }`}
          >
            <tab.icon className="w-4 h-4" /> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1">
        {activeTab === 'apis' && (
          <div className="glass-panel p-8 flex flex-col gap-8 animate-in slide-in-from-right-4 duration-300">
            <div className="flex items-center gap-3 pb-6 border-b border-white/5">
              <Sparkles className="text-accent w-5 h-5" />
              <h3 className="text-xl font-bold text-white tracking-tight">AI & 外部工具連線配置</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* OpenAI Section */}
              <div className="space-y-4">
                <label className="text-xs font-black text-text-muted uppercase tracking-widest flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary" /> OpenAI 配置
                </label>
                <div className="space-y-4 bg-black/20 p-6 rounded-2xl border border-white/5">
                  <div className="space-y-2">
                    <span className="text-[10px] text-text-muted ml-1">OpenAI API Key</span>
                    <input 
                      type="password"
                      className="input-field"
                      placeholder="sk-..."
                      value={apiKeys.openai_key}
                      onChange={e => setApiKeys({...apiKeys, openai_key: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <span className="text-[10px] text-text-muted ml-1">AI 默認模型</span>
                    <select 
                      className="input-field appearance-none"
                      value={apiKeys.openai_model}
                      onChange={e => setApiKeys({...apiKeys, openai_model: e.target.value})}
                    >
                      <option value="gpt-4o">GPT-4o (推薦)</option>
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
                    <span className="text-[10px] text-text-muted ml-1">Hunter.io API Key</span>
                    <input 
                      type="password"
                      className="input-field"
                      placeholder="API Key for Email Discovery"
                      value={apiKeys.hunter_key}
                      onChange={e => setApiKeys({...apiKeys, hunter_key: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <span className="text-[10px] text-text-muted ml-1">Google CSE ID</span>
                    <input 
                      className="input-field"
                      placeholder="Search Engine ID"
                      value={apiKeys.google_cse_id}
                      onChange={e => setApiKeys({...apiKeys, google_cse_id: e.target.value})}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button 
                onClick={handleSaveApiKeys}
                disabled={saving}
                className="flex items-center gap-2 bg-primary hover:bg-primary-dark text-white px-8 py-3 rounded-xl font-bold transition-all shadow-xl shadow-primary/20 disabled:opacity-50"
              >
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                儲存連線設定
              </button>
            </div>
          </div>
        )}

        {activeTab === 'mapping' && (
          <div className="glass-panel p-8 flex flex-col gap-8 animate-in slide-in-from-right-4 duration-300">
            <div className="flex items-center gap-3 pb-6 border-b border-white/5">
              <Database className="text-primary w-5 h-5" />
              <h3 className="text-xl font-bold text-white tracking-tight">變數與標籤自動化映射</h3>
            </div>

            <div className="space-y-6">
              <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl flex items-start gap-3">
                <Info className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <p className="text-xs text-text-muted leading-relaxed">
                  在這裡定義標籤名稱，系統會在「行銷模板」編輯器中顯示您的自定義標籤（例如：<code>公司名稱</code>），而在發送時自動轉換回系統標準變數（例如：<code>{"{{company_name}}"}</code>）。
                </p>
              </div>

              <div className="grid grid-cols-1 gap-4">
                 <div className="flex items-end gap-4 bg-white/5 p-6 rounded-2xl border border-white/5">
                    <div className="flex-1 space-y-2">
                       <span className="text-[10px] font-bold text-text-muted uppercase ml-1">系統變數名 (e.g. company_name)</span>
                       <input 
                          value={newMappingKey}
                          onChange={e => setNewMappingKey(e.target.value)}
                          className="input-field"
                          placeholder="company_name"
                       />
                    </div>
                    <div className="flex-1 space-y-2">
                       <span className="text-[10px] font-bold text-text-muted uppercase ml-1">顯示標籤名 (e.g. 公司名稱)</span>
                       <input 
                          value={newMappingLabel}
                          onChange={e => setNewMappingLabel(e.target.value)}
                          className="input-field"
                          placeholder="公司名稱"
                       />
                    </div>
                    <button 
                      onClick={addMapping}
                      className="bg-white/10 hover:bg-white/20 p-3.5 rounded-2xl transition-all border border-white/10 text-white"
                    >
                      <Plus className="w-5 h-5" />
                    </button>
                 </div>

                 <div className="space-y-2 mt-4">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-widest ml-1">現有映射清單</span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                       {Object.entries(variableMapping).map(([key, label]) => (
                         <div key={key} className="flex items-center justify-between p-4 bg-black/20 rounded-xl border border-white/5 hover:border-primary/20 transition-all group">
                            <div className="flex items-center gap-4">
                               <code className="text-[11px] font-mono text-primary bg-primary/10 px-2 py-1 rounded">{"{" + key + "}"}</code>
                               <span className="text-white font-bold text-sm">{label}</span>
                            </div>
                            <button 
                              onClick={() => removeMapping(key)}
                              className="text-error/30 hover:text-error transition-colors p-2"
                            >
                               <Trash2 className="w-4 h-4" />
                            </button>
                         </div>
                       ))}
                    </div>
                 </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button 
                onClick={handleSaveMapping}
                disabled={saving}
                className="flex items-center gap-2 bg-primary hover:bg-primary-dark text-white px-8 py-3 rounded-xl font-bold transition-all shadow-xl shadow-primary/20 disabled:opacity-50"
              >
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                儲存映射關係
              </button>
            </div>
          </div>
        )}

        {activeTab === 'general' && (
          <div className="glass-panel p-16 flex flex-col items-center justify-center gap-4 border-dashed border-white/10 opacity-60 animate-in fade-in duration-500">
             <Shield className="w-16 h-16 text-text-muted" />
             <div className="text-center">
                <h3 className="text-xl font-bold text-white">通用參數即將推出</h3>
                <p className="text-sm text-text-muted mt-1">包含語系切換、時區設定及預設登入偏好。</p>
             </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemSettings;
