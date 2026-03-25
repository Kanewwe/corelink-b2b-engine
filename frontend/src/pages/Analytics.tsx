import React, { useState, useEffect } from 'react';
import { getEngagements, getAdminVendors } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { 
  BarChart3, TrendingUp, Users, DollarSign, 
  ArrowUpRight, Calendar, Receipt,
  Building2, RefreshCw
} from 'lucide-react';

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

  const fetchData = async () => {
    setLoading(true);
    try {
      const resp = await getEngagements(selectedVendor);
      if (resp.ok) {
        const result = await resp.json();
        setData(result);
      }
      
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

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full text-text-muted">
        <RefreshCw className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  const billing = data?.billing as BillingInfo;

  return (
    <div className="flex flex-col h-full gap-6 max-w-7xl mx-auto w-full">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-primary" />
            成效與帳務分析
          </h2>
          <p className="text-text-muted text-sm mt-1">
            {user?.role === 'admin' ? '全系統營運數據監控' : '委外專案執行進度與結算額'}
          </p>
        </div>
        
        {user?.role === 'admin' && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-text-muted">查看特定廠商:</span>
            <select 
              value={selectedVendor || ''} 
              onChange={(e) => setSelectedVendor(e.target.value ? Number(e.target.value) : undefined)}
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-primary"
            >
              <option value="">全系統 (All Users)</option>
              {vendors.map(v => (
                <option key={v.id} value={v.id}>{v.company_name}</option>
              ))}
            </select>
          </div>
        )}
      </header>

      {/* Top Stats - Billing Focused for Vendors/Admins */}
      {billing && (
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-panel p-6 border-l-4 border-l-primary relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Users className="w-16 h-16" />
            </div>
            <div className="text-sm text-text-muted mb-1 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              累積探勘名單 (Leads)
            </div>
            <div className="text-3xl font-bold text-white tracking-tight">
              {billing.total_leads.toLocaleString()}
              <span className="text-sm font-normal text-text-muted ml-2">筆</span>
            </div>
            <div className="text-xs text-green-400 mt-2 flex items-center gap-1">
              <ArrowUpRight className="w-3 h-3" />
              本月週期: {billing.period}
            </div>
          </div>

          <div className="glass-panel p-6 border-l-4 border-l-accent relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <DollarSign className="w-16 h-16" />
            </div>
            <div className="text-sm text-text-muted mb-1 flex items-center gap-2">
              <Receipt className="w-4 h-4" />
              {user?.role === 'admin' ? '預估應收 (Wholesale)' : '本月對帳應付'}
            </div>
            <div className="text-3xl font-bold text-accent tracking-tight">
              ${billing.total_amount.toLocaleString()}
              <span className="text-sm font-normal text-text-muted ml-2">{billing.currency}</span>
            </div>
            <div className="text-xs text-text-muted mt-2">
              計費單價: ${billing.unit_price} / lead
            </div>
          </div>

          <div className="glass-panel p-6 border-l-4 border-l-warning relative overflow-hidden group flex flex-col justify-center bg-warning/5">
             <div className="text-sm font-bold text-warning flex items-center gap-2 mb-2">
               <Calendar className="w-4 h-4" />
               結算提醒
             </div>
             <p className="text-xs text-text-muted leading-relaxed">
               {user?.role === 'vendor' 
                ? "此金額為您委外團隊執行之批發對帳額度，請於次月 5 日前確認數據是否有誤。" 
                : "管理員提示：此為目前的批發應收款項估計，最終結帳金額以實發 Lead 為準。"}
             </p>
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        {/* Left: Tag Distribution */}
        <section className="glass-panel p-6 flex flex-col overflow-hidden">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            各行業界別分佈
          </h3>
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {Object.entries(data?.tag_stats || {}).map(([tag, stats]: [string, any]) => (
              <div key={tag} className="space-y-2">
                <div className="flex justify-between text-sm items-end">
                  <span className="text-white font-medium">{tag}</span>
                  <span className="text-text-muted">{stats.total} 筆</span>
                </div>
                <div className="h-3 bg-white/5 rounded-full overflow-hidden border border-white/5">
                  <div 
                    className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-1000"
                    style={{ width: `${Math.min(100, (stats.total / (data.total_leads || 1)) * 100)}%` }}
                  ></div>
                </div>
                <div className="flex gap-4 text-[10px] text-text-muted uppercase tracking-tighter">
                  <span>Delivered: {stats.delivered}</span>
                  <span className="text-accent">Opened: {stats.opened}</span>
                  <span className="text-primary-light">Clicked: {stats.clicked}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Right: Recent Activity Log */}
        <section className="glass-panel p-6 flex flex-col overflow-hidden">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-accent" />
            即時探勘動態
          </h3>
          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {data?.records?.slice(0, 20).map((record: any) => (
              <div key={record.id} className="p-3 bg-white/5 border border-white/5 rounded-lg flex justify-between items-center group hover:bg-white/10 transition-colors">
                <div>
                  <div className="text-sm font-medium text-white">{record.company_name}</div>
                  <div className="text-xs text-text-muted mt-0.5">{record.recipient}</div>
                </div>
                <div className="text-right">
                  <div className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold ${
                    record.opened ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/40'
                  }`}>
                    {record.opened ? '已開信' : '未讀'}
                  </div>
                  <div className="text-[10px] text-text-muted mt-1 font-mono">{record.sent_at}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default Analytics;
