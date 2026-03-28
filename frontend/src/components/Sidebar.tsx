import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Search, FileText, Send, BarChart2, Clock, Settings, Users, Cpu, UserCog,
  ChevronLeft, ChevronRight, Monitor, Bug, FlaskConical, Activity, Inbox as InboxIcon, type LucideIcon
} from 'lucide-react';

interface NavItemData {
  to: string;
  icon: LucideIcon;
  label: string;
}

interface NavSection {
  title: string;
  items: NavItemData[];
  adminOnly?: boolean;
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: '主要功能',
    items: [
      { to: '/lead-engine', icon: Search, label: '精準開發雷達' },
    ],
  },
  {
    title: '寄信作業',
    items: [
      { to: '/templates', icon: FileText, label: '智慧行銷劇本' },
      { to: '/campaigns', icon: Send, label: '自動化投遞' },
    ],
  },
  {
    title: '分析',
    items: [
      { to: '/analytics', icon: BarChart2, label: '成效分析雷達' },
      { to: '/history', icon: Clock, label: '開發紀錄專區' },
      { to: '/inbox', icon: InboxIcon, label: 'AI 智慧收件匣' },
    ],
  },
  {
    title: '設定',
    items: [
      { to: '/smtp', icon: Settings, label: '發信通道配置' },
    ],
  },
  {
    title: '管理 (Admin)',
    adminOnly: true,
    items: [
      { to: '/admin/dashboard', icon: Monitor, label: '系統監控' },
      { to: '/admin/scrape-monitor', icon: Bug, label: '爬蟲監控' },
      { to: '/admin/scraper-health', icon: Activity, label: '探勘健康雷達' },
      { to: '/admin/research', icon: FlaskConical, label: '爬蟲調研實驗室' },
      { to: '/admin/members', icon: UserCog, label: '會員管理' },
      { to: '/admin/vendors', icon: Users, label: '廠商管理' },
      { to: '/admin/settings', icon: Cpu, label: '系統控制中心' },
    ],
  },
];

const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);


  const toggleCollapse = () => setCollapsed(v => !v);

  const NavItem = ({ to, icon: Icon, label }: { to: string; icon: LucideIcon; label: string }) => {
    if (collapsed) {
      // ── Mini mode: icon only with tooltip ──
      return (
        <div className="relative group">
          <NavLink
            to={to}
            className={({ isActive }) =>
              `flex items-center justify-center w-10 h-10 rounded-lg text-lg transition-all mx-auto ${
                isActive
                  ? 'bg-primary/15 text-primary shadow-[0_0_12px_rgba(79,142,247,0.2)]'
                  : 'text-text-muted hover:bg-white/5 hover:text-text-main'
              }`
            }
          >
            <Icon size={20} />
          </NavLink>
          {/* Tooltip */}
          <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-3 py-1.5 bg-[#1e2538] text-white text-xs font-medium rounded-lg shadow-xl border border-white/10 whitespace-nowrap opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 pointer-events-none">
            {label}
            <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-[#1e2538]" />
          </div>
        </div>
      );
    }

    // ── Full mode: icon + text ──
    return (
      <NavLink
        to={to}
        className={({ isActive }) =>
          `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
            isActive
              ? 'bg-primary/15 text-primary border-l-4 border-primary pl-3'
              : 'text-text-muted hover:bg-primary/10 hover:text-text-main'
          }`
        }
      >
        <Icon size={18} className="shrink-0" />
        <span className="truncate">{label}</span>
      </NavLink>
    );
  };

  const SectionLabel = ({ title }: { title: string }) => {
    if (collapsed) {
      return (
        <div className="relative group w-full flex justify-center my-3">
          <div className="w-6 h-px bg-white/10" />
          <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-2 py-1 bg-[#1e2538] text-text-muted text-[10px] font-semibold uppercase tracking-widest rounded-lg shadow-xl border border-white/10 whitespace-nowrap opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 pointer-events-none">
            {title}
            <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-[#1e2538]" />
          </div>
        </div>
      );
    }
    return (
      <div className="text-[10px] font-semibold text-text-muted mt-5 mb-1.5 px-4 tracking-widest uppercase">
        {title}
      </div>
    );
  };

  return (
    <aside
      className={`flex flex-col bg-bg-dark border-r border-glass-border transition-all duration-300 ease-in-out h-full ${
        collapsed ? 'w-[68px]' : 'w-[250px]'
      }`}
    >
      {/* ── Logo Area ── */}
      <div className="flex items-center gap-3 p-4 shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent shadow-[0_0_15px_rgba(79,142,247,0.4)] flex items-center justify-center text-bg-dark font-bold text-lg shrink-0">
          L
        </div>
        {!collapsed && (
          <h1 className="text-xl font-bold bg-gradient-to-br from-primary to-accent bg-clip-text text-transparent whitespace-nowrap">
            Linkora
          </h1>
        )}
      </div>

      {/* ── Navigation (scrollable) ── */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2 scrollbar-thin">
        {NAV_SECTIONS.map(section => {
          if (section.adminOnly && user?.role !== 'admin') return null;
          return (
            <div key={section.title}>
              <SectionLabel title={section.title} />
              <div className="flex flex-col gap-1">
                {section.items.map(item => (
                  <NavItem key={item.to} {...item} />
                ))}
              </div>
            </div>
          );
        })}
      </nav>

      {/* ── Bottom Area ── */}
      <div className="shrink-0 border-t border-glass-border">
        {/* Collapse Toggle */}
        <button
          onClick={toggleCollapse}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-text-muted hover:text-text-main hover:bg-white/5 transition-colors text-xs"
          title={collapsed ? '展開選單' : '收合選單'}
        >
          {collapsed ? <ChevronRight size={16} /> : (
            <>
              <ChevronLeft size={16} />
              <span>收合選單</span>
            </>
          )}
        </button>

        {/* User Info (Removed in v3.7.21, consolidated to Top-Right Header) */}
        {!collapsed && (
          <div className="px-4 py-2 text-[10px] text-text-muted text-center border-t border-white/5 opacity-50">
            Linkora Engine v3.7.21
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
