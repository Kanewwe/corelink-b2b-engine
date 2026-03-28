import React, { useState, useEffect } from 'react';
import { Activity, Shield, Clock, AlertTriangle, CheckCircle, BarChart2, Zap, RefreshCw, Server, ArrowLeft } from 'lucide-react';
import { getScraperHealthStats } from '../services/api';
import { useNavigate } from 'react-router-dom';

const ScraperHealth: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // 每一分鐘更新一次
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await getScraperHealthStats();
      const data = await res.json();
      if (data.success) {
        setStats(data);
      } else {
        setError(data.message || '無法讀取監控數據');
      }
    } catch (err) {
      setError('網絡連線錯誤');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Healthy': return 'var(--color-success)';
      case 'Degraded': return 'var(--color-warning)';
      case 'Critical': return 'var(--color-danger)';
      default: return 'var(--color-text-muted)';
    }
  };

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div className="page-header__left">
          <button onClick={() => navigate(-1)} className="btn-icon mb-2">
            <ArrowLeft size={18} />
          </button>
          <div className="flex items-center gap-3">
            <h1 className="page-title">
              探勘引擎健康度
              <span className="page-title__en">Scraper Health Radar</span>
            </h1>
            {stats?.summary?.status && (
              <span className="badge" style={{ 
                background: `${getStatusColor(stats.summary.status)}20`, 
                color: getStatusColor(stats.summary.status),
                borderColor: `${getStatusColor(stats.summary.status)}40`
              }}>
                ●系統狀態: {stats.summary.status}
              </span>
            )}
          </div>
          <p className="page-subtitle">實時監控探勘成功率、響應延遲與節點穩定性 (v3.7 Telemetry)</p>
        </div>
        <div className="page-header__right">
          <button onClick={fetchStats} className="btn-outline flex items-center gap-2">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            立即重新整理
          </button>
        </div>
      </div>

      {error && (
        <div className="card mb-6" style={{ borderColor: 'var(--color-danger)' }}>
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle size={20} />
            <p className="font-bold">{error}</p>
          </div>
        </div>
      )}

      {/* ── 核心指標 ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="stat-card">
          <div className="stat-card__icon" style={{ background: 'rgba(78,205,196,0.15)' }}>
            <Activity size={20} style={{ color: 'var(--color-accent-teal)' }} />
          </div>
          <div>
            <div className="stat-card__value" style={{ color: 'var(--color-accent-teal)' }}>
              {stats?.summary?.success_rate}%
            </div>
            <div className="stat-card__label">平均成功率 (Success Rate)</div>
            <div className="stat-card__note">定義為 HTTP 2xx 響應</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card__icon" style={{ background: 'rgba(91,127,255,0.15)' }}>
            <Server size={20} style={{ color: 'var(--color-primary)' }} />
          </div>
          <div>
            <div className="stat-card__value">{stats?.summary?.total_requests?.toLocaleString()}</div>
            <div className="stat-card__label">累積探勘請求 (Total Logs)</div>
            <div className="stat-card__note">最近 7 天樣本數</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card__icon" style={{ background: 'rgba(245,158,11,0.15)' }}>
            <Clock size={20} style={{ color: 'var(--color-warning)' }} />
          </div>
          <div>
            <div className="stat-card__value" style={{ color: 'var(--color-warning)' }}>
              {stats?.miner_metrics?.[0]?.latency || 0}s
            </div>
            <div className="stat-card__label">平均響應延遲 (Latency)</div>
            <div className="stat-card__note">系統整體平均</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Miner 效能對比 */}
        <div className="card">
          <div className="card__header">
            <h3 className="card__title">
              <Zap size={16} className="text-primary" />
              探勘模組效能分析 (Miner Performance)
            </h3>
          </div>
          <div className="space-y-6">
            {stats?.miner_metrics?.map((m: any) => (
              <div key={m.mode} className="bg-white/[0.02] p-4 rounded-xl border border-white/[0.05]">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-bold text-white uppercase tracking-wider">{m.mode}</span>
                  <span className="text-xs text-text-muted">{m.count} 次請求</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex-1 h-3 bg-white/10 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-primary to-accent-teal"
                      style={{ width: `${Math.min(100, (1 / (m.latency || 0.1)) * 50)}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono text-accent-teal">{m.latency}s</span>
                </div>
                <div className="mt-2 text-[10px] text-text-muted flex items-center gap-1">
                  <Shield size={10} /> 響應速度得分: {m.latency < 2 ? 'Excellent' : m.latency < 5 ? 'Good' : 'Needs Optimization'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* HTTP 狀態碼分佈 */}
        <div className="card">
          <div className="card__header">
            <h3 className="card__title">
              <BarChart2 size={16} className="text-accent-teal" />
              HTTP 狀態碼統計 (Status Distribution)
            </h3>
          </div>
          <div className="flex flex-col gap-3">
            {stats?.status_distribution?.sort((a: any, b: any) => a.status - b.status).map((s: any) => (
              <div key={s.status} className="flex items-center gap-4">
                <div className="w-12 text-sm font-mono font-bold" style={{ color: s.status < 300 ? 'var(--color-success)' : 'var(--color-danger)' }}>
                  {s.status}
                </div>
                <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className="h-full" 
                    style={{ 
                      width: `${(s.count / stats.summary.total_requests) * 100}%`,
                      background: s.status < 300 ? 'var(--color-success)' : 'var(--color-danger)',
                      opacity: 0.7
                    }} 
                  />
                </div>
                <div className="w-16 text-right text-xs text-text-muted">{s.count}</div>
              </div>
            ))}
            <div className="mt-8 p-4 bg-primary/5 rounded-2xl border border-primary/10">
              <div className="flex items-start gap-3">
                <CheckCircle size={16} className="text-primary mt-1" />
                <div>
                  <h4 className="text-sm font-bold text-white mb-1">健康診斷報告</h4>
                  <p className="text-xs text-text-muted leading-relaxed">
                    目前的 API 成功率為 <span className="text-white font-bold">{stats?.summary?.success_rate}%</span>。
                    {stats?.summary?.success_rate > 95 
                      ? '系統運作極其穩定，暫無已知的代理或封鎖問題。' 
                      : '部分請求出現 4xx/5xx，建議檢查代理 IP 池的健康度或目標站點的的反爬機制更新。'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScraperHealth;
