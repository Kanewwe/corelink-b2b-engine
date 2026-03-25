import React from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuth } from '../contexts/AuthContext';

const Layout: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const getPageTitle = () => {
    const path = location.pathname;
    if (path.includes('/lead-engine')) return '精準開發雷達 (Precision Radar)';
    if (path.includes('/templates')) return '智慧行銷劇本 (AI Scripts)';
    if (path.includes('/campaigns')) return '自動化投遞 (Automated Outreach)';
    if (path.includes('/analytics')) return '成效分析雷達 (Performance Radar)';
    if (path.includes('/history')) return '開發紀錄專區 (Campaign Archive)';
    if (path.includes('/admin/settings')) return '系統控制中心 (System Hub)';
    if (path.includes('/admin/vendors')) return '廠商管理';
    return 'Dashboard';
  };

  return (
    <div className="flex h-screen p-4 gap-6 overflow-hidden bg-gradient-to-br from-bg-dark to-bg-content text-text-main">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-y-auto overflow-x-hidden pb-5">
        <header className="flex justify-between items-center py-4 mb-4">
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              {getPageTitle()}
            </h2>
            <div className="text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded border border-primary/20 font-bold uppercase tracking-widest h-fit">
              Linkora V2
            </div>
          </div>
          <div className="flex items-center gap-3">
             <div className="text-right">
                <div className="text-xs font-bold text-white">{user?.name}</div>
                <div className="text-[10px] text-text-muted capitalize">{user?.role} Account</div>
             </div>
             <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center font-bold text-white text-xs border border-white/10 shadow-lg">
                {user?.name?.[0] || 'U'}
             </div>
          </div>
        </header>
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 flex-1 flex flex-col h-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
