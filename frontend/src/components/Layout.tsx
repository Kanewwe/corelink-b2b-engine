import React, { useEffect, useState, useRef } from 'react';
import { Outlet, Navigate, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, ChevronDown } from 'lucide-react';

const PAGE_TITLES: Record<string, string> = {
  '/lead-engine':    'Linkora - 精準開發雷達',
  '/templates':      'Linkora - 智慧行銷劇本',
  '/campaigns':      'Linkora - 自動化投遞',
  '/analytics':      'Linkora - 成效分析雷達',
  '/history':        'Linkora - 開發紀錄專區',
  '/smtp':           'Linkora - 發信通道配置',
  '/admin/settings': 'Linkora - 系統控制中心',
  '/admin/vendors':  'Linkora - 委外廠商管理',
  '/admin/members':  'Linkora - 會員管理',
};

const Layout: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const match = Object.keys(PAGE_TITLES).find(k => location.pathname.startsWith(k));
    document.title = match ? PAGE_TITLES[match] : 'Linkora';
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
    <div className="flex h-screen p-4 gap-6 overflow-hidden bg-gradient-to-br from-bg-dark to-bg-content text-text-main">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-y-auto overflow-x-hidden pb-5">
        {/* 右上角 User Dropdown */}
        <div className="flex justify-end items-center py-3 mb-2 shrink-0">
          <div className="relative" ref={dropdownRef}>
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
                  className="w-full flex items-center gap-2.5 px-4 py-3 text-sm text-text-muted hover:text-error hover:bg-error/5 transition-colors"
                >
                  <LogOut size={14} /> 登出
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 flex-1 flex flex-col h-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
