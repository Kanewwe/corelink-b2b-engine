import { Plus, Folder, Paperclip, Save, Trash2, Edit, Check, Sparkles, RotateCcw, FileCode, Eye, Layout, Languages, Type } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { getTemplates, createTemplate, updateTemplate, deleteTemplate, generateAiTemplate } from '../services/api';
import Editor from "@monaco-editor/react";
import React, { useState, useEffect } from 'react';

interface Template {
  id: number;
  name: string;
  tag: string;
  subject: string;
  body: string;
  is_default: boolean;
  attachment_url?: string;
  created_at: string;
}

const Templates: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'create' | 'list' | 'attachments' | 'settings'>('list');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [variableMapping, setVariableMapping] = useState<Record<string, string>>({
    'company_name': '公司名稱',
    'bd_name': '我的姓名 (BD)',
    'industry': '產業領域',
    'product_name': '產品名稱'
  });
  
  const [editorMode, setEditorMode] = useState<'html' | 'preview' | 'split'>('html');
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiStyle, setAiStyle] = useState('formal');
  const [aiLanguage, setAiLanguage] = useState('English');
  const [isGenerating, setIsGenerating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  
  const [form, setForm] = useState({
    name: '',
    tag: 'GENERAL',
    subject: '',
    body: '<html><body>\n<h1>Hello {{company_name}}</h1>\n<p>This is a sample template.</p>\n</body></html>',
    is_default: false
  });

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const resp = await getTemplates();
      if (resp.ok) {
        setTemplates(await resp.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchSettings = async () => {
    try {
      const { getSystemSettings } = await import('../services/api');
      const resp = await getSystemSettings();
      if (resp.ok) {
        const data = await resp.json();
        if (data.variable_mapping) {
          setVariableMapping(data.variable_mapping);
        }
      }
    } catch (e) {
      console.error("Failed to fetch mapping", e);
    }
  };

  useEffect(() => {
    fetchTemplates();
    fetchSettings();
  }, []);

  const handleAiGenerate = async () => {
    if (!aiPrompt) {
      toast.error("請描述您想生成的信件內容");
      return;
    }
    
    setIsGenerating(true);
    const loadingToast = toast.loading("AI 正在為您排版專業開發信...");
    
    try {
      const resp = await generateAiTemplate({
        prompt: aiPrompt,
        style: aiStyle,
        language: aiLanguage
      });
      
      const data = await resp.json();
      if (resp.ok && data.html) {
        toast.success("AI 生成成功！已套用至編輯器。", { id: loadingToast });
        setForm(prev => ({ ...prev, body: data.html, subject: data.subject || prev.subject }));
        setEditorMode('split');
      } else {
        toast.error(data.detail || "AI 服務暫時無法回應", { id: loadingToast });
      }
    } catch (e) {
      toast.error("網路通訊錯誤", { id: loadingToast });
    } finally {
      setIsGenerating(false);
    }
  };

  const insertVariable = (v: string) => {
    setForm(prev => ({ ...prev, body: prev.body + ` {{${v}}}` }));
    toast.success(`已插入變數: {{${v}}}`);
  };

  const handleSave = async () => {
    if (!form.name || !form.subject) {
      toast.error("請填寫模板名稱與主旨");
      return;
    }
    if (!form.body || form.body.trim() === '<html><body></body></html>') {
      toast.error("HTML 內容不可為空");
      return;
    }
    
    setSaving(true);
    const loadingToast = toast.loading(editingId ? "正在更新模板..." : "正在儲存模板...");
    
    try {
      let resp;
      if (editingId) {
        resp = await updateTemplate(editingId, form);
      } else {
        resp = await createTemplate(form);
      }
      
      if (resp.ok) {
        toast.success(editingId ? "模板更新成功！" : "模板儲存成功！", { id: loadingToast });
        setEditingId(null);
        setForm({ name: '', tag: 'GENERAL', subject: '', body: '<html><body></body></html>', is_default: false });
        setActiveTab('list');
        fetchTemplates();
      } else {
        const err = await resp.json();
        toast.error(err.detail || "儲存失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("網路錯誤，請稍後再試", { id: loadingToast });
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (t: Template) => {
    setEditingId(t.id);
    setForm({
      name: t.name,
      tag: t.tag,
      subject: t.subject,
      body: t.body,
      is_default: t.is_default
    });
    setActiveTab('create');
  };

  const handleDelete = async (id: number) => {
    if (!confirm('確定要刪除此模板嗎？')) return;
    try {
      const resp = await deleteTemplate(id);
      if (resp.ok) { fetchTemplates(); toast.success('模板已刪除'); }
    } catch { toast.error('刪除失敗'); }
  };

  return (
    <div className="page-wrapper">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              智慧行銷劇本
              <span className="page-title__en">AI Scripts</span>
            </h1>
            <span className="version-badge">LINKORA V2</span>
          </div>
          <p className="page-subtitle">建立、管理並以 AI 輔助生成個性化開發信模板。</p>
        </div>
        <div className="page-header__right">
          <button onClick={() => { setEditingId(null); setForm({ name: '', tag: 'GENERAL', subject: '', body: '<html><body></body></html>', is_default: false }); setActiveTab('create'); }} className="btn-primary btn--sm">
            <Plus size={14} />建立新模板
          </button>
        </div>
      </div>

      {/* ── Tab Nav（統一元件）── */}
      <div className="tab-nav">
        <button className={`tab-nav__item ${activeTab === 'list' ? 'active' : ''}`} onClick={() => setActiveTab('list')}>
          <Folder size={14} /> 現有模板
        </button>
        <button className={`tab-nav__item ${activeTab === 'create' ? 'active' : ''}`} onClick={() => { setEditingId(null); setForm({ name: '', tag: 'GENERAL', subject: '', body: '<html><body></body></html>', is_default: false }); setActiveTab('create'); }}>
          <Plus size={14} /> {editingId ? '編輯模板' : '建立新模板'}
        </button>
        <button className={`tab-nav__item ${activeTab === 'attachments' ? 'active' : ''}`} onClick={() => setActiveTab('attachments')}>
          <Paperclip size={14} /> 附件管理
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0, paddingRight: 4 }}>
        {activeTab === 'create' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20, paddingBottom: 40 }}>

            {/* 模板基本資訊 */}
            <div className="card">
              <div className="card__header">
                <h3 className="card__title">
                  {editingId ? '📝 編輯模板內容' : '✨ 建立新行銷模板'}
                </h3>
                {editingId && <span className="badge badge--primary">Editing Mode</span>}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div>
                  <label className="form-label">模板名稱 *</label>
                  <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                    placeholder="例如：北美開發信-V1" className="form-input" />
                </div>
                <div>
                  <label className="form-label">分類標籤</label>
                  <input value={form.tag} onChange={e => setForm({ ...form, tag: e.target.value })}
                    placeholder="GENERAL" className="form-input" />
                </div>
                <div className="space-y-2 flex flex-col justify-end pb-3">
                  <label className="flex items-center gap-3 cursor-pointer text-sm select-none text-text-muted hover:text-white transition-colors">
                    <input 
                      type="checkbox" 
                      className="w-5 h-5 accent-primary rounded-md"
                      checked={form.is_default}
                      onChange={e => setForm({...form, is_default: e.target.checked})}
                    />
                    設為該標籤預設
                  </label>
                </div>
              </div>

              <div className="mt-6 space-y-2">
                <label className="text-xs font-bold text-text-muted uppercase tracking-widest ml-1">郵件主旨 (Subject) *</label>
                <input 
                  type="text" 
                  value={form.subject}
                  onChange={e => setForm({...form, subject: e.target.value})}
                  placeholder="Hello {{company_name}}, interesting opportunity for you"
                  className="form-input"
                />
                <p className="text-[10px] text-text-muted flex items-center gap-1.5 mt-2">
                  <span className="bg-white/10 px-1.5 py-0.5 rounded text-white flex items-center">Tip</span>
                  支援變數動態替換：<code>{"{{company_name}}"}</code>, <code>{"{{contact_name}}"}</code>
                </p>
              </div>
            </div>

            {/* Middle Section: Advanced Controller & Monaco Editor */}
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              {/* AI Generation Box (The Advanced One) */}
              <div className="bg-[#1e2330] rounded-2xl border border-white/5 p-6 shadow-inner">
                 <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 bg-primary/20 rounded-lg flex items-center justify-center">
                       <Sparkles className="w-4 h-4 text-primary fill-primary/30" />
                    </div>
                    <div>
                       <h4 className="text-sm font-bold text-white">AI 智慧生成信件排版</h4>
                       <p className="text-[10px] text-text-muted">描述您的信件目的，AI 自動排版為專業 HTML 開發信</p>
                    </div>
                 </div>

                 <textarea 
                    value={aiPrompt}
                    onChange={e => setAiPrompt(e.target.value)}
                    placeholder="例如：我要寫一封針對美國汽車零件採購商的開發信，強調我們的 Cable 產品品質與交期..."
                    className="form-textarea" style={{ height: 96, resize: "none", marginBottom: 14 }}
                 />

                 <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex gap-4">
                       <div className="flex flex-col gap-1.5">
                          <label className="text-[10px] text-text-muted font-bold ml-1">語言風格：</label>
                          <div className="relative">
                             <Type className="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted" />
                             <select 
                                value={aiStyle}
                                onChange={e => setAiStyle(e.target.value)}
                                className="form-select" style={{ paddingLeft: 32, fontSize: 12 }}
                             >
                                <option value="formal">正式商務</option>
                                <option value="friendly">親切隨和</option>
                                <option value="urgent">急迫感行銷</option>
                                <option value="followup">後續追蹤</option>
                             </select>
                          </div>
                       </div>
                       <div className="flex flex-col gap-1.5">
                          <label className="text-[10px] text-text-muted font-bold ml-1">信件語言：</label>
                          <div className="relative">
                             <Languages className="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted" />
                             <select 
                                value={aiLanguage}
                                onChange={e => setAiLanguage(e.target.value)}
                                className="form-select" style={{ paddingLeft: 32, fontSize: 12 }}
                             >
                                <option value="English">English</option>
                                <option value="Traditional Chinese">繁體中文</option>
                                <option value="Spanish">Spanish</option>
                                <option value="Japanese">日本語</option>
                             </select>
                          </div>
                       </div>
                    </div>
                    
                    <div className="flex gap-2">
                       <button 
                          onClick={handleAiGenerate}
                          disabled={isGenerating}
                          className="bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-xl text-xs font-black transition-all shadow-lg shadow-primary/20 flex items-center gap-2 disabled:opacity-50"
                       >
                          {isGenerating ? <RotateCcw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                          讓 AI 生成 HTML
                       </button>
                       <button 
                          onClick={() => {setAiPrompt(''); setAiStyle('formal');}}
                          className="bg-white/5 hover:bg-white/10 text-text-muted px-4 py-2 rounded-xl text-xs font-bold transition-all"
                       >
                          清除
                       </button>
                    </div>
                 </div>
              </div>

              {/* Mode Switcher & Tools */}
              <div className="flex flex-wrap items-center justify-between gap-4 py-2 border-y border-white/5">
                 <div className="flex items-center gap-3">
                    <span className="text-[10px] text-text-muted font-bold uppercase tracking-wider">模式切換：</span>
                    <div className="flex bg-black/40 p-1 rounded-xl border border-white/5">
                       <button 
                          onClick={() => setEditorMode('html')}
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all ${editorMode === 'html' ? 'bg-white/10 text-white' : 'text-text-muted hover:text-white'}`}
                       >
                          <FileCode className="w-3.5 h-3.5" /> HTML 編輯
                       </button>
                       <button 
                          onClick={() => setEditorMode('preview')}
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all ${editorMode === 'preview' ? 'bg-white/10 text-white' : 'text-text-muted hover:text-white'}`}
                       >
                          <Eye className="w-3.5 h-3.5" /> 預覽
                       </button>
                       <button 
                          onClick={() => setEditorMode('split')}
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all ${editorMode === 'split' ? 'bg-white/10 text-white' : 'text-text-muted hover:text-white'}`}
                       >
                          <Layout className="w-3.5 h-3.5" /> 分割視圖
                       </button>
                    </div>
                 </div>

                 <div className="flex gap-2">
                    <button className="text-[10px] bg-white/5 hover:bg-white/10 text-text-muted px-3 py-1.5 rounded-lg transition-colors">格式化</button>
                    <button className="text-[10px] bg-white/5 hover:bg-white/10 text-text-muted px-3 py-1.5 rounded-lg transition-colors">復原</button>
                 </div>
              </div>

              {/* Variable Insertion Chips */}
              <div className="flex flex-wrap items-center gap-2">
                 <span className="text-[10px] text-text-muted font-bold uppercase tracking-wider mr-1">變數插入 (點擊插入)：</span>
                 {Object.entries(variableMapping).map(([key, label]) => (
                    <button 
                       key={key}
                       onClick={() => insertVariable(key)}
                       className="bg-primary/10 border border-primary/20 text-primary-light text-[10px] px-2.5 py-1 rounded-md hover:bg-primary/20 transition-all flex items-center gap-1.5"
                    >
                       <span className="opacity-60">{label}:</span>
                       <span className="font-mono">{"{{" + key + "}}"}</span>
                    </button>
                 ))}
                 
                 {Object.keys(variableMapping).length === 0 && (
                    <span className="text-[10px] text-text-muted italic">尚未在設定中建立變數映射</span>
                 )}
              </div>

              {/* Editor / Preview Area */}
              <div className={`grid gap-4 ${editorMode === 'split' ? 'grid-cols-2' : 'grid-cols-1'}`}>
                 {(editorMode === 'html' || editorMode === 'split') && (
                    <div className="flex flex-col gap-2" style={{ minHeight: 400 }}>
                       <div className="text-[10px] text-text-muted uppercase tracking-widest flex items-center gap-1.5 bg-white/5 px-3 py-1 rounded-t-lg w-fit">
                          <FileCode className="w-3 h-3" /> HTML 編輯器
                       </div>
                       <div className="flex-1 border border-white/10 rounded-xl overflow-hidden shadow-2xl" style={{ minHeight: 400 }}>
                          <Editor
                             height="400px"
                             defaultLanguage="html"
                             theme="vs-dark"
                             value={form.body}
                             onChange={(val) => setForm({...form, body: val || ''})}
                             options={{
                               minimap: { enabled: false },
                               fontSize: 14,
                               lineNumbers: 'on',
                               scrollBeyondLastLine: false,
                               automaticLayout: true,
                               padding: { top: 16, bottom: 16 },
                               renderLineHighlight: 'all',
                               fontFamily: 'JetBrains Mono, Menlo, Monaco, Courier New, monospace',
                             }}
                          />
                       </div>
                    </div>
                 )}

                 {(editorMode === 'preview' || editorMode === 'split') && (
                    <div className="flex flex-col gap-2" style={{ minHeight: 350 }}>
                       <div className="text-[10px] text-text-muted uppercase tracking-widest flex items-center gap-1.5 bg-white/5 px-3 py-1 rounded-t-lg w-fit">
                          <Eye className="w-3 h-3" /> 即時預覽
                       </div>
                       <div className="flex-1 bg-white rounded-xl overflow-hidden border border-white/10 shadow-2xl p-4" style={{ minHeight: 350 }}>
                          <iframe
                             title="Email Preview"
                             srcDoc={form.body}
                             className="w-full h-full border-none"
                          />
                       </div>
                    </div>
                 )}
              </div>
            </div>

            {/* Bottom Save Section */}
            <div className="flex justify-end pt-4">
               <button
                  onClick={handleSave}
                  disabled={saving}
                  className="btn-primary"
               >
                  {saving ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  ) : (
                    <><Save size={16} />{editingId ? '更新模板' : '儲存模板'}</>
                  )}
               </button>
            </div>
          </div>
        )}

        {activeTab === 'list' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 className="card__title">現有模板列表</h3>
                <p className="card__subtitle">管理您所有已儲存的開發信模板</p>
              </div>
              <button onClick={fetchTemplates} className="btn-outline btn--sm">
                <RotateCcw size={13} className={loading ? 'animate-spin' : ''} />重新整理
              </button>
            </div>

            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>名稱 / 標籤</th>
                    <th>主旨</th>
                    <th>狀態</th>
                    <th style={{ textAlign: 'right' }}>管理</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr className="empty-row"><td colSpan={4}>載入中...</td></tr>
                  ) : templates.length === 0 ? (
                    <tr><td colSpan={4}>
                      <div className="empty-state">
                        <div className="empty-state__icon">📁</div>
                        <p className="empty-state__title">尚無模板資料</p>
                        <p className="empty-state__desc">點擊「建立新模板」開始建立您的第一個開發信模板</p>
                      </div>
                    </td></tr>
                  ) : templates.map(t => (
                    <tr key={t.id}>
                      <td>
                        <div style={{ fontWeight: 600, fontSize: 13 }}>{t.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--color-primary)', fontFamily: 'monospace', marginTop: 2 }}>{t.tag}</div>
                      </td>
                      <td style={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12, color: 'var(--color-text-muted)' }}>
                        {t.subject}
                      </td>
                      <td>
                        {t.is_default
                          ? <span className="badge badge--primary"><Check size={10} style={{ marginRight: 4 }} />預設</span>
                          : <span className="badge badge--neutral">一般</span>
                        }
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
                          <button onClick={() => handleEdit(t)} className="btn-icon-sm" title="編輯"><Edit size={13} /></button>
                          <button onClick={() => handleDelete(t.id)} className="btn-icon-sm danger" title="刪除"><Trash2 size={13} /></button>
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
    </div>
  );
};

export default Templates;
