import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Send, Search, RefreshCw, AlertTriangle, Clock, TrendingUp } from 'lucide-react';
import { getOptimalSendTime } from '../services/api';
import { toast } from 'react-hot-toast';

const STATUS_OPTIONS = ['已寄出', '已送達', '已開信', '已點擊', '已回覆', '退信', '失敗'];

const STATUS_BADGE: Record<string, string> = {
  '已寄出': 'badge--primary',
  '已送達': 'badge--neutral',
  '已開信': 'badge--success',
  '已點擊': 'badge--success',
  '已回覆': 'badge--success',
  '退信':   'badge--warning',
  '失敗':   'badge--danger',
};

const Campaigns: React.FC = () => {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [searchText, setSearchText] = useState('');
  const [hasSmtp] = useState(false);
  // v3.2: 最佳寄信時間
  const [optimalTime, setOptimalTime] = useState<any>(null);
  const [loadingOptimal, setLoadingOptimal] = useState(false);

  useEffect(() => {
    if (campaigns.length < 0) setCampaigns([]);
  }, []);

  // v3.2: 載入最佳寄信時間
  useEffect(() => {
    const fetchOptimal = async () => {
      setLoadingOptimal(true);
      try {
        const resp = await getOptimalSendTime();
        const data = await resp.json();
        if (data.success) setOptimalTime(data);
      } catch (e) { /* silent */ }
      finally { setLoadingOptimal(false); }
    };
    fetchOptimal();
  }, []);

  const handleApplyOptimalTime = () => {
    if (!optimalTime?.best_day || !optimalTime?.best_hour) return;
    const now = new Date();
    const days: Record<string, number> = { Sunday: 0, Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4, Friday: 5, Saturday: 6 };
    const targetDay = days[optimalTime.best_day] ?? 2;
    now.setDate(now.getDate() + ((targetDay - now.getDay() + 7) % 7 || 7));
    now.setHours(optimalTime.best_hour, 0, 0, 0);
    toast.success(`已設定寄信時間為 ${optimalTime.best_time_display || optimalTime.best_day + ' ' + optimalTime.best_hour + ':00'}`);
  };

  const filtered = campaigns.filter(c => {
    if (statusFilter && c.status !== statusFilter) return false;
    if (searchText && !c.subject?.includes(searchText) && !c.company?.includes(searchText)) return false;
    return true;
  });

  return (
    <div className="page-wrapper">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              自動化投遞
              <span className="page-title__en">Automated Outreach</span>
            </h1>
            <span className="version-badge">LINKORA V3.2 (AI Outreach)</span>
          </div>
          <p className="page-subtitle">追蹤所有開發信的寄送狀態、開信率與互動記錄。</p>
        </div>
        <div className="page-header__right">
          <button className="btn-outline btn--sm">
            <RefreshCw size={13} />重新整理
          </button>
        </div>
      </div>

      {/* v3.2: AI 最佳寄信時間推薦 */}
      {optimalTime && (
        <div className="card mb-4" style={{
          background: 'linear-gradient(135deg, rgba(78,205,196,0.08) 0%, rgba(91,127,255,0.05) 100%)',
          borderColor: 'rgba(78,205,196,0.2)'
        }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-accent-teal/20 rounded-xl flex items-center justify-center">
                <Clock size={18} style={{ color: 'var(--color-accent-teal)' }} />
              </div>
              <div>
                <div className="text-sm font-black text-white">🤖 AI 最佳寄信時間</div>
                <div className="text-xs text-text-muted mt-0.5">
                  {optimalTime.reason || `根據您的歷史數據分析`}
                  {optimalTime.total_opened > 0 && <span className="ml-2 text-accent-teal">（已分析 {optimalTime.total_opened} 封開信）</span>}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {optimalTime.best_day && optimalTime.best_hour !== undefined && (
                <>
                  <div className="text-center">
                    <div className="text-lg font-black text-accent-teal">{optimalTime.best_time_display || `${optimalTime.best_day} ${String(optimalTime.best_hour).padStart(2,'0')}:00`}</div>
                    <div className="text-[10px] text-text-muted">
                      信心度：
                      <span className={optimalTime.confidence === 'high' ? 'text-emerald-400' : optimalTime.confidence === 'medium' ? 'text-yellow-400' : 'text-slate-400'}>
                        {optimalTime.confidence === 'high' ? '高' : optimalTime.confidence === 'medium' ? '中' : '低（數據不足）'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={handleApplyOptimalTime}
                    className="btn-outline btn--sm flex items-center gap-1.5"
                    style={{ borderColor: 'var(--color-accent-teal)', color: 'var(--color-accent-teal)' }}
                  >
                    <TrendingUp size={13} /> 套用建議
                  </button>
                </>
              )}
              {optimalTime.confidence === 'low' && (
                <span className="text-xs text-text-muted">{optimalTime.recommendation || '請持續累積開信數據'}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── SMTP 警告橫幅（未設定時顯示）── */}
      {!hasSmtp && (
        <div className="page-banner page-banner--warning">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
            <AlertTriangle size={18} style={{ flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 600, marginBottom: 2 }}>SMTP 尚未設定，目前無法寄信</div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>完成設定後才能發送開發信</div>
            </div>
          </div>
          <Link to="/smtp" className="btn-primary btn--sm" style={{ textDecoration: 'none', flexShrink: 0 }}>
            前往設定 →
          </Link>
        </div>
      )}

      {/* ── 篩選列 ── */}
      <div className="filter-bar">
        <div className="form-input-wrapper" style={{ flex: 1, minWidth: 200 }}>
          <Search size={14} className="input-icon" />
          <input
            className="form-input"
            placeholder="搜尋主旨 / 公司..."
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
          />
        </div>

        <select className="form-select" style={{ width: 'auto', minWidth: 120 }}
          value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">所有狀態</option>
          {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <input type="date" className="form-input" style={{ width: 'auto' }}
          value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
        <span style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>至</span>
        <input type="date" className="form-input" style={{ width: 'auto' }}
          value={dateTo} onChange={e => setDateTo(e.target.value)} />
      </div>

      {/* ── Table ── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', flex: 1 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 40 }}><input type="checkbox" style={{ accentColor: 'var(--color-primary)' }} /></th>
              <th>時間</th>
              <th>目標公司</th>
              <th>Email</th>
              <th>主旨</th>
              <th>狀態</th>
              <th style={{ width: 100 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={7}>
                <div className="empty-state">
                  <div className="empty-state__icon"><Send size={40} style={{ opacity: 0.3 }} /></div>
                  <p className="empty-state__title">尚無寄信記錄</p>
                  <p className="empty-state__desc">
                    {hasSmtp
                      ? '完成 Lead 探勘並選擇模板後，即可開始發送開發信'
                      : '請先完成 SMTP 設定，才能開始發送開發信'}
                  </p>
                  {!hasSmtp && (
                    <Link to="/smtp" className="btn-primary btn--sm" style={{ textDecoration: 'none', marginTop: 8 }}>
                      前往 SMTP 設定
                    </Link>
                  )}
                </div>
              </td></tr>
            ) : filtered.map((c, i) => (
              <tr key={i}>
                <td data-label="選取"><input type="checkbox" style={{ accentColor: 'var(--color-primary)' }} /></td>
                <td data-label="時間" style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{c.sent_at}</td>
                <td data-label="目標公司" style={{ fontWeight: 600 }}>{c.company}</td>
                <td data-label="Email" style={{ fontFamily: 'monospace', fontSize: 12 }}>{c.email}</td>
                <td data-label="主旨" style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.subject}</td>
                <td data-label="狀態"><span className={`badge ${STATUS_BADGE[c.status] || 'badge--neutral'}`}>{c.status}</span></td>
                <td>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn-icon-sm" title="查看">👁</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Campaigns;
