import React, { useState, useEffect } from 'react';
import { getEngagements, getAdminVendors, generateAnalyticsSummary, getDeliveryStats, getTagFunnel } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { BarChart3, Users, DollarSign, Calendar, Building2, Brain, RotateCcw, Lightbulb, TrendingUp } from 'lucide-react';

interface BillingInfo {
  total_leads: number;
  unit_price: number;
  total_amount: number;
  currency: string;
  period: string;
}

const Analytics: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [vendors, setVendors] = useState<any[]>([]);
  const [selectedVendor, setSelectedVendor] = useState<number | undefined>(undefined);
  // v3.2: AI 成效摘要
  const [aiSummary, setAiSummary] = useState<any>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  
  // v3.5: 真實遙測狀態
  const [deliveryStats, setDeliveryStats] = useState<any>(null);
  const [tagFunnel, setTagFunnel] = useState<any>(null);
  
  const fetchData = async () => {
    setLoading(true);
    try {
      const resp = await getEngagements(selectedVendor);
      if (resp.ok) {
        const result = await resp.json();
        setData(result);
      }
      
      // v3.5: 真實投遞數據與行業漏斗
      const statsResp = await getDeliveryStats();
      const funnelResp = await getTagFunnel();
      if (statsResp.ok) setDeliveryStats(await statsResp.json());
      if (funnelResp.ok) setTagFunnel(await funnelResp.json());
      
      if (user?.role === 'admin' && vendors.length === 0) {
        const vResp = await getAdminVendors();
        if (vResp.ok) setVendors(await vResp.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedVendor]);

  // v3.2: AI 成效摘要
  const fetchAiSummary = async () => {
    setLoadingSummary(true);
    try {
      const resp = await generateAnalyticsSummary();
      const result = await resp.json();
      if (result.success) {
        setAiSummary(result);
      }
    } catch (e) {
      console.error("AI summary failed", e);
    } finally {
      setLoadingSummary(false);
    }
  };

  useEffect(() => {
    if (data?.billing) {
      fetchAiSummary();
    }
  }, [data]);

  if (loading && !data) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <span>Loading Analytics...</span>
      </div>
    );
  }

  const billing = data?.billing as BillingInfo;

  return (
    <div className="page-wrapper">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              成效分析雷達
              <span className="page-title__en">Performance Radar</span>
            </h1>
            <span className="version-badge">LINKORA V3.6 (AI Radar)</span>
          </div>
          <p className="page-subtitle">
            {user?.role === 'admin' ? '全系統營運數據監控' : '委外專案執行進度與結算額'}
          </p>
        </div>
        {user?.role === 'admin' && (
          <div className="page-header__right">
            <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>查看廠商:</span>
            <select
              value={selectedVendor || ''}
              onChange={e => setSelectedVendor(e.target.value ? Number(e.target.value) : undefined)}
              className="form-select" style={{ width: 'auto', minWidth: 160 }}
            >
              <option value="">全系統 (All Users)</option>
              {vendors.map(v => <option key={v.id} value={v.id}>{v.company_name}</option>)}
            </select>
          </div>
        )}
      </div>

      {/* ── 無資料時的空狀態 ── */}
      {!billing && !data?.tag_stats && (
        <div className="card">
          <div className="empty-state" style={{ padding: '60px 20px' }}>
            <div className="empty-state__icon">📊</div>
            <p className="empty-state__title">尚無分析資料</p>
            <p className="empty-state__desc">完成第一次探勘並發送開發信後，成效數據將自動顯示於此。</p>
          </div>
        </div>
      )}

      {/* v3.2/v3.6: AI 成效摘要 Report */}
      {aiSummary && (
        <div className="card mb-6" style={{
          background: 'linear-gradient(135deg, rgba(91,127,255,0.08) 0%, rgba(78,205,196,0.05) 100%)',
          borderColor: 'rgba(91,127,255,0.2)'
        }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-primary/20 rounded-lg flex items-center justify-center">
                <Brain size={16} style={{ color: 'var(--color-primary)' }} />
              </div>
              <div>
                <h3 className="text-sm font-black text-white">🤖 AI 成效摘要</h3>
                <p className="text-[10px] text-text-muted">
                  {aiSummary.period_start || ''} ~ {aiSummary.period_end || ''} 期間分析
                </p>
              </div>
            </div>
            <button
              onClick={fetchAiSummary}
              disabled={loadingSummary}
              className="btn-outline btn--sm flex items-center gap-1.5"
            >
              {loadingSummary ? <RotateCcw className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
              重新生成
            </button>
          </div>
          
          {/* Summary text */}
          <div className="bg-white/[0.03] rounded-xl p-4 mb-4">
            <p className="text-sm text-white/90 leading-relaxed">{aiSummary.summary}</p>
          </div>
          
          {/* Stats row - v3.5: Real Data Mapping */}
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[
              { label: '寄送', value: deliveryStats?.funnel?.sent || 0, color: 'var(--color-primary)' },
              { label: '開信率', value: `${deliveryStats?.funnel?.open_rate || 0}%`, color: 'var(--color-accent-teal)' },
              { label: '點擊率', value: `${deliveryStats?.funnel?.click_rate || 0}%`, color: 'var(--color-warning)' },
              { label: '回覆率', value: `${deliveryStats?.funnel?.reply_rate || 0}%`, color: 'var(--color-success)' },
            ].map(stat => (
              <div key={stat.label} className="bg-white/[0.03] rounded-xl p-3 text-center transition-transform hover:scale-105">
                <div className="text-lg font-black" style={{ color: stat.color }}>{stat.value}</div>
                <div className="text-[10px] text-text-muted mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
          
          {/* Insights */}
          {aiSummary.insights && aiSummary.insights.length > 0 && (
            <div className="space-y-2">
              <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest flex items-center gap-1.5">
                <Lightbulb size={12} /> 改善建議
              </div>
              {aiSummary.insights.map((insight: string, i: number) => (
                <div key={i} className="flex items-start gap-2 text-xs text-slate-300 bg-white/[0.02] rounded-lg px-3 py-2">
                  <span className="text-accent-teal mt-0.5 flex-shrink-0">💡</span>
                  <span>{insight}</span>
                </div>
              ))}
            </div>
          )}
          
          {/* Highlight */}
          {aiSummary.highlight && (
            <div className="mt-3 flex items-start gap-2 text-xs text-emerald-300 bg-emerald-500/10 rounded-lg px-3 py-2">
              <TrendingUp size={12} className="mt-0.5 flex-shrink-0" />
              <span>{aiSummary.highlight}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Billing Stats ── */}
      {billing && (
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 24 }}>
          <div className="stat-card">
            <div className="stat-card__icon" style={{ background: 'rgba(91,127,255,0.15)' }}>
              <Users size={20} style={{ color: 'var(--color-primary)' }} />
            </div>
            <div>
              <div className="stat-card__value">{billing.total_leads.toLocaleString()}</div>
              <div className="stat-card__label">累積探勘名單</div>
              <div className="stat-card__note">本月週期: {billing.period}</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card__icon" style={{ background: 'rgba(78,205,196,0.15)' }}>
              <DollarSign size={20} style={{ color: 'var(--color-accent-teal)' }} />
            </div>
            <div>
              <div className="stat-card__value" style={{ color: 'var(--color-accent-teal)' }}>
                ${billing.total_amount.toLocaleString()}
              </div>
              <div className="stat-card__label">
                {user?.role === 'admin' ? '預估應收 (Wholesale)' : '本月對帳應付'}
              </div>
              <div className="stat-card__note">計費單價: ${billing.unit_price} / lead</div>
            </div>
          </div>

          <div className="card" style={{ background: 'rgba(245,158,11,0.05)', borderColor: 'rgba(245,158,11,0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Calendar size={14} style={{ color: 'var(--color-warning)' }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-warning)' }}>結算提醒</span>
            </div>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.6, margin: 0 }}>
              {user?.role === 'vendor'
                ? '此金額為您委外團隊執行之批發對帳額度，請於次月 5 日前確認數據是否有誤。'
                : '管理員提示：此為目前的批發應收款項估計，最終結帳金額以實發 Lead 為準。'}
            </p>
          </div>
        </div>
      )}

      {/* ── Charts ── */}
      <div className="analytics-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* ── v3.5: Conversion Funnel ── */}
        <div className="card">
          <div className="card__header">
            <h3 className="card__title">
              <TrendingUp size={16} className="text-primary" />
              投遞轉換漏斗 (Delivery Funnel)
            </h3>
          </div>
          <div className="flex flex-col gap-4 py-4">
            {[
              { label: '探勘名單 (Sent)', count: deliveryStats?.funnel?.sent || 0, percent: 100, color: 'bg-primary' },
              { label: '成功送達 (Delivered)', count: deliveryStats?.funnel?.sent || 0, percent: 100, color: 'bg-accent-teal' },
              { label: '客戶開信 (Opened)', count: deliveryStats?.funnel?.opened || 0, percent: deliveryStats?.funnel?.open_rate || 0, color: 'bg-accent-blue' },
              { label: '點擊連結 (Clicked)', count: deliveryStats?.funnel?.clicked || 0, percent: deliveryStats?.funnel?.click_rate || 0, color: 'bg-warning' },
              { label: '回覆對話 (Replied)', count: deliveryStats?.funnel?.replied || 0, percent: deliveryStats?.funnel?.reply_rate || 0, color: 'bg-success' },
            ].map((step, i) => (
              <div key={step.label} className="relative">
                <div className="flex justify-between items-center mb-1.5 px-2">
                  <span className="text-xs font-bold text-white/80">{step.label}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black text-white">{step.count}</span>
                    <span className="text-[10px] text-text-muted">({step.percent}%)</span>
                  </div>
                </div>
                <div className="h-2.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${step.color} transition-all duration-1000 ease-out`}
                    style={{ width: `${step.percent}%`, opacity: 1 - (i * 0.15) }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 行業分佈 - v3.5: Real Industry Mapping */}
        <div className="card">
          <div className="card__header">
            <h3 className="card__title">
              <BarChart3 size={16} style={{ color: 'var(--color-primary)' }} />
              各行業界別分佈 (Industry Impact)
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto', maxHeight: 400 }}>
            {Object.entries(tagFunnel || {}).map(([tag, stats]: [string, any]) => (
              <div key={tag} className="hover:bg-white/[0.02] p-2 rounded-lg transition-colors">
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
                  <span style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>{tag}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-accent-teal font-bold">{stats.open_rate}% 開信</span>
                    <span style={{ color: 'var(--color-text-muted)' }}>{stats.sent} 筆</span>
                  </div>
                </div>
                <div style={{ height: 6, background: 'var(--color-border)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    background: 'linear-gradient(90deg, var(--color-primary), var(--color-accent-teal))',
                    width: `${Math.min(100, (stats.sent / (deliveryStats?.funnel?.sent || 1)) * 100)}%`,
                    transition: 'width 1s ease',
                    borderRadius: 3
                  }} />
                </div>
                <div style={{ display: 'flex', gap: 16, fontSize: 10, color: 'var(--color-text-muted)', marginTop: 6 }}>
                  <span>已送達: {stats.sent}</span>
                  <span style={{ color: 'var(--color-accent-teal)' }}>已開信: {stats.opened}</span>
                  <span style={{ color: 'var(--color-primary)' }}>已點擊: {stats.clicked}</span>
                </div>
              </div>
            ))}
            {Object.keys(tagFunnel || {}).length === 0 && (
              <div className="empty-state" style={{ padding: '40px 20px' }}>
                <div className="empty-state__icon">📊</div>
                <p className="empty-state__title">尚無產業數據</p>
              </div>
            )}
          </div>
        </div>

        {/* 即時動態 */}
        <div className="card">
          <div className="card__header">
            <h3 className="card__title">
              <Building2 size={16} style={{ color: 'var(--color-accent-teal)' }} />
              即時探勘動態
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto', maxHeight: 400 }}>
            {data?.records?.slice(0, 20).map((record: any) => (
              <div key={record.id} className="card" style={{ padding: '10px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    {record.company_name}
                    {record.reply_intent && (
                      <span className="badge badge--success" style={{ 
                        fontSize: '9px', 
                        padding: '2px 6px', 
                        background: record.reply_intent === 'positive' ? 'rgba(78,205,196,0.15)' : 'rgba(255,255,255,0.05)',
                        color: record.reply_intent === 'positive' ? 'var(--color-accent-teal)' : 'var(--color-text-muted)',
                        border: '1px solid rgba(255,255,255,0.1)'
                      }}>
                        🤖 {record.reply_intent.toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>{record.recipient}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className={`badge ${record.opened ? 'badge--success' : 'badge--neutral'}`}>
                    {record.opened ? '已開信' : '未讀'}
                  </span>
                  <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 4, fontFamily: 'monospace' }}>{record.sent_at}</div>
                </div>
              </div>
            ))}
            {(!data?.records || data.records.length === 0) && (
              <div className="empty-state" style={{ padding: '40px 20px' }}>
                <div className="empty-state__icon">📬</div>
                <p className="empty-state__title">尚無動態記錄</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
