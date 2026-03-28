import { Plus, Folder, Paperclip, Save, Trash2, Edit, Check, Sparkles, RotateCcw, FileCode, Eye, Layout, Languages, Type, Wand2, GitBranch } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { getTemplates, createTemplate, updateTemplate, deleteTemplate, generateAiTemplate, optimizeEmailSubject, generateABVersions } from '../services/api';
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
  
  // v3.2: AI 主旨優化
  const [subjectSuggestions, setSubjectSuggestions] = useState<string[]>([]);
  const [optimizingSubject, setOptimizingSubject] = useState(false);
  
  // v3.2: A/B 雙版本
  const [abVersions, setAbVersions] = useState<{version_a: {subject: string, body: string}, version_b: {subject: string, body: string}} | null>(null);
  const [generatingAB, setGeneratingAB] = useState(false);
  const [showABModal, setShowABModal] = useState(false);
  
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

  // v3.7: AI 輸出清洗工具 (防範 Markdown 符號與重複標籤)
  const sanitizeAiOutput = (content: string): string => {
    let cleaned = content.trim();
    
    // 1. 強力移除所有 Markdown 程式碼塊包裹
    cleaned = cleaned.replace(/^```[a-z]*\n?/i, '');
    cleaned = cleaned.replace(/```$/i, '');
    
    // 2. 移除所有 HTML 文件宣告與根標籤 (避免在主 Layout 中嵌套)
    cleaned = cleaned.replace(/<!DOCTYPE[^>]*>/gi, '');
    cleaned = cleaned.replace(/<\/?html[^>]*>/gi, '');
    cleaned = cleaned.replace(/<\/?head[^>]*>/gi, '');
    cleaned = cleaned.replace(/<\/?body[^>]*>/gi, '');
    cleaned = cleaned.replace(/<meta[^>]*>/gi, '');
    cleaned = cleaned.replace(/<link[^>]*>/gi, '');
    cleaned = cleaned.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ''); // 內部樣式由 Layout 統一提供
    cleaned = cleaned.replace(/<title[^>]*>[\s\S]*?<\/title>/gi, '');
    
    return cleaned.trim();
  };

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
        const cleanHtml = sanitizeAiOutput(data.html);
        const finalBody = `<html>\n<head>\n<style>\nbody { font-family: sans-serif; line-height: 1.6; color: #333; }\n</style>\n</head>\n<body>\n${cleanHtml}\n</body>\n</html>`;
        setForm(prev => ({ ...prev, body: finalBody, subject: data.subject || prev.subject }));
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

  // v3.2: AI 主旨優化
  const handleOptimizeSubject = async () => {
    if (!form.subject) {
      toast.error("請先填寫主旨");
      return;
    }
    setOptimizingSubject(true);
    const loadingToast = toast.loading("AI 正在優化主旨...");
    try {
      const resp = await optimizeEmailSubject(form.subject, form.name || '');
      const data = await resp.json();
      if (data.success && data.suggestions && data.suggestions.length > 0) {
        setSubjectSuggestions(data.suggestions);
        toast.success(`產生 ${data.suggestions.length} 個建議！`, { id: loadingToast });
      } else {
        toast.error(data.message || "優化失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("網路錯誤", { id: loadingToast });
    } finally {
      setOptimizingSubject(false);
    }
  };

  // v3.2: 套用選擇的主旨
  const applySubject = (subject: string) => {
    setForm(prev => ({ ...prev, subject }));
    setSubjectSuggestions([]);
    toast.success("已套用主旨");
  };

  // v3.2: A/B 雙版本生成
  const handleGenerateAB = async () => {
    if (!form.name && !aiPrompt) {
      toast.error("請填寫公司名稱或描述內容");
      return;
    }
    setGeneratingAB(true);
    const loadingToast = toast.loading("AI 正在生成 A/B 雙版本...");
    try {
      const resp = await generateABVersions(
        form.name || aiPrompt.slice(0, 50),
        form.tag,
        []
      );
      const data = await resp.json();
      if (data.success && data.version_a && data.version_b) {
        setAbVersions(data);
        setShowABModal(true);
        toast.success("A/B 版本已生成！", { id: loadingToast });
      } else {
        toast.error(data.message || "生成失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("網路錯誤", { id: loadingToast });
    } finally {
      setGeneratingAB(false);
    }
  };

  // v3.2: 套用選擇的 A/B 版本
  const applyABVersion = (version: 'version_a' | 'version_b') => {
    if (!abVersions) return;
    const v = abVersions[version];
    const cleanBody = sanitizeAiOutput(v.body);
    setForm(prev => ({ 
      ...prev, 
      subject: v.subject, 
      body: `<html>\n<head>\n<style>\nbody { font-family: sans-serif; line-height: 1.6; color: #333; }\n</style>\n</head>\n<body>\n${cleanBody}\n<p>Corelink From Concept to Connect</p>\n</body>\n</html>` 
    }));
    setShowABModal(false);
    setAbVersions(null);
    setEditorMode('split');
    toast.success(`已套用版本 ${version === 'version_a' ? 'A' : 'B'}`);
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
            <span className="version-badge">LINKORA V3.2 (AI Scripts)</span>
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
                {/* v3.2: 主旨輸入 + AI 優化按鈕 */}
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    value={form.subject}
                    onChange={e => setForm({...form, subject: e.target.value})}
                    placeholder="Hello {{company_name}}, interesting opportunity for you"
                    className="form-input flex-1"
                  />
                  <button
                    onClick={handleOptimizeSubject}
                    disabled={optimizingSubject || !form.subject}
                    className="btn-outline btn--sm flex items-center gap-1.5 flex-shrink-0"
                    style={{ borderColor: 'var(--color-accent-teal)', color: 'var(--color-accent-teal)' }}
                    title="AI 優化主旨"
                  >
                    {optimizingSubject ? <RotateCcw className="w-3.5 h-3.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5" />}
                    ✨ 優化
                  </button>
                </div>
                {/* v3.2: AI 建議主旨 */}
                {subjectSuggestions.length > 0 && (
                  <div className="bg-accent-teal/5 border border-accent-teal/20 rounded-xl p-4 space-y-2">
                    <div className="text-xs font-bold text-accent-teal mb-2">✨ AI 建議主旨（點擊套用）</div>
                    {subjectSuggestions.map((s, i) => (
                      <div
                        key={i}
                        onClick={() => applySubject(s)}
                        className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-white/5 cursor-pointer transition-all group"
                      >
                        <span className={`w-5 h-5 rounded border flex items-center justify-center text-[10px] font-black flex-shrink-0 ${
                          i === 0 ? 'border-accent-teal text-accent-teal' : 'border-white/20 text-text-muted'
                        }`}>{String.fromCharCode(65 + i)}</span>
                        <span className="text-xs text-white group-hover:text-accent-teal transition-colors flex-1">{s}</span>
                        <span className="text-[9px] text-text-muted opacity-0 group-hover:opacity-100 transition-opacity">套用 →</span>
                      </div>
                    ))}
                  </div>
                )}
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
                          AI 生成 HTML
                       </button>
                       {/* v3.2: A/B 雙版本生成 */}
                       <button
                          onClick={handleGenerateAB}
                          disabled={generatingAB}
                          className="bg-accent-teal/10 hover:bg-accent-teal/20 border border-accent-teal/30 text-accent-teal px-4 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 disabled:opacity-50"
                          title="生成理性版與感性版供 A/B 測試"
                       >
                          {generatingAB ? <RotateCcw className="w-3.5 h-3.5 animate-spin" /> : <GitBranch className="w-3.5 h-3.5" />}
                          ⚡ A/B 雙版本
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

            {/* v3.2: A/B 雙版本 Modal */}
            {showABModal && abVersions && (
              <>
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={() => setShowABModal(false)} />
                <div className="fixed inset-4 md:inset-10 z-50 flex items-center justify-center">
                  <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-5xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col">
                    {/* Modal Header */}
                    <div className="p-6 border-b border-white/10 flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-black text-white flex items-center gap-2">
                          <GitBranch className="w-5 h-5 text-accent-teal" />
                          A/B 測試雙版本
                        </h3>
                        <p className="text-xs text-text-muted mt-1">版本 A 為理性/數據型，版本 B 為故事/情感型。選擇一個套用。</p>
                      </div>
                      <button onClick={() => setShowABModal(false)} className="btn-icon-sm">✕</button>
                    </div>
                    {/* Modal Body */}
                    <div className="flex-1 overflow-y-auto p-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Version A */}
                        <div className="border border-blue-500/30 rounded-2xl overflow-hidden bg-blue-500/5">
                          <div className="bg-blue-500/10 px-5 py-3 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="bg-blue-500 text-white text-xs font-black w-6 h-6 rounded flex items-center justify-center">A</span>
                              <span className="font-bold text-blue-400 text-sm">理性 / 數據型</span>
                            </div>
                            <span className="text-[9px] text-blue-400/60 uppercase tracking-widest">Data-Driven</span>
                          </div>
                          <div className="p-5 space-y-3">
                            <div>
                              <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1">主旨</div>
                              <div className="text-sm font-bold text-white bg-white/5 rounded-lg p-3">{abVersions.version_a.subject}</div>
                            </div>
                            <div>
                              <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1">內容預覽</div>
                              <div className="text-xs text-slate-300 bg-white/5 rounded-lg p-3 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">{abVersions.version_a.body}</div>
                            </div>
                            <button
                              onClick={() => applyABVersion('version_a')}
                              className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-xl text-xs font-black transition-all"
                            >
                              使用版本 A
                            </button>
                          </div>
                        </div>
                        {/* Version B */}
                        <div className="border border-amber-500/30 rounded-2xl overflow-hidden bg-amber-500/5">
                          <div className="bg-amber-500/10 px-5 py-3 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="bg-amber-500 text-white text-xs font-black w-6 h-6 rounded flex items-center justify-center">B</span>
                              <span className="font-bold text-amber-400 text-sm">故事 / 情感型</span>
                            </div>
                            <span className="text-[9px] text-amber-400/60 uppercase tracking-widest">Story-Driven</span>
                          </div>
                          <div className="p-5 space-y-3">
                            <div>
                              <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1">主旨</div>
                              <div className="text-sm font-bold text-white bg-white/5 rounded-lg p-3">{abVersions.version_b.subject}</div>
                            </div>
                            <div>
                              <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1">內容預覽</div>
                              <div className="text-xs text-slate-300 bg-white/5 rounded-lg p-3 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">{abVersions.version_b.body}</div>
                            </div>
                            <button
                              onClick={() => applyABVersion('version_b')}
                              className="w-full bg-amber-600 hover:bg-amber-500 text-white py-2.5 rounded-xl text-xs font-black transition-all"
                            >
                              使用版本 B
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
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
