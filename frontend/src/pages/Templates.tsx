import React, { useState } from 'react';

const Templates: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'create' | 'list' | 'attachments'>('create');

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Tab Navigation */}
      <div className="flex gap-3 border-b border-glass-border pb-3">
        <button 
          onClick={() => setActiveTab('create')}
          className={`px-4 py-2 rounded-lg text-sm transition-all ${activeTab === 'create' ? 'bg-primary/20 text-white' : 'bg-white/5 text-text-muted hover:bg-white/10'}`}
        >
          📝 建立/編輯模板
        </button>
        <button 
          onClick={() => setActiveTab('list')}
          className={`px-4 py-2 rounded-lg text-sm transition-all ${activeTab === 'list' ? 'bg-primary/20 text-white' : 'bg-white/5 text-text-muted hover:bg-white/10'}`}
        >
          📁 現有模板
        </button>
        <button 
          onClick={() => setActiveTab('attachments')}
          className={`px-4 py-2 rounded-lg text-sm transition-all ${activeTab === 'attachments' ? 'bg-primary/20 text-white' : 'bg-white/5 text-text-muted hover:bg-white/10'}`}
        >
          📎 附件管理
        </button>
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === 'create' && (
          <div className="grid grid-cols-2 gap-6 h-full">
            {/* Left: AI Generation + Monaco Editor */}
            <section className="glass-panel p-6 flex flex-col gap-4 overflow-hidden">
              <div className="bg-indigo-500/10 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">🤖 AI 智慧生成信件排版</h4>
                <p className="text-xs text-text-muted mb-3">描述你的信件目的，AI 自動排版為專業 HTML 開發信</p>
                <textarea 
                  rows={3} 
                  placeholder="例如：我要寫一封針對美國汽車零件採購商的開發信..."
                  className="w-full p-3 bg-black/25 border border-glass-border rounded-lg text-white mb-3"
                ></textarea>
                <div className="flex gap-4 items-center">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-text-muted">風格：</span>
                    <select className="bg-black/25 text-sm p-1 rounded border border-glass-border text-white">
                      <option>正式</option>
                      <option>親切</option>
                    </select>
                  </div>
                  <button className="btn-primary py-1.5 px-4 text-sm w-auto">✨ 生成</button>
                </div>
              </div>

              <div className="flex flex-col flex-1 gap-2 min-h-0">
                <div className="text-xs text-text-muted mb-1 flex items-center justify-between">
                  <span>HTML 編輯器 (Monaco)</span>
                  <div className="flex gap-2">
                     <button className="bg-white/10 px-2 py-1 rounded">格式化</button>
                  </div>
                </div>
                <div className="flex-1 bg-[#1e1e1e] rounded-lg border border-glass-border p-4 flex items-center justify-center text-text-muted text-sm relative">
                  [Monaco Editor Component Goes Here]
                  {/* Implementing a full monaco wrapper will be part of fine-tuning, leaving placeholder for layout scaffolding */}
                </div>
              </div>
            </section>

            {/* Right: Template Settings */}
            <section className="glass-panel p-6 overflow-y-auto">
              <h3 className="text-xl font-semibold mb-6">⚙️ 模板設定</h3>
              
              <div className="flex flex-col gap-4">
                <div>
                  <label className="block text-sm text-text-muted mb-1">模板名稱 *</label>
                  <input type="text" className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg text-white focus:border-primary" />
                </div>
                <div>
                  <label className="block text-sm text-text-muted mb-1">適用標籤 *</label>
                  <select className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg text-white focus:border-primary">
                    <option>NA-CABLE (Cable)</option>
                    <option>AUTO-PARTS (汽車零件)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-text-muted mb-1">信件主旨 *</label>
                  <input type="text" className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg text-white focus:border-primary" />
                </div>
              </div>

              <div className="mt-8 flex gap-4 items-center">
                <button className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white py-2.5 px-6 rounded-lg font-semibold hover:-translate-y-0.5 transition-all">
                  💾 儲存模板
                </button>
                <label className="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="checkbox" className="accent-primary" />
                  設為預設
                </label>
              </div>
            </section>
          </div>
        )}

        {activeTab === 'list' && (
           <div className="glass-panel p-6 h-full flex flex-col">
              <h3 className="text-xl font-semibold mb-4">現有模板</h3>
              <div className="flex-1 flex items-center justify-center text-text-muted text-lg">
                 📋 List Component Placerholder
              </div>
           </div>
        )}

        {activeTab === 'attachments' && (
           <div className="glass-panel p-6 h-full flex flex-col">
              <h3 className="text-xl font-semibold mb-4">📎 附件管理</h3>
              <div className="border-2 border-dashed border-white/20 rounded-xl p-16 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-primary/5 hover:border-primary/50 transition-all">
                 <div className="text-5xl mb-4">📁</div>
                 <div className="font-medium mb-2">拖曳檔案到此處，或點擊上傳</div>
                 <div className="text-xs text-text-muted">支援：PDF、DOCX、XLSX、PPT、PNG、JPG | 單檔限制：10MB</div>
              </div>
           </div>
        )}
      </div>
    </div>
  );
};

export default Templates;
