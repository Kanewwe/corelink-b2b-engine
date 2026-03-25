import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Search, FileText, Send, BarChart2, Clock, Settings, Users, Shield, LogOut 
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const NavItem = ({ to, icon, label }: { to: string, icon: React.ReactNode, label: string }) => (
    <NavLink 
      to={to} 
      className={({ isActive }) => 
        `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
          isActive 
            ? 'bg-primary/15 text-primary border-l-4 border-primary pl-3' 
            : 'text-text-muted hover:bg-primary/10 hover:text-text-main'
        }`
      }
    >
      {icon}
      <span>{label}</span>
    </NavLink>
  );

  return (
    <aside className="w-[250px] p-6 flex flex-col shrink-0 bg-bg-dark border-r border-glass-border">
      <div className="flex items-center gap-3 mb-10">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent shadow-[0_0_15px_rgba(79,142,247,0.4)] flex items-center justify-center text-bg-dark font-bold text-lg">
          L
        </div>
        <h1 className="text-xl font-bold bg-gradient-to-br from-primary to-accent bg-clip-text text-transparent">
          Linkora
        </h1>
      </div>

      <nav className="flex flex-col gap-2 flex-1 overflow-y-auto pr-2">
        <div className="text-xs font-semibold text-text-muted mt-2 mb-1 px-4 tracking-wider uppercase">主要功能</div>
        <NavItem to="/lead-engine" icon={<Search size={18} />} label="Lead Engine" />

        <div className="text-xs font-semibold text-text-muted mt-6 mb-1 px-4 tracking-wider uppercase">寄信作業</div>
        <NavItem to="/templates" icon={<FileText size={18} />} label="信件模板" />
        <NavItem to="/campaigns" icon={<Send size={18} />} label="寄信記錄" />

        <div className="text-xs font-semibold text-text-muted mt-6 mb-1 px-4 tracking-wider uppercase">分析</div>
        <NavItem to="/analytics" icon={<BarChart2 size={18} />} label="觸及率分析" />
        <NavItem to="/history" icon={<Clock size={18} />} label="探勘歷史" />

        <div className="text-xs font-semibold text-text-muted mt-6 mb-1 px-4 tracking-wider uppercase">設定</div>
        <NavItem to="/smtp" icon={<Settings size={18} />} label="SMTP 設定" />

        {/* Phase 1 & 2 preparation: Admin Only Section */}
        {user?.role === 'admin' && (
          <>
            <div className="text-xs font-semibold text-text-muted mt-6 mb-1 px-4 tracking-wider uppercase text-warning">管理 (Admin)</div>
            <NavItem to="/admin/vendors" icon={<Users size={18} />} label="委外廠商管理" />
            <NavItem to="/admin/settings" icon={<Shield size={18} />} label="系統設定" />
          </>
        )}
      </nav>

      <div className="mt-auto pt-5 border-t border-glass-border">
        <div className="flex items-center gap-3 p-3 bg-primary/10 rounded-lg">
          <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-full flex items-center justify-center font-bold text-bg-dark">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="flex-1 overflow-hidden">
            <div className="font-semibold text-sm truncate text-text-main">{user?.username || user?.email || 'User'}</div>
            <div className="text-xs text-text-muted uppercase tracking-wider">{user?.role || 'Member'}</div>
          </div>
          <button 
            onClick={handleLogout}
            className="p-1 text-text-muted hover:text-error transition-colors"
            title="登出"
          >
            <LogOut size={18} />
          </button>
        </div>
        <p className="text-text-muted text-xs text-center mt-4">Linkora v2.0</p>
      </div>
    </aside>
  );
};

export default Sidebar;
