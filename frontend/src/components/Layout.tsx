import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuth } from '../contexts/AuthContext';

const Layout: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-screen p-4 gap-6 overflow-hidden bg-gradient-to-br from-bg-dark to-bg-content text-text-main">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-y-auto overflow-x-hidden pb-5">
        <header className="flex justify-between items-center py-4 mb-4">
          <h2 className="text-2xl font-semibold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            Linkora — AI Prospecting
          </h2>
        </header>
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 flex-1 flex flex-col h-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
