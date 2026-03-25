import React, { useState, useEffect } from 'react';
import Editor from "@monaco-editor/react";
import { getTemplates, createTemplate, updateTemplate, deleteTemplate } from '../services/api';
import { Plus, Folder, Paperclip, Save, Trash2, Edit, Check, Sparkles } from 'lucide-react';

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
  
  // Edit State
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

  const handleSave = async () => {
    if (!form.name || !form.subject) {
      alert("請填寫模板名稱與主旨");
      return;
    }
    setSaving(true);
    try {
      let resp;
      if (editingId) {
        resp = await updateTemplate(editingId, form);
      } else {
        resp = await createTemplate(form);
      }
      
      if (resp.ok) {
        setEditingId(null);
        setForm({ name: '', tag: 'GENERAL', subject: '', body: '<html><body></body></html>', is_default: false });
        setActiveTab('list');
        fetchTemplates();
      } else {
        const err = await resp.json();
        alert(err.detail || "儲存失敗");
      }
    } catch (e) {
      alert("網路錯誤");
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

      <div className="flex-1 overflow-hidden min-h-0">
        {activeTab === 'create' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
            {/* Left: AI Generation + Monaco Editor */}
            <section className="glass-panel p-5 flex flex-col gap-4 overflow-hidden border border-white/10">
              <div className="bg-primary/10 p-4 rounded-xl border border-primary/20">
                <h4 className="font-semibold text-sm mb-1 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" /> AI 智慧輔助生成
                </h4>
                <p className="text-[10px] text-text-muted mb-3">使用 AI 快速生成專業 HTML 郵件版型</p>
                <div className="flex gap-2">
                  <input 
                    placeholder="描述信件目的..."
                    className="flex-1 bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white"
                  />
                  <button className="bg-primary hover:bg-primary-dark text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all">
                    生成
                  </button>
                </div>
              </div>

              <div className="flex flex-col flex-1 gap-2 min-h-0">
                <div className="text-[11px] text-text-muted mb-1 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                    HTML 原始碼編輯器
                  </span>
                  <span className="font-mono opacity-50">Monaco Editor</span>
                </div>
                <div className="flex-1 rounded-xl overflow-hidden border border-white/10 shadow-inner">
                  <Editor
                    height="100%"
                    defaultLanguage="html"
                    theme="vs-dark"
                    value={form.body}
                    onChange={(val) => setForm({...form, body: val || ''})}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 13,
                      lineNumbers: 'on',
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                    }}
                  />
                </div>
              </div>
            </section>

            {/* Right: Template Settings */}
            <section className="glass-panel p-6 overflow-y-auto border border-white/10">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-xl font-bold text-white">⚙️ 模板詳細內容設定</h3>
                  <p className="text-xs text-text-muted mt-1">設定模板名稱、標籤與郵件主旨</p>
                </div>
                {editingId && (
                  <span className="bg-yellow-500/10 text-yellow-500 text-[10px] px-2 py-1 rounded border border-yellow-500/20">
                    編輯模式 (ID: {editingId})
                  </span>
                )}
              </div>
              
              <div className="space-y-5">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-muted ml-0.5">模板顯示名稱 *</label>
                  <input 
                    required
                    type="text" 
                    value={form.name}
                    onChange={e => setForm({...form, name: e.target.value})}
                    placeholder="例如：第一階段開發信 - 北美市場"
                    className="input-field" 
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-muted ml-0.5">分類標籤</label>
                    <input 
                      value={form.tag}
                      onChange={e => setForm({...form, tag: e.target.value})}
                      placeholder="GENERAL"
                      className="input-field" 
                    />
                  </div>
                  <div className="space-y-2 flex flex-col justify-end pb-2">
                    <label className="flex items-center gap-2 cursor-pointer text-sm select-none">
                      <input 
                        type="checkbox" 
                        className="w-4 h-4 accent-primary"
                        checked={form.is_default}
                        onChange={e => setForm({...form, is_default: e.target.checked})}
                      />
                      設為該標籤的預設模板
                    </label>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-muted ml-0.5">郵件主旨 (Subject) *</label>
                  <input 
                    required
                    type="text" 
                    value={form.subject}
                    onChange={e => setForm({...form, subject: e.target.value})}
                    placeholder="Hello {{company_name}}, special offer for you"
                    className="input-field" 
                  />
                  <p className="text-[10px] text-text-muted italic">提示：可使用 <code>{"{{company_name}}"}</code> 等變數</p>
                </div>
              </div>

              <div className="mt-10 pt-6 border-t border-white/5">
                <button 
                  onClick={handleSave}
                  disabled={saving}
                  className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white py-3 rounded-xl font-bold transition-all shadow-xl shadow-primary/20 disabled:opacity-50"
                >
                  {saving ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <Save className="w-5 h-5" />
                      {editingId ? '更新模板' : '儲存新模板'}
                    </>
                  )}
                </button>
              </div>
            </section>
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
