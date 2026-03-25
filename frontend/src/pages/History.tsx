import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSearchHistory } from '../services/api';
import { Search, RotateCw, Download, ChevronDown, ChevronUp, Clock, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';

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
      if (resp.ok) setTasks(await resp.json());
    } catch { toast.error('載入失敗'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchHistory(); }, []);

  const handleReimport = (task: ScrapeTask) => {
    toast('重新匯入功能開發中', { icon: '🔄' });
  };

  const handleDownloadCsv = (task: ScrapeTask) => {
    toast('CSV 下載功能開發中', { icon: '📥' });
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return <span className="badge badge--success"><CheckCircle size={10} style={{ marginRight: 4 }} />完成</span>;
      case 'running':   return <span className="badge badge--primary"><RotateCw size={10} style={{ marginRight: 4, animation: 'spin 1s linear infinite' }} />執行中</span>;
      case 'failed':    return <span className="badge badge--danger"><XCircle size={10} style={{ marginRight: 4 }} />失敗</span>;
      default:          return <span className="badge badge--neutral"><Clock size={10} style={{ marginRight: 4 }} />等待中</span>;
    }
  };

  return (
    <div className="page-wrapper">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              開發紀錄專區
              <span className="page-title__en">Campaign Archive</span>
            </h1>
            <span className="version-badge">LINKORA V2</span>
          </div>
          <p className="page-subtitle">查看所有探勘任務的執行記錄、結果與狀態。</p>
        </div>
        <div className="page-header__right">
          <button onClick={fetchHistory} className="btn-outline btn--sm">
            <RotateCw size={13} style={loading ? { animation: 'spin 1s linear infinite' } : {}} />
            更新列表
          </button>
        </div>
      </div>

      {/* ── Task List ── */}
      {loading && tasks.length === 0 ? (
        <div className="page-loading">
          <div className="spinner" />
          <span>載入中...</span>
        </div>
      ) : tasks.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state__icon">🔍</div>
            <p className="empty-state__title">尚無探勘記錄</p>
            <p className="empty-state__desc">前往精準開發雷達開始第一次探勘任務</p>
            <Link to="/lead-engine" className="btn-primary btn--sm" style={{ textDecoration: 'none', marginTop: 8 }}>
              前往探勘
            </Link>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {tasks.map(task => (
            <div key={task.id} className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {/* Row */}
              <div
                style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', gap: 16 }}
                onClick={() => setExpandedId(expandedId === task.id ? null : task.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, flex: 1, minWidth: 0 }}>
                  <div style={{ flexShrink: 0 }}>{getStatusBadge(task.status)}</div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
                        {task.keywords.split(',').join(', ')}
                      </span>
                      <span className="badge badge--neutral" style={{ fontSize: 10 }}>{task.miner_mode}</span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={11} />{task.started_at}</span>
                      <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>{task.leads_found} 筆資料</span>
                      <span>市場: {task.market}</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                  <button onClick={e => { e.stopPropagation(); handleReimport(task); }} className="btn-outline btn--sm">
                    <RotateCw size={12} />重新匯入
                  </button>
                  <button onClick={e => { e.stopPropagation(); handleDownloadCsv(task); }} className="btn-outline btn--sm" style={{ color: 'var(--color-success)', borderColor: 'rgba(34,197,94,0.3)' }}>
                    <Download size={12} />下載 CSV
                  </button>
                  <div style={{ color: 'var(--color-text-muted)', marginLeft: 4 }}>
                    {expandedId === task.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </div>
              </div>

              {/* Expanded */}
              {expandedId === task.id && (
                <div style={{ padding: '14px 20px', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--color-border-light)' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 12, color: 'var(--color-text-muted)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <span><span style={{ color: 'var(--color-text-secondary)' }}>Task ID:</span> #{task.id}</span>
                      <span><span style={{ color: 'var(--color-text-secondary)' }}>Market:</span> {task.market}</span>
                      <span><span style={{ color: 'var(--color-text-secondary)' }}>Keywords:</span> {task.keywords}</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <span><span style={{ color: 'var(--color-text-secondary)' }}>Pages:</span> {task.pages_requested}</span>
                      <span><span style={{ color: 'var(--color-text-secondary)' }}>Status:</span> {task.status}</span>
                      <span><span style={{ color: 'var(--color-text-secondary)' }}>Completed:</span> {task.completed_at || 'Running...'}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default History;
