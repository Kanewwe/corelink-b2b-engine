import React from 'react';

const Analytics: React.FC = () => {
  return (
    <div className="flex flex-col h-full gap-4">
      <div className="grid grid-cols-2 gap-6 flex-1">
        {/* Left: Tag Stats */}
        <section className="glass-panel p-6 overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-semibold">📊 各行業界別觸及統計</h3>
            <button className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-text-muted hover:text-white transition-colors">↺</button>
          </div>
          <div className="flex flex-col items-center justify-center h-48 text-text-muted">
            [Chart Placeholder]
          </div>
        </section>

        {/* Right: Pricing Settings (Legacy view, will be replaced by Phase 4 logic) */}
        <section className="glass-panel p-6 overflow-y-auto">
          <h3 className="text-xl font-semibold mb-2">💰 收費標準設定</h3>
          <p className="text-sm text-text-muted mb-6">用於內部報價參考，可隨時調整</p>
          
          <form className="flex flex-col gap-4">
            <div>
              <label className="block text-sm text-text-muted mb-1">基本費用 (Base Fee)</label>
              <input type="number" required className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg text-white outline-none focus:border-primary" />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1">每筆客戶費用</label>
              <input type="number" required className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg text-white outline-none focus:border-primary" />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1">開信追蹤費用</label>
              <input type="number" required className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg text-white outline-none focus:border-primary" />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1">點擊追蹤費用</label>
              <input type="number" required className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg text-white outline-none focus:border-primary" />
            </div>
            
            <button type="submit" className="btn-primary mt-4">💾 儲存收費標準</button>
          </form>
        </section>
      </div>
    </div>
  );
};

export default Analytics;
