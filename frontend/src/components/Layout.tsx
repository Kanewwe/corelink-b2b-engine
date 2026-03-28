import React, { useEffect, useState, useRef } from 'react';
import { Outlet, Navigate, useLocation, useNavigate, NavLink } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, ChevronDown, Menu, X, Search, FileText, Send, BarChart2, Settings } from 'lucide-react';

const PAGE_TITLES: Record<string, string> = {
  '/lead-engine':    'Linkora - 精準開發雷達',
  '/templates':      'Linkora - 智慧行銷劇本',
  '/campaigns':      'Linkora - 自動化投遞',
  '/analytics':      'Linkora - 成效分析雷達',
  '/history':        'Linkora - 開發紀錄專區',
  '/smtp':           'Linkora - 發信通道配置',
  '/admin/settings': 'Linkora - 系統控制中心',
  '/admin/vendors':  'Linkora - 廠商管理',
  '/admin/members':  'Linkora - 會員管理',
  '/admin/dashboard':'Linkora - 系統監控',
  '/admin/research': 'Linkora - 爬蟲調研實驗室',
  '/admin/intelligence': 'Linkora - 情資庫管理中心',
};

// 底部 TabBar 項目（手機版主要導覽）
const TAB_ITEMS = [
  { to: '/lead-engine', icon: Search,   label: '探勘' },
  { to: '/templates',   icon: FileText, label: '模板' },
  { to: '/campaigns',   icon: Send,     label: '投遞' },
  { to: '/analytics',   icon: BarChart2,label: '分析' },
  { to: '/smtp',        icon: Settings, label: '設定' },
];

const Layout: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 動態更新 <title>
  useEffect(() => {
    const match = Object.keys(PAGE_TITLES).find(k => location.pathname.startsWith(k));
    document.title = match ? PAGE_TITLES[match] : 'Linkora';
  }, [location.pathname]);

  // 路由切換時關閉 sidebar
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  // 點外部關閉 dropdown
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen p-4 gap-6 overflow-hidden bg-gradient-to-br from-bg-dark to-bg-content text-text-main layout-root">

      {/* ── Desktop Sidebar ── */}
      <div className="hidden md:block shrink-0">
        <Sidebar />
      </div>

      {/* ── Mobile Sidebar Drawer ── */}
      <div className={`sidebar-drawer md:hidden ${sidebarOpen ? 'open' : ''}`}>
        <Sidebar />
      </div>
      <div
        className={`sidebar-overlay md:hidden ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* ── Main Content ── */}
      <main className="flex-1 flex flex-col overflow-y-auto overflow-x-hidden pb-24 layout-main">

        {/* Top Bar */}
        <div className="flex justify-between items-center py-3 mb-2 shrink-0">
          {/* Hamburger (mobile only) */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-white/5 text-text-muted transition-colors"
            onClick={() => setSidebarOpen(v => !v)}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          {/* User Dropdown */}
          <div className="relative ml-auto" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(v => !v)}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-white/5 transition-colors border border-transparent hover:border-white/10"
            >
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center font-bold text-white text-xs border border-white/10">
                {((user?.name || user?.email || 'U')[0] || 'U').toUpperCase()}
              </div>
              <div className="text-right hidden sm:block">
                <div className="text-xs font-bold text-white leading-tight">{user?.name || user?.email}</div>
                <div className="text-[10px] text-text-muted capitalize">{user?.role}</div>
              </div>
              <ChevronDown size={14} className={`text-text-muted transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 top-full mt-2 w-44 bg-[#161b27] border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-white/5">
                  <div className="text-xs font-bold text-white truncate">{user?.email}</div>
                  <div className="text-[10px] text-text-muted capitalize mt-0.5">{user?.role} Account</div>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-4 py-3 text-sm text-text-muted hover:text-red-400 hover:bg-red-500/5 transition-colors"
                >
                  <LogOut size={14} /> 登出
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Page Content */}
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 flex-1 flex flex-col h-full">
          <Outlet />
        </div>
      </main>

      {/* ── M2: Bottom TabBar (mobile only) ── */}
      <nav className="bottom-tabbar">
        {TAB_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `bottom-tabbar__item${isActive ? ' active' : ''}`}
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
};

export default Layout;
