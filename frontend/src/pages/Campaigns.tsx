import React, { useState, useEffect } from 'react';

const Campaigns: React.FC = () => {
  const [campaigns, setCampaigns] = useState<any[]>([]);

  useEffect(() => {
    // Placeholder to use setCampaigns
    if (campaigns.length < 0) setCampaigns([]);
  }, [campaigns]);

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Feature Card: SMTP Warning (Hidden by default, shown if no SMTP) */}
      <div className="glass-panel p-4 border-l-4 border-warning bg-warning/5 flex justify-between items-center">
        <div>
          <div className="font-semibold text-warning mb-1">⚠️ SMTP 尚未設定，目前無法寄信</div>
          <div className="text-sm text-text-muted">完成設定後才能發送開發信</div>
        </div>
        <button className="bg-gradient-to-br from-warning to-orange-500 text-white py-2 px-4 rounded-lg font-medium">
          前往 SMTP 設定 →
        </button>
      </div>

      {/* Feature Card: Filters */}
      <div className="glass-panel p-4 flex gap-3 items-center flex-wrap">
        <select className="p-2.5 rounded-lg bg-black/25 border border-glass-border text-white text-sm outline-none focus:border-primary">
          <option value="">所有狀態</option>
          <option value="Sent">已寄出</option>
          <option value="Delivered">已送達</option>
          <option value="Opened">已開信</option>
          <option value="Clicked">已點擊</option>
          <option value="Replied">已回覆</option>
          <option value="Bounced">退信</option>
          <option value="Failed">失敗</option>
        </select>
        <input type="date" className="p-2.5 rounded-lg bg-black/25 border border-glass-border text-white text-sm outline-none focus:border-primary" />
        <span className="text-text-muted text-sm">至</span>
        <input type="date" className="p-2.5 rounded-lg bg-black/25 border border-glass-border text-white text-sm outline-none focus:border-primary" />
        <input type="text" placeholder="搜尋主旨/公司..." className="flex-1 min-w-[150px] p-2.5 rounded-lg bg-black/25 border border-glass-border text-white text-sm outline-none focus:border-primary" />
        <button className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-text-muted hover:text-white transition-colors">↺</button>
      </div>

      {/* Feature Card: Table */}
      <div className="glass-panel flex-1 flex flex-col overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-text-muted text-sm">
                <th className="p-3 w-10"><input type="checkbox" className="accent-primary" /></th>
                <th className="p-3">時間</th>
                <th className="p-3">目標公司</th>
                <th className="p-3">Email</th>
                <th className="p-3">主旨</th>
                <th className="p-3">狀態</th>
                <th className="p-3 w-[100px]">操作</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-text-muted">
                    尚無寄信記錄
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Campaigns;
