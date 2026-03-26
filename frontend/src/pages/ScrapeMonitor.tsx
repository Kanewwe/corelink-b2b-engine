import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  getAdminScrapeTasks, getAdminScrapeTaskDetail, retryAdminScrapeTask, 
  cleanupStaleTasks, getAdminScrapeTaskLogs 
} from '../services/api';
import { 
  RefreshCw, Play, Trash2, ChevronDown, ChevronRight, 
  CheckCircle, XCircle, Clock, AlertTriangle, Bug, Loader2
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface ScrapeTask {
  id: number;
  user_id: number;
  market: string;
  keywords: string;
  miner_mode: string;
  pages_requested: number;
  status: string;
  leads_found: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

interface ScrapeLog {
  id: number;
  task_id: number;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  keyword?: string;
  page?: number;
  items_found?: number;
  created_at: string;
}

const LEVEL_CONFIG = {
  info:     { icon: <Clock size={12} />,     color: '#8b8fa8', label: '資訊' },
  warning:  { icon: <AlertTriangle size={12} />, color: '#f59e0b', label: '警告' },
  error:    { icon: <XCircle size={12} />,    color: '#ef4444', label: '錯誤' },
  success:  { icon: <CheckCircle size={12} />, color: '#22c55e', label: '成功' },
};

const STATUS_CONFIG: Record<string, { color: string; bg: string; icon: any }> = {
  Running:   { color: '#3b82f6', bg: 'rgba(59,130,246,0.1)',  icon: <Loader2 size={14} className="animate-spin" /> },
  Completed: { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',   icon: <CheckCircle size={14} /> },
  Failed:    { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',   icon: <XCircle size={14} /> },
};

const ScrapeMonitor: React.FC = () => {
  const [tasks, setTasks] = useState<ScrapeTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('');
  const [expandedTask, setExpandedTask] = useState<number | null>(null);
  const [taskLogs, setTaskLogs] = useState<Record<number, ScrapeLog[]>>({});
  const [taskDetails, setTaskDetails] = useState<Record<number, ScrapeTask>>({});
  const [loadingLogs, setLoadingLogs] = useState<Record<number, boolean>>({});
  const [cleaning, setCleaning] = useState(false);
  const autoRefreshRef = useRef<NodeJS.Timeout | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const resp = await getAdminScrapeTasks(filter || undefined);
      if (resp.ok) {
        setTasks(await resp.json());
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchTasks();
    
    // Auto-refresh every 5 seconds for Running tasks
    autoRefreshRef.current = setInterval(() => {
      if (tasks.some(t => t.status === 'Running')) {
        fetchTasks();
      }
    }, 5000);
    
    return () => {
      if (autoRefreshRef.current) clearInterval(autoRefreshRef.current);
    };
  }, [fetchTasks]);

  const toggleExpand = async (taskId: number) => {
    if (expandedTask === taskId) {
      setExpandedTask(null);
      return;
    }
    setExpandedTask(taskId);
    
    if (!taskLogs[taskId]) {
      setLoadingLogs(prev => ({ ...prev, [taskId]: true }));
      try {
        const [logsResp, detailResp] = await Promise.all([
          getAdminScrapeTaskLogs(taskId),
          getAdminScrapeTaskDetail(taskId),
        ]);
        
        if (logsResp.ok) setTaskLogs(prev => ({ ...prev, [taskId]: await logsResp.json() }));
        if (detailResp.ok) setTaskDetails(prev => ({ ...prev, [taskId]: await detailResp.json() }));
      } catch {
        toast.error('載入日誌失敗');
      } finally {
        setLoadingLogs(prev => ({ ...prev, [taskId]: false }));
      }
    }
  };

  const handleRetry = async (taskId: number) => {
    if (!confirm('確定要重試這個任務嗎？')) return;
    try {
      const resp = await retryAdminScrapeTask(taskId);
      if (resp.ok) {
        toast.success('已重新排程任務');
        fetchTasks();
      } else {
        const err = await resp.json();
        toast.error(err.detail || '重試失敗');
      }
    } catch {
      toast.error('網路錯誤');
    }
  };

  const handleCleanup = async () => {
    if (!confirm('清理所有卡住超過 10 分鐘的任務？')) return;
    setCleaning(true);
    try {
      const resp = await cleanupStaleTasks();
      if (resp.ok) {
        const data = await resp.json();
        toast.success(data.message);
        fetchTasks();
      }
    } catch {
      toast.error('清理失敗');
    } finally {
      setCleaning(false);
    }
  };

  const formatTime = (str: string) => {
    if (!str) return '-';
    const d = new Date(str);
    return d.toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const duration = (start: string, end?: string) => {
    if (!start) return '-';
    const s = new Date(start).getTime();
    const e = end ? new Date(end).getTime() : Date.now();
    const ms = Math.round((e - s) / 1000);
    if (ms < 60) return `${ms}s`;
    if (ms < 3600) return `${Math.floor(ms / 60)}m ${ms % 60}s`;
    return `${Math.floor(ms / 3600)}h ${Math.floor((ms % 3600) / 60)}m`;
  };

  const filteredTasks = tasks;

  return (
    <div className="page-wrapper">
      {/* Header */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              爬蟲監控
              <span className="page-title__en">Scrape Monitor</span>
            </h1>
            <span className="version-badge">ADMIN</span>
          </div>
          <p className="page-subtitle">即時監控爬蟲任務執行狀態與詳細日誌，快速排除問題。</p>
        </div>
        <div className="page-header__right">
          {/* Filter */}
          <select 
            value={filter} 
            onChange={e => setFilter(e.target.value)}
            className="form-select"
          >
            <option value="">全部狀態</option>
            <option value="Running">執行中</option>
            <option value="Completed">已完成</option>
            <option value="Failed">失敗</option>
          </select>
          
          <button onClick={fetchTasks} className="btn-outline btn--sm" disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            重新整理
          </button>
          
          <button onClick={handleCleanup} className="btn-outline btn--sm" disabled={cleaning}>
            <Trash2 size={14} />
            {cleaning ? '清理中...' : '清理卡住任務'}
          </button>
        </div>
      </div>

      {/* Running Tasks Alert */}
      {tasks.filter(t => t.status === 'Running').length > 0 && (
        <div className="page-banner page-banner--info" style={{ marginBottom: 16 }}>
          <Bug size={16} />
          <div>
            <div style={{ fontWeight: 600 }}>目前有 {tasks.filter(t => t.status === 'Running').length} 個任務執行中</div>
            <div style={{ fontSize: 12, opacity: 0.8 }}>頁面每 5 秒自動更新，點擊任務可查看即時日誌</div>
          </div>
        </div>
      )}

      {/* Task List */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div className="page-loading">
            <div className="spinner" />
            <span>載入中...</span>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__icon">🕷️</div>
            <p className="empty-state__title">尚無爬蟲任務記錄</p>
            <p className="empty-state__desc">當會員啟動探勘任務時會顯示在這裡</p>
          </div>
        ) : (
          <div>
            {filteredTasks.map(task => {
              const isExpanded = expandedTask === task.id;
              const statusCfg = STATUS_CONFIG[task.status] || STATUS_CONFIG.Running;
              const logs = taskLogs[task.id] || [];
              const detail = taskDetails[task.id];
              
              return (
                <div key={task.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  {/* Task Row */}
                  <div 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: 16, 
                      padding: '14px 20px',
                      cursor: 'pointer',
                      background: isExpanded ? 'rgba(91,127,255,0.05)' : 'transparent',
                      transition: 'background 0.2s',
                    }}
                    onClick={() => toggleExpand(task.id)}
                  >
                    {/* Expand Icon */}
                    {isExpanded 
                      ? <ChevronDown size={16} className="text-text-muted" />
                      : <ChevronRight size={16} className="text-text-muted" />
                    }
                    
                    {/* Status Badge */}
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: 6,
                      padding: '4px 10px',
                      borderRadius: 20,
                      background: statusCfg.bg,
                      color: statusCfg.color,
                      fontSize: 12,
                      fontWeight: 700,
                      minWidth: 90,
                      justifyContent: 'center',
                    }}>
                      {statusCfg.icon}
                      {task.status}
                    </div>

                    {/* Task Info */}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>
                        #{task.id} — {task.keywords}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                        {task.miner_mode} · {task.market} · {task.pages_requested} 頁
                      </div>
                    </div>

                    {/* Stats */}
                    <div style={{ textAlign: 'right', minWidth: 80 }}>
                      <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--color-primary)' }}>
                        {task.leads_found}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>leads</div>
                    </div>

                    {/* Duration */}
                    <div style={{ textAlign: 'right', minWidth: 80 }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>
                        {duration(task.started_at, task.completed_at)}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>耗時</div>
                    </div>

                    {/* Time */}
                    <div style={{ textAlign: 'right', minWidth: 130, fontSize: 11, color: 'var(--color-text-muted)' }}>
                      {formatTime(task.started_at)}
                    </div>

                    {/* Actions */}
                    {(task.status === 'Failed' || task.status === 'Completed') && (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleRetry(task.id); }}
                        className="btn-outline btn--sm"
                        style={{ flexShrink: 0 }}
                      >
                        <Play size={12} />
                        重試
                      </button>
                    )}
                  </div>

                  {/* Expanded Detail */}
                  {isExpanded && (
                    <div style={{ padding: '0 20px 16px 56px' }}>
                      {/* Error Message */}
                      {task.error_message && (
                        <div style={{ 
                          padding: '10px 14px',
                          background: 'rgba(239,68,68,0.1)',
                          border: '1px solid rgba(239,68,68,0.3)',
                          borderRadius: 8,
                          marginBottom: 12,
                          fontSize: 12,
                          color: '#ef4444',
                        }}>
                          <div style={{ fontWeight: 600, marginBottom: 4 }}>錯誤訊息</div>
                          <code style={{ fontSize: 11 }}>{task.error_message}</code>
                        </div>
                      )}

                      {/* Logs */}
                      {loadingLogs[task.id] ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-muted)', fontSize: 12 }}>
                          <Loader2 size={14} className="animate-spin" />
                          載入日誌中...
                        </div>
                      ) : logs.length === 0 ? (
                        <div style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>尚無日誌記錄</div>
                      ) : (
                        <div style={{ 
                          background: '#0d0f1e',
                          borderRadius: 8,
                          border: '1px solid var(--color-border)',
                          maxHeight: 400,
                          overflowY: 'auto',
                          fontFamily: 'monospace',
                          fontSize: 11,
                        }}>
                          {logs.map((log, idx) => {
                            const cfg = LEVEL_CONFIG[log.level] || LEVEL_CONFIG.info;
                            return (
                              <div key={log.id} style={{ 
                                display: 'flex', 
                                gap: 12, 
                                padding: '6px 12px',
                                borderBottom: idx < logs.length - 1 ? '1px solid rgba(255,255,255,0.03)' : 'none',
                                alignItems: 'flex-start',
                              }}>
                                <span style={{ color: '#4a4f6a', whiteSpace: 'nowrap', minWidth: 60 }}>
                                  {log.created_at}
                                </span>
                                <span style={{ color: cfg.color, minWidth: 50, display: 'flex', alignItems: 'center', gap: 4 }}>
                                  {cfg.icon} {cfg.label}
                                </span>
                                <span style={{ color: 'var(--color-text-secondary)' }}>{log.message}</span>
                                {log.items_found !== null && log.items_found !== undefined && (
                                  <span style={{ marginLeft: 'auto', color: 'var(--color-primary)', fontWeight: 600 }}>
                                    {log.items_found} 筆
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ScrapeMonitor;
