import React, { useState, useEffect } from 'react';
import { getAdminStats, getAdminMembers } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { 
  BarChart3, Users, TrendingUp, Mail, Search, 
  Zap, Package, CreditCard, Activity, Calendar,
  ArrowUpRight, ArrowDownRight, RefreshCw
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface SystemStats {
  users: {
    total: number;
    active: number;
    new_this_month: number;
    by_role: { admin: number; vendor: number; member: number };
    by_plan: { free: number; pro: number; enterprise: number };
  };
  data: {
    total_leads: number;
    total_emails_sent: number;
    total_emails_opened: number;
    open_rate: number;
  };
  usage: {
    total_scrape_tasks: number;
    active_tasks: number;
    completed_tasks: number;
  };
}

const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsResp, membersResp] = await Promise.all([
        getAdminStats(),
        getAdminMembers()
      ]);
      
      if (statsResp.ok) {
        setStats(await statsResp.json());
      }
      if (membersResp.ok) {
        setMembers(await membersResp.json());
      }
    } catch (e) {
      toast.error('載入數據失敗');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [timeRange]);

  if (loading && !stats) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <span>載入系統數據...</span>
      </div>
    );
  }

  const StatCard = ({ 
    title, 
    value, 
    subtext, 
    icon: Icon, 
    trend,
    color = 'primary' 
  }: { 
    title: string; 
    value: string | number; 
    subtext?: string;
    icon: any;
    trend?: { value: number; isPositive: boolean };
    color?: 'primary' | 'success' | 'warning' | 'danger';
  }) => {
    const colorMap = {
      primary: 'var(--color-primary)',
      success: 'var(--color-success)',
      warning: 'var(--color-warning)',
      danger: 'var(--color-danger)'
    };
    
    return (
      <div className="card" style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
        <div style={{ 
          width: 48, 
          height: 48, 
          borderRadius: 12, 
          background: `${colorMap[color]}15`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colorMap[color]
        }}>
          <Icon size={24} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>{title}</div>
          <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--color-text-primary)' }}>{value}</div>
          {subtext && (
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>{subtext}</div>
          )}
          {trend && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 4, 
              marginTop: 8,
              fontSize: 12,
              color: trend.isPositive ? 'var(--color-success)' : 'var(--color-danger)'
            }}>
              {trend.isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              {trend.value}%
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="page-wrapper">
      {/* Header */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              系統監控儀表
              <span className="page-title__en">Admin Dashboard</span>
            </h1>
            <span className="version-badge">ADMIN</span>
          </div>
          <p className="page-subtitle">即時監控全系統用量、會員活躍度與營運指標。</p>
        </div>
        <div className="page-header__right" style={{ display: 'flex', gap: 12 }}>
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="form-select"
            style={{ width: 'auto' }}
          >
            <option value="7d">近 7 天</option>
            <option value="30d">近 30 天</option>
            <option value="90d">近 90 天</option>
          </select>
          <button onClick={fetchData} className="btn-outline btn--sm">
            <RefreshCw size={14} />
            重新整理
          </button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <StatCard 
          title="總會員數" 
          value={stats?.users.total || 0} 
          subtext={`+${stats?.users.new_this_month || 0} 本月新增`}
          icon={Users}
          trend={{ value: 12, isPositive: true }}
        />
        <StatCard 
          title="總 Leads 數" 
          value={stats?.data.total_leads?.toLocaleString() || 0}
          subtext="全系統累積"
          icon={Search}
          color="success"
        />
        <StatCard 
          title="郵件發送" 
          value={stats?.data.total_emails_sent?.toLocaleString() || 0}
          subtext={`開信率 ${stats?.data.open_rate || 0}%`}
          icon={Mail}
          color="warning"
        />
        <StatCard 
          title="探勘任務" 
          value={stats?.usage.total_scrape_tasks || 0}
          subtext={`${stats?.usage.active_tasks || 0} 進行中`}
          icon={Zap}
          color="danger"
        />
      </div>

      {/* Role Distribution */}
      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <h3 className="card__title" style={{ marginBottom: 20 }}>
            <Users size={16} />
            角色分佈
          </h3>
          <div style={{ display: 'flex', gap: 16 }}>
            {[
              { label: 'Admin', count: stats?.users.by_role.admin || 0, color: '#ef4444' },
              { label: 'Vendor', count: stats?.users.by_role.vendor || 0, color: '#f59e0b' },
              { label: 'Member', count: stats?.users.by_role.member || 0, color: '#3b82f6' },
            ].map((item) => (
              <div key={item.label} style={{ flex: 1, textAlign: 'center' }}>
                <div style={{ 
                  fontSize: 32, 
                  fontWeight: 900, 
                  color: item.color,
                  marginBottom: 4 
                }}>
                  {item.count}
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="card__title" style={{ marginBottom: 20 }}>
            <Package size={16} />
            方案分佈
          </h3>
          <div style={{ display: 'flex', gap: 16 }}>
            {[
              { label: '免費版', count: stats?.users.by_plan.free || 0, color: '#6b7280' },
              { label: '專業版', count: stats?.users.by_plan.pro || 0, color: '#10b981' },
              { label: '企業版', count: stats?.users.by_plan.enterprise || 0, color: '#8b5cf6' },
            ].map((item) => (
              <div key={item.label} style={{ flex: 1, textAlign: 'center' }}>
                <div style={{ 
                  fontSize: 32, 
                  fontWeight: 900, 
                  color: item.color,
                  marginBottom: 4 
                }}>
                  {item.count}
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="card__title" style={{ marginBottom: 16 }}>
          <Activity size={16} />
          最近活躍會員
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {members.slice(0, 5).map((member: any) => (
            <div 
              key={member.id} 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                padding: '12px 16px',
                background: 'var(--color-bg-card)',
                borderRadius: 8,
                border: '1px solid var(--color-border)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ 
                  width: 36, 
                  height: 36, 
                  borderRadius: '50%', 
                  background: 'var(--color-primary-glow)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  color: 'var(--color-primary)'
                }}>
                  {(member.name || member.email)[0].toUpperCase()}
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{member.name || member.email}</div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                    {member.subscription?.plan.display_name || '無訂閱'} · {member.role}
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ 
                  fontSize: 12, 
                  color: member.is_active ? 'var(--color-success)' : 'var(--color-danger)'
                }}>
                  {member.is_active ? '啟用中' : '已停用'}
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                  {new Date(member.created_at).toLocaleDateString('zh-TW')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
