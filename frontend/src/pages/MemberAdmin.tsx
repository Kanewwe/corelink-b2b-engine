import React, { useState, useEffect, useCallback } from 'react';
import {
  Users, Search, UserCheck, UserX, RefreshCw,
  ChevronDown, MoreVertical, Eye, Trash2, KeyRound,
  CheckCircle, XCircle, Crown, User, Building2, Mail,
  TrendingUp, BarChart2, AlertTriangle, X
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import {
  getAdminMembers, getAdminMemberDetail,
  updateAdminMember, deleteAdminMember,
  resetMemberPassword, getAdminStats
} from '../services/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Member {
  id: number;
  email: string;
  name: string | null;
  company_name: string | null;
  role: 'admin' | 'vendor' | 'member';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  subscription: {
    plan: { display_name: string; name: string };
    status: string;
  } | null;
  usage: {
    customers: { used: number; limit: number };
    emails_month: { used: number; limit: number };
    autominer_runs: { used: number; limit: number };
  } | null;
}

interface MemberDetail extends Member {
  last_login_at: string | null;
  stats: {
    leads_count: number;
    emails_sent: number;
    emails_opened: number;
    open_rate: number;
  };
}

interface AdminStats {
  users: {
    total: number;
    active: number;
    new_this_month: number;
    by_role: { admin: number; vendor: number; member: number };
  };
  data: { total_leads: number; total_emails: number };
}

// ─── Role Badge ───────────────────────────────────────────────────────────────

