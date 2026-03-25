import { Plus, Folder, Paperclip, Save, Trash2, Edit, Check, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'react-hot-toast';

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
  
  const [aiExpanded, setAiExpanded] = useState(false);
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

            {/* Middle Section: Monaco Editor (Main Work Area) */}
            <section className="glass-panel p-0 overflow-hidden border border-white/10 shadow-2xl">
              <div className="bg-white/[0.03] px-5 py-3 border-b border-white/5 flex justify-between items-center">
                <span className="text-[11px] font-bold text-text-muted uppercase tracking-widest flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                  HTML Source Code Editor (Monaco)
                </span>
                <span className="text-[10px] text-text-muted italic opacity-50">Auto-layout enabled</span>
              </div>
              <div className="h-[450px] relative">
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
            </section>

            {/* Bottom Section: AI Assistant & Save */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
              <section className="lg:col-span-2 glass-panel p-5 border border-white/10">
                <button 
                  onClick={() => setAiExpanded(!aiExpanded)}
                  className="w-full flex justify-between items-center group"
                >
                  <div className="text-left">
                    <h4 className="font-bold text-sm text-white flex items-center gap-2 group-hover:text-primary transition-colors">
                      <Sparkles className="w-4 h-4 text-primary" /> AI 智慧輔助生成工具
                    </h4>
                    <p className="text-[10px] text-text-muted mt-0.5">快速產生專業的開發信內文範本</p>
                  </div>
                  {aiExpanded ? <ChevronUp className="w-5 h-5 text-text-muted" /> : <ChevronDown className="w-5 h-5 text-text-muted" />}
                </button>

                {aiExpanded && (
                  <div className="mt-5 animate-in slide-in-from-top-2 duration-300">
                    <div className="flex gap-3">
                      <input 
                        placeholder="請輸入產品類型或信件目的，例如：AI 客服外包、北美市場開發..."
                        className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:border-primary/50 transition-all outline-none"
                      />
                      <button className="bg-primary hover:bg-primary-dark text-white px-6 py-2.5 rounded-xl text-xs font-bold transition-all shadow-lg shadow-primary/20">
                        立即生成
                      </button>
                    </div>
                    <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
                      {['正式商務', '親切感隨和', '急迫感行銷', '後續追蹤'].map(tag => (
                        <span key={tag} className="flex-shrink-0 text-[10px] bg-white/5 border border-white/5 px-2 py-1 rounded-md text-text-muted cursor-pointer hover:bg-white/10 transition-colors">
                          # {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </section>

              <section className="flex flex-col gap-4">
                <button 
                  onClick={handleSave}
                  disabled={saving}
                  className="w-full h-[68px] flex items-center justify-center gap-3 bg-gradient-to-r from-primary to-primary-dark hover:from-primary-dark hover:to-primary text-white rounded-2xl font-black text-lg transition-all shadow-2xl shadow-primary/30 disabled:opacity-50 group active:scale-[0.98]"
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
                <button 
                  onClick={() => {
                    setActiveTab('list');
                    setEditingId(null);
                  }}
                  className="w-full py-3 text-xs text-text-muted hover:text-white transition-colors text-center"
                >
                  取消並回到列表
                </button>
              </section>
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
