import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSearchHistory } from '../services/api';
import { Search, RotateCw, Download, ChevronDown, ChevronUp, Clock, CheckCircle, XCircle } from 'lucide-react';

interface ScrapeTask {
  id: number;
  market: string;
  keywords: string;
  miner_mode: string;
  pages_requested: number;
  status: string;
  leads_found: number;
  started_at: string;
  completed_at: string;
}

const History: React.FC = () => {
  const [tasks, setTasks] = useState<ScrapeTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const resp = await getSearchHistory();
      if (resp.ok) {
        const data = await resp.json();
        setTasks(data);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleReimport = (task: ScrapeTask) => {
    alert(`Re-importing task ID ${task.id} (${task.keywords}). This would dispatch a new mining job.`);
  };

  const handleDownloadCsv = (task: ScrapeTask) => {
    alert(`Downloading CSV for task ID ${task.id} (${task.keywords}).`);
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'running': return <RotateCw className="w-5 h-5 text-blue-400 animate-spin" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="flex flex-col h-full gap-4">
      {/* 探勘歷史 */}
      <section className="glass-panel p-6 flex-1 flex flex-col overflow-hidden">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold flex items-center gap-2">
            <Search className="w-5 h-5 text-primary" />
            探勘任務歷史記錄
          </h3>
          <button 
            onClick={fetchHistory}
            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-text-muted hover:text-white transition-colors flex items-center gap-1 text-sm font-medium"
          >
            <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            更新列表
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto pr-2">
          {loading && tasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-text-muted">
              <RotateCw className="w-8 h-8 animate-spin mb-4" />
              <div>載入中...</div>
            </div>
          ) : tasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-text-muted text-center h-full">
              <div className="text-6xl mb-6 opacity-20">🔍</div>
              <div className="text-xl font-bold text-white mb-2">尚無探勘記錄</div>
              <Link 
                to="/lead-engine" 
                className="text-primary hover:text-primary-light hover:underline transition-all flex items-center gap-1 group"
              >
                前往 Lead Engine 開始第一次探勘
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {tasks.map((task) => (
                <div key={task.id} className="bg-white/5 border border-white/10 rounded-xl overflow-hidden transition-all hover:border-primary/50">
                  <div 
                    className="p-4 flex items-center justify-between cursor-pointer"
                    onClick={() => setExpandedId(expandedId === task.id ? null : task.id)}
                  >
                    <div className="flex items-center gap-4">
                      {getStatusIcon(task.status)}
                      <div>
                        <div className="font-semibold text-white drop-shadow-sm flex items-center gap-2">
                          {task.keywords.split(',').join(', ')}
                          <span className="text-xs font-normal text-text-muted bg-white/10 px-2 py-0.5 rounded-full">
                            {task.miner_mode}
                          </span>
                        </div>
                        <div className="text-sm text-text-muted flex items-center gap-4 mt-1">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {task.started_at}
                          </span>
                          <span>|</span>
                          <span className="text-primary-light font-medium">{task.leads_found} 筆資料</span>
                          <span>|</span>
                          <span>市場: {task.market}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2 opacity-80 hover:opacity-100">
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleReimport(task); }}
                          className="flex items-center gap-1 text-xs px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/40 text-blue-200 rounded-lg transition-colors border border-blue-500/30"
                        >
                          <RotateCw className="w-3 h-3" />
                          重新匯入
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleDownloadCsv(task); }}
                          className="flex items-center gap-1 text-xs px-3 py-1.5 bg-green-500/20 hover:bg-green-500/40 text-green-200 rounded-lg transition-colors border border-green-500/30"
                        >
                          <Download className="w-3 h-3" />
                          下載 CSV
                        </button>
                      </div>
                      <div className="text-text-muted ml-2">
                        {expandedId === task.id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </div>
                    </div>
                  </div>
                  
                  {/* Expanded Details */}
                  {expandedId === task.id && (
                    <div className="p-4 bg-black/20 border-t border-white/5 text-sm text-text-muted">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p><span className="text-white/50">Task ID:</span> #{task.id}</p>
                          <p><span className="text-white/50">Market:</span> {task.market}</p>
                          <p><span className="text-white/50">Keywords:</span> {task.keywords}</p>
                        </div>
                        <div>
                          <p><span className="text-white/50">Pages Requested:</span> {task.pages_requested}</p>
                          <p><span className="text-white/50">Status:</span> {task.status}</p>
                          <p><span className="text-white/50">Completed At:</span> {task.completed_at || 'Running...'}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default History;
