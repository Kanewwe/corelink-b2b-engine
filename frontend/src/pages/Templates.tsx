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
  const [activeTab, setActiveTab] = useState<'create' | 'list' | 'attachments'>('list');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
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

  useEffect(() => {
    fetchTemplates();
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
    if (!confirm("確定要刪除此模板嗎？")) return;
    try {
      const resp = await deleteTemplate(id);
      if (resp.ok) fetchTemplates();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Tab Navigation */}
      <div className="flex gap-3 border-b border-white/10 pb-3">
        <button 
          onClick={() => setActiveTab('list')}
          className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-all ${activeTab === 'list' ? 'bg-primary/20 text-white border border-primary/30' : 'bg-white/5 text-text-muted hover:bg-white/10'}`}
        >
          <Folder className="w-4 h-4" /> 現有模板
        </button>
        <button 
          onClick={() => {
            setEditingId(null);
            setForm({ name: '', tag: 'GENERAL', subject: '', body: '<html><body></body></html>', is_default: false });
            setActiveTab('create');
          }}
          className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-all ${activeTab === 'create' ? 'bg-primary/20 text-white border border-primary/30' : 'bg-white/5 text-text-muted hover:bg-white/10'}`}
        >
          <Plus className="w-4 h-4" /> {editingId ? '編輯模板' : '建立新模板'}
        </button>
        <button 
          onClick={() => setActiveTab('attachments')}
          className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-all ${activeTab === 'attachments' ? 'bg-primary/20 text-white border border-primary/30' : 'bg-white/5 text-text-muted hover:bg-white/10'}`}
        >
          <Paperclip className="w-4 h-4" /> 附件管理
        </button>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 pr-1">
        {activeTab === 'create' && (
          <div className="flex flex-col gap-6 pb-10">
            {/* Top Section: Basic Info */}
            <section className="glass-panel p-6 border border-white/10 shadow-xl">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    {editingId ? '📝 編輯模板內容' : '✨ 建立新行銷模板'}
                  </h3>
                  <p className="text-xs text-text-muted mt-1">請先填寫模板基本資訊，然後在下方編輯 HTML 原始碼</p>
                </div>
                {editingId && (
                  <span className="bg-primary/20 text-primary text-[10px] px-3 py-1 rounded-full border border-primary/30 font-bold uppercase tracking-wider">
                    Editing Mode
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-text-muted uppercase tracking-widest ml-1">模板名稱 *</label>
                  <input 
                    type="text" 
                    value={form.name}
                    onChange={e => setForm({...form, name: e.target.value})}
                    placeholder="例如：北美開發信-V1"
                    className="input-field py-2.5" 
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-text-muted uppercase tracking-widest ml-1">分類標籤</label>
                  <input 
                    value={form.tag}
                    onChange={e => setForm({...form, tag: e.target.value})}
                    placeholder="GENERAL"
                    className="input-field py-2.5" 
                  />
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
                  className="input-field py-2.5 font-medium" 
                />
                <p className="text-[10px] text-text-muted flex items-center gap-1.5 mt-2">
                  <span className="bg-white/10 px-1.5 py-0.5 rounded text-white flex items-center">Tip</span>
                  支援變數動態替換：<code>{"{{company_name}}"}</code>, <code>{"{{contact_name}}"}</code>
                </p>
              </div>
            </section>

            {/* Middle Section: Advanced Controller & Monaco Editor */}
            <section className="glass-panel p-5 border border-white/10 shadow-2xl flex flex-col gap-5">
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
                    className="w-full h-24 bg-black/30 border border-white/10 rounded-xl p-4 text-sm text-white focus:border-primary/50 outline-none transition-all resize-none mb-4 placeholder:text-text-muted/30"
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
                                className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white outline-none focus:border-primary/50 capitalize appearance-none"
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
                                className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white outline-none focus:border-primary/50 appearance-none"
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
                 <span className="text-[10px] text-text-muted font-bold uppercase tracking-wider mr-1">變數插入：</span>
                 {['company_name', 'bd_name', 'keywords', 'description'].map(v => (
                    <button 
                       key={v}
                       onClick={() => insertVariable(v)}
                       className="bg-primary/10 border border-primary/20 text-primary-light text-[10px] px-2.5 py-1 rounded-md hover:bg-primary/20 transition-colors font-mono"
                    >
                       `{`{{${v}}}`}`
                    </button>
                 ))}
              </div>

              {/* Editor / Preview Area */}
              <div className={`grid gap-4 ${editorMode === 'split' ? 'grid-cols-2' : 'grid-cols-1'}`}>
                 {(editorMode === 'html' || editorMode === 'split') && (
                    <div className="flex flex-col gap-2 min-h-[400px]">
                       <div className="text-[10px] text-text-muted uppercase tracking-widest flex items-center gap-1.5 bg-white/5 px-3 py-1 rounded-t-lg w-fit">
                          <FileCode className="w-3 h-3" /> HTML 編輯器
                       </div>
                       <div className="flex-1 border border-white/10 rounded-xl overflow-hidden shadow-2xl">
                          <Editor
                             height="100%"
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
                    <div className="flex flex-col gap-2 min-h-[400px]">
                       <div className="text-[10px] text-text-muted uppercase tracking-widest flex items-center gap-1.5 bg-white/5 px-3 py-1 rounded-t-lg w-fit">
                          <Eye className="w-3 h-3" /> 即時預覽
                       </div>
                       <div className="flex-1 bg-white rounded-xl overflow-hidden border border-white/10 shadow-2xl p-4">
                          <iframe 
                             title="Email Preview"
                             srcDoc={form.body}
                             className="w-full h-full border-none"
                          />
                       </div>
                    </div>
                 )}
              </div>
            </section>

            {/* Bottom Save Section */}
            <div className="flex justify-end pt-4">
               <button 
                  onClick={handleSave}
                  disabled={saving}
                  className="px-12 h-16 flex items-center justify-center gap-3 bg-gradient-to-r from-primary to-primary-dark hover:from-primary-dark hover:to-primary text-white rounded-2xl font-black text-lg transition-all shadow-2xl shadow-primary/30 disabled:opacity-50 group active:scale-[0.98]"
               >
                  {saving ? (
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <Save className="w-6 h-6 group-hover:scale-110 transition-transform" />
                      {editingId ? '更新模板內容' : '確認儲存模板'}
                    </>
                  )}
               </button>
            </div>
          </div>
        )}

        {activeTab === 'list' && (
          <section className="glass-panel p-6 h-full flex flex-col border border-white/10 overflow-hidden">
            <header className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-xl font-bold text-white">現有模板列表</h3>
                <p className="text-xs text-text-muted mt-1">管理您所有已儲存的開發信模板</p>
              </div>
              <button 
                onClick={fetchTemplates}
                className="p-2 hover:bg-white/5 rounded-lg text-text-muted transition-colors"
                title="重新整理"
              >
                <Plus className={`w-5 h-5 transition-transform ${loading ? 'animate-spin' : ''}`} />
              </button>
            </header>

            <div className="flex-1 overflow-y-auto min-h-0 -mx-6 px-6">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-bg-dark/80 backdrop-blur-md z-10">
                  <tr className="text-text-muted text-[11px] uppercase tracking-wider border-b border-white/10">
                    <th className="py-4 font-semibold">名稱 / 標籤</th>
                    <th className="py-4 font-semibold">主旨</th>
                    <th className="py-4 font-semibold">狀態</th>
                    <th className="py-4 font-semibold text-right">管理</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {loading ? (
                    <tr>
                      <td colSpan={4} className="py-10 text-center text-text-muted text-sm">載入中...</td>
                    </tr>
                  ) : templates.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-16 text-center">
                        <div className="text-4xl mb-3">📁</div>
                        <div className="text-text-muted text-sm">尚無模板資料，點擊「建立新模板」開始吧！</div>
                      </td>
                    </tr>
                  ) : (
                    templates.map(t => (
                      <tr key={t.id} className="hover:bg-white/[0.02] transition-colors group">
                        <td className="py-4">
                          <div className="font-medium text-white text-sm">{t.name}</div>
                          <div className="text-[10px] text-primary-light font-mono mt-0.5">{t.tag}</div>
                        </td>
                        <td className="py-4 max-w-xs truncate text-xs text-text-muted">
                          {t.subject}
                        </td>
                        <td className="py-4">
                          {t.is_default ? (
                            <span className="bg-primary/10 text-primary text-[10px] px-2 py-1 rounded-full border border-primary/20 flex items-center w-fit gap-1">
                              <Check className="w-3 h-3" /> 預設
                            </span>
                          ) : (
                            <span className="text-[10px] text-text-muted px-2 py-1">一般</span>
                          )}
                        </td>
                        <td className="py-4 text-right">
                          <div className="flex justify-end gap-1 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity">
                            <button 
                              onClick={() => handleEdit(t)}
                              className="p-2 hover:bg-blue-500/10 rounded-lg text-blue-400 transition-colors"
                              title="編輯"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => handleDelete(t.id)}
                              className="p-2 hover:bg-red-500/10 rounded-lg text-red-400 transition-colors"
                              title="刪除"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {activeTab === 'attachments' && (
          <section className="glass-panel p-6 h-full flex flex-col border border-white/10">
            <h3 className="text-xl font-bold mb-4">📎 附件管理中心</h3>
            <div className="border-2 border-dashed border-white/10 rounded-2xl p-16 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-primary/5 hover:border-primary/30 transition-all group">
              <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Paperclip className="w-8 h-8 text-text-muted" />
              </div>
              <div className="font-bold text-white mb-2">拖曳檔案到此處，或點擊上傳</div>
              <div className="text-xs text-text-muted max-w-xs mx-auto leading-relaxed">
                支援：PDF、DOCX、XLSX、PPT、PNG、JPG<br />
                單檔限制：10MB | 附件將可用於行銷郵件
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default Templates;
