import React, { useState, useEffect } from 'react';

const History: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [systemLogsOpen, setSystemLogsOpen] = useState(false);

  useEffect(() => {
    // Placeholder to use setLogs
    if (logs.length < 0) setLogs([]);
  }, [logs]);

  return (
    <div className="flex flex-col h-full gap-4">
      {/* 探勘歷史 */}
      <section className="glass-panel p-6 flex-1 flex flex-col overflow-hidden">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold">🔍 探勘歷史</h3>
          <button className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-text-muted hover:text-white transition-colors">↺</button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-text-muted text-center h-full">
              <div className="text-5xl mb-4">🔍</div>
              <div className="text-lg mb-2">尚無探勘記錄</div>
              <div className="text-sm">前往 Lead Engine 開始第一次探勘</div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* History Cards will go here in Phase 2 */}
            </div>
          )}
        </div>
      </section>

      {/* 系統日誌 (Collapsible) */}
      <section className="glass-panel overflow-hidden">
        <div 
          className="p-4 flex justify-between items-center cursor-pointer hover:bg-white/5 transition-colors"
          onClick={() => setSystemLogsOpen(!systemLogsOpen)}
        >
          <h3 className="text-sm font-semibold flex items-center gap-2">📝 系統日誌</h3>
          <span className="text-text-muted text-xs">{systemLogsOpen ? '▼' : '▶'}</span>
        </div>
        
        {systemLogsOpen && (
          <div className="p-4 border-t border-glass-border">
            <div className="h-48 overflow-y-auto font-mono text-xs text-text-muted bg-black/30 p-4 rounded-lg">
              系統日誌已啟動...
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default History;