const RoleBadge: React.FC<{ role: string }> = ({ role }) => {
  const map: Record<string, { label: string; cls: string; icon: React.ReactNode }> = {
    admin:  { label: 'Admin',  cls: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',  icon: <Crown size={11} /> },
    vendor: { label: 'Vendor', cls: 'bg-purple-500/15 text-purple-400 border-purple-500/30', icon: <Building2 size={11} /> },
    member: { label: 'Member', cls: 'bg-blue-500/15 text-blue-400 border-blue-500/30',       icon: <User size={11} /> },
  };
  const { label, cls, icon } = map[role] ?? map.member;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${cls}`}>
      {icon}{label}
    </span>
  );
};

// ─── Status Badge ─────────────────────────────────────────────────────────────

const StatusBadge: React.FC<{ active: boolean }> = ({ active }) =>
  active
    ? <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-500/15 text-green-400 border border-green-500/30"><CheckCircle size={10} />啟用</span>
    : <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-500/15 text-red-400 border border-red-500/30"><XCircle size={10} />停用</span>;

// ─── Usage Bar ────────────────────────────────────────────────────────────────

const UsageBar: React.FC<{ used: number; limit: number; label: string }> = ({ used, limit, label }) => {
  const pct = limit <= 0 ? 0 : Math.min(100, Math.round(used / limit * 100));
  const color = pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-primary';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] text-text-muted">
        <span>{label}</span>
        <span>{limit < 0 ? `${used} / ∞` : `${used} / ${limit}`}</span>
      </div>
      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

// ─── Detail Modal ─────────────────────────────────────────────────────────────

const DetailModal: React.FC<{ memberId: number; onClose: () => void; onUpdated: () => void }> = ({ memberId, onClose, onUpdated }) => {
  const [detail, setDetail] = useState<MemberDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editRole, setEditRole] = useState('');
  const [showTempPwd, setShowTempPwd] = useState('');

  useEffect(() => {
    getAdminMemberDetail(memberId)
      .then(r => r.json())
      .then(d => { setDetail(d); setEditRole(d.role); })
      .finally(() => setLoading(false));
  }, [memberId]);

  const handleToggleActive = async () => {
    if (!detail) return;
    setSaving(true);
    const r = await updateAdminMember(detail.id, { is_active: !detail.is_active });
    if (r.ok) {
      const updated = await r.json();
      setDetail(prev => prev ? { ...prev, is_active: updated.is_active } : prev);
      toast.success(updated.is_active ? '已啟用帳號' : '已停用帳號');
      onUpdated();
    } else toast.error('操作失敗');
    setSaving(false);
  };

  const handleRoleChange = async () => {
    if (!detail || editRole === detail.role) return;
    setSaving(true);
    const r = await updateAdminMember(detail.id, { role: editRole });
    if (r.ok) {
      setDetail(prev => prev ? { ...prev, role: editRole as any } : prev);
      toast.success('角色已更新');
      onUpdated();
    } else {
      const err = await r.json();
      toast.error(err.detail || '更新失敗');
    }
    setSaving(false);
  };

  const handleResetPwd = async () => {
    if (!detail) return;
    if (!confirm(`確定要重設 ${detail.email} 的密碼？`)) return;
    setSaving(true);
    const r = await resetMemberPassword(detail.id);
    if (r.ok) {
      const data = await r.json();
      setShowTempPwd(data.temp_password);
      toast.success('密碼已重設');
    } else toast.error('重設失敗');
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[#0f1117] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Eye size={18} className="text-primary" /> 會員詳情
          </h3>
          <button onClick={onClose} className="text-text-muted hover:text-white transition-colors p-1">
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-16">
            <RefreshCw className="animate-spin text-primary" size={28} />
          </div>
        ) : detail ? (
          <div className="p-6 space-y-6">
            {/* Basic Info */}
            <div className="flex items-start gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/30 to-accent/30 border border-primary/20 flex items-center justify-center text-2xl font-black text-white shrink-0">
                {(detail.name || detail.email).charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-white font-bold text-lg">{detail.name || '—'}</span>
                  <RoleBadge role={detail.role} />
                  <StatusBadge active={detail.is_active} />
                </div>
                <div className="flex items-center gap-1 text-text-muted text-sm mt-1">
                  <Mail size={13} />{detail.email}
                </div>
                {detail.company_name && (
                  <div className="flex items-center gap-1 text-text-muted text-xs mt-0.5">
                    <Building2 size={12} />{detail.company_name}
                  </div>
                )}
                <div className="text-[10px] text-text-muted mt-1">
                  加入：{new Date(detail.created_at).toLocaleDateString('zh-TW')}
                  {detail.last_login_at && ` · 最後登入：${new Date(detail.last_login_at).toLocaleDateString('zh-TW')}`}
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: 'Leads', value: detail.stats.leads_count, icon: <Users size={14} /> },
                { label: '已寄信', value: detail.stats.emails_sent, icon: <Mail size={14} /> },
                { label: '已開信', value: detail.stats.emails_opened, icon: <Eye size={14} /> },
                { label: '開信率', value: `${detail.stats.open_rate}%`, icon: <TrendingUp size={14} /> },
              ].map(s => (
                <div key={s.label} className="bg-white/5 rounded-xl p-3 text-center border border-white/5">
                  <div className="text-text-muted flex justify-center mb-1">{s.icon}</div>
                  <div className="text-white font-black text-lg">{s.value}</div>
                  <div className="text-text-muted text-[10px]">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Usage */}
            {detail.usage && (
              <div className="bg-white/5 rounded-xl p-4 border border-white/5 space-y-3">
                <span className="text-xs font-bold text-text-muted uppercase tracking-widest">本月用量</span>
                <UsageBar used={detail.usage.customers.used} limit={detail.usage.customers.limit} label="客戶數" />
                <UsageBar used={detail.usage.emails_month.used} limit={detail.usage.emails_month.limit} label="寄信數" />
                <UsageBar used={detail.usage.autominer_runs.used} limit={detail.usage.autominer_runs.limit} label="探勘次數" />
              </div>
            )}

            {/* Subscription */}
            <div className="bg-white/5 rounded-xl p-4 border border-white/5">
              <span className="text-xs font-bold text-text-muted uppercase tracking-widest block mb-2">訂閱方案</span>
              {detail.subscription
                ? <span className="text-white font-bold">{detail.subscription.plan.display_name} <span className="text-text-muted text-xs">({detail.subscription.status})</span></span>
                : <span className="text-text-muted text-sm">無訂閱</span>
              }
              
              {/* 調整方案 */}
              {detail.role === 'member' && (
                <div className="mt-3 pt-3 border-t border-white/5">
                  <span className="text-[10px] text-text-muted block mb-2">調整方案</span>
                  <div className="flex items-center gap-2">
                    <select
                      value={detail.subscription?.plan.name || 'free'}
                      onChange={async (e) => {
                        const newPlan = e.target.value;
                        if (!confirm(`確定要將此會員方案調整為「${newPlan}」嗎？`)) return;
                        try {
                          const resp = await updateAdminMember(detail.id, { plan: newPlan });
                          if (resp.ok) {
                            toast.success('方案已更新');
                            // Refresh detail data
                            const updated = await getAdminMemberDetail(detail.id);
                            if (updated.ok) {
                              const d = await updated.json();
                              setDetail(d);
                              setEditRole(d.role);
                            }
                            // Refresh parent list
                            onUpdated();
                          } else {
                            toast.error('更新失敗');
                          }
                        } catch (err) {
                          toast.error('連線錯誤');
                        }
                      }}
                      className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary/50"
                    >
                      <option value="free">免費版</option>
                      <option value="pro">專業版</option>
                      <option value="enterprise">企業版</option>
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="border-t border-white/5 pt-4 space-y-3">
              <span className="text-xs font-bold text-text-muted uppercase tracking-widest block">管理操作</span>

              {/* Role Change */}
              <div className="flex items-center gap-3">
                <select
                  value={editRole}
                  onChange={e => setEditRole(e.target.value)}
                  className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50"
                >
                  <option value="member">Member</option>
                  <option value="vendor">Vendor</option>
                  <option value="admin">Admin</option>
                </select>
                <button
                  onClick={handleRoleChange}
                  disabled={saving || editRole === detail.role}
                  className="px-4 py-2.5 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 rounded-xl text-sm font-bold transition-all disabled:opacity-40"
                >
                  更新角色
                </button>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleToggleActive}
                  disabled={saving}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold border transition-all disabled:opacity-40 ${
                    detail.is_active
                      ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30'
                      : 'bg-green-500/10 hover:bg-green-500/20 text-green-400 border-green-500/30'
                  }`}
                >
                  {detail.is_active ? <><UserX size={15} />停用帳號</> : <><UserCheck size={15} />啟用帳號</>}
                </button>
                <button
                  onClick={handleResetPwd}
                  disabled={saving}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 transition-all disabled:opacity-40"
                >
                  <KeyRound size={15} />重設密碼
                </button>
              </div>

              {/* Temp Password Display */}
              {showTempPwd && (
                <div className="flex items-center gap-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                  <AlertTriangle size={16} className="text-yellow-400 shrink-0" />
                  <div className="flex-1">
                    <div className="text-[10px] text-yellow-400/70 mb-0.5">臨時密碼（請立即告知用戶）</div>
                    <code className="text-yellow-300 font-mono font-bold text-sm">{showTempPwd}</code>
                  </div>
                  <button onClick={() => { navigator.clipboard.writeText(showTempPwd); toast.success('已複製'); }} className="text-yellow-400 hover:text-yellow-300 text-xs border border-yellow-500/30 px-2 py-1 rounded-lg">複製</button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-16 text-center text-text-muted">找不到會員資料</div>
        )}
      </div>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const MemberAdmin: React.FC = () => {
  const [members, setMembers] = useState<Member[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [actionMenu, setActionMenu] = useState<number | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (roleFilter) params.role = roleFilter;
      if (statusFilter !== '') params.is_active = statusFilter === 'active';
      if (search) params.search = search;

      const [mRes, sRes] = await Promise.all([
        getAdminMembers(params),
        getAdminStats()
      ]);
      if (mRes.ok) setMembers(await mRes.json());
      if (sRes.ok) setStats(await sRes.json());
    } catch {
      toast.error('載入失敗');
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter, statusFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleQuickToggle = async (member: Member) => {
    const r = await updateAdminMember(member.id, { is_active: !member.is_active });
    if (r.ok) {
      setMembers(prev => prev.map(m => m.id === member.id ? { ...m, is_active: !m.is_active } : m));
      toast.success(member.is_active ? '已停用' : '已啟用');
    } else toast.error('操作失敗');
    setActionMenu(null);
  };

  const handleDelete = async (member: Member) => {
    if (!confirm(`確定要停用 ${member.email}？`)) return;
    const r = await deleteAdminMember(member.id);
    if (r.ok) {
      setMembers(prev => prev.map(m => m.id === member.id ? { ...m, is_active: false } : m));
      toast.success('已停用');
    } else toast.error('操作失敗');
    setActionMenu(null);
  };

  return (
    <div className="flex flex-col h-full gap-6 animate-in fade-in duration-500 overflow-y-auto pb-20 pr-2 custom-scrollbar">

      {/* Header */}
      <div className="bg-glass-panel p-8 rounded-2xl border border-white/5 relative overflow-hidden group">
        <div className="absolute -right-10 -top-10 opacity-5 group-hover:opacity-10 transition-opacity">
          <Users size={200} />
        </div>
        <div className="relative z-10">
          <h2 className="text-3xl font-black text-white flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/20 flex items-center justify-center border border-blue-500/20 shadow-inner">
              <Users className="w-7 h-7 text-blue-400" />
            </div>
            會員管理中心
          </h2>
          <p className="text-text-muted mt-2 text-sm">管理所有平台用戶、查看用量、調整角色與帳號狀態。</p>
        </div>
      </div>

      {/* Stats Row */}
      {stats?.users && stats?.data && (
        <div className="stats-grid">
          {[
            { label: '總會員數',  value: stats.users.total ?? 0,           icon: <Users size={18} />,     iconColor: 'var(--color-primary)',      bg: 'var(--color-primary-glow)' },
            { label: '啟用中',    value: stats.users.active ?? 0,          icon: <UserCheck size={18} />, iconColor: 'var(--color-accent-teal)',  bg: 'rgba(78,205,196,0.12)' },
            { label: '本月新增',  value: stats.users.new_this_month ?? 0,  icon: <TrendingUp size={18} />,iconColor: 'var(--color-warning)',      bg: 'rgba(245,158,11,0.12)' },
            { label: '總 Leads',  value: stats.data.total_leads ?? 0,      icon: <BarChart2 size={18} />, iconColor: 'var(--color-text-secondary)',bg: 'var(--color-bg-card)' },
          ].map(s => (
            <div key={s.label} className="stat-card">
              <div className="stat-card__icon" style={{ background: s.bg }}>
                <span style={{ color: s.iconColor }}>{s.icon}</span>
              </div>
              <div>
                <div className="stat-card__value" style={{ color: s.iconColor }}>{s.value}</div>
                <div className="stat-card__label">{s.label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Role Distribution */}
      {stats?.users?.by_role && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { role: 'admin',  count: stats.users.by_role.admin ?? 0,  label: 'Admin' },
            { role: 'vendor', count: stats.users.by_role.vendor ?? 0, label: 'Vendor' },
            { role: 'member', count: stats.users.by_role.member ?? 0, label: 'Member' },
          ].map(r => (
            <div key={r.role} className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px' }}>
              <RoleBadge role={r.role} />
              <span style={{ fontSize: 22, fontWeight: 900, color: 'var(--color-text-primary)' }}>{r.count}</span>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="搜尋 Email / 名稱 / 公司..."
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-text-muted focus:outline-none focus:border-primary/50 transition-colors"
          />
        </div>

        <div className="relative">
          <select
            value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)}
            className="appearance-none bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 pr-8 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
          >
            <option value="">所有角色</option>
            <option value="admin">Admin</option>
            <option value="vendor">Vendor</option>
            <option value="member">Member</option>
          </select>
          <ChevronDown size={13} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
        </div>

        <div className="relative">
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="appearance-none bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 pr-8 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
          >
            <option value="">所有狀態</option>
            <option value="active">啟用中</option>
            <option value="inactive">已停用</option>
          </select>
          <ChevronDown size={13} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
        </div>

        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-text-muted hover:text-white transition-all"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          重新整理
        </button>
      </div>

      {/* Table */}
      <div className="bg-glass-panel rounded-2xl border border-white/5 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20 gap-3 text-text-muted">
            <RefreshCw size={20} className="animate-spin text-primary" />
            <span className="text-sm">載入中...</span>
          </div>
        ) : members.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-text-muted">
            <Users size={40} className="opacity-30" />
            <span className="text-sm">沒有符合條件的會員</span>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-[11px] text-text-muted uppercase tracking-widest">
                <th className="text-left px-6 py-4 font-semibold">會員</th>
                <th className="text-left px-4 py-4 font-semibold">角色</th>
                <th className="text-left px-4 py-4 font-semibold">狀態</th>
                <th className="text-left px-4 py-4 font-semibold">方案</th>
                <th className="text-left px-4 py-4 font-semibold">本月用量</th>
                <th className="text-left px-4 py-4 font-semibold">加入日期</th>
                <th className="px-4 py-4" />
              </tr>
            </thead>
            <tbody>
              {members.map((m, i) => (
                <tr
                  key={m.id}
                  className={`border-b border-white/5 hover:bg-white/3 transition-colors ${i % 2 === 0 ? '' : 'bg-white/[0.02]'}`}
                >
                  {/* Member Info */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-white/10 flex items-center justify-center font-bold text-white text-sm shrink-0">
                        {(m.name || m.email).charAt(0).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <div className="text-white font-semibold truncate max-w-[160px]">{m.name || '—'}</div>
                        <div className="text-text-muted text-xs truncate max-w-[160px]">{m.email}</div>
                        {m.company_name && <div className="text-text-muted text-[10px] truncate max-w-[160px]">{m.company_name}</div>}
                      </div>
                    </div>
                  </td>

                  {/* Role */}
                  <td className="px-4 py-4"><RoleBadge role={m.role} /></td>

                  {/* Status */}
                  <td className="px-4 py-4"><StatusBadge active={m.is_active} /></td>

                  {/* Plan */}
                  <td className="px-4 py-4">
                    <span className="text-text-muted text-xs">
                      {m.subscription?.plan?.display_name ?? '無方案'}
                    </span>
                  </td>

                  {/* Usage */}
                  <td className="px-4 py-4 min-w-[120px]">
                    {m.usage ? (
                      <div className="space-y-1 w-28">
                        <UsageBar used={m.usage.emails_month.used} limit={m.usage.emails_month.limit} label="信件" />
                        <UsageBar used={m.usage.customers.used} limit={m.usage.customers.limit} label="客戶" />
                      </div>
                    ) : <span className="text-text-muted text-xs">—</span>}
                  </td>

                  {/* Date */}
                  <td className="px-4 py-4 text-text-muted text-xs whitespace-nowrap">
                    {new Date(m.created_at).toLocaleDateString('zh-TW')}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-4">
                    <div className="relative flex items-center gap-2">
                      <button
                        onClick={() => setSelectedId(m.id)}
                        className="p-1.5 rounded-lg bg-white/5 hover:bg-primary/20 text-text-muted hover:text-primary transition-all border border-white/5"
                        title="查看詳情"
                      >
                        <Eye size={14} />
                      </button>
                      <button
                        onClick={() => setActionMenu(actionMenu === m.id ? null : m.id)}
                        className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-text-muted hover:text-white transition-all border border-white/5"
                      >
                        <MoreVertical size={14} />
                      </button>

                      {actionMenu === m.id && (
                        <div className="absolute right-0 top-8 z-20 bg-[#0f1117] border border-white/10 rounded-xl shadow-2xl overflow-hidden min-w-[140px]">
                          <button
                            onClick={() => handleQuickToggle(m)}
                            className={`w-full flex items-center gap-2 px-4 py-2.5 text-xs hover:bg-white/5 transition-colors ${m.is_active ? 'text-red-400' : 'text-green-400'}`}
                          >
                            {m.is_active ? <><UserX size={13} />停用帳號</> : <><UserCheck size={13} />啟用帳號</>}
                          </button>
                          <button
                            onClick={() => handleDelete(m)}
                            className="w-full flex items-center gap-2 px-4 py-2.5 text-xs text-red-400 hover:bg-white/5 transition-colors"
                          >
                            <Trash2 size={13} />刪除
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Footer */}
        {!loading && members.length > 0 && (
          <div className="px-6 py-3 border-t border-white/5 text-xs text-text-muted">
            共 {members.length} 筆會員
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedId !== null && (
        <DetailModal
          memberId={selectedId}
          onClose={() => setSelectedId(null)}
          onUpdated={fetchData}
        />
      )}

      {/* Close action menu on outside click */}
      {actionMenu !== null && (
        <div className="fixed inset-0 z-10" onClick={() => setActionMenu(null)} />
      )}
    </div>
  );
};

export default MemberAdmin;
