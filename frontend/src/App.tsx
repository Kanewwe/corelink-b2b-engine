// App.tsx entry
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import RoleGuard from './components/RoleGuard';
import { Toaster } from 'react-hot-toast';

// Pages
import LeadEngine from './pages/LeadEngine';
import Templates from './pages/Templates';
import Campaigns from './pages/Campaigns';
import Analytics from './pages/Analytics';
import History from './pages/History';
import VendorAdmin from './pages/VendorAdmin';
import SmtpSettings from './pages/SmtpSettings';
import SystemSettings from './pages/SystemSettings';
import MemberAdmin from './pages/MemberAdmin';
import AdminDashboard from './pages/AdminDashboard';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
        <Routes>
          <Route path="/login" element={<Login />} />
          
          {/* Authenticated Routes Array */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/lead-engine" replace />} />
            <Route path="lead-engine" element={<LeadEngine />} />
            <Route path="templates" element={<Templates />} />
            <Route path="campaigns" element={<Campaigns />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="history" element={<History />} />
            <Route path="smtp" element={<SmtpSettings />} />
            
            {/* Admin Routes */}
            <Route path="admin/dashboard" element={
              <RoleGuard require={['admin']}>
                <AdminDashboard />
              </RoleGuard>
            } />
            <Route path="admin/vendors" element={
              <RoleGuard require={['admin']}>
                <VendorAdmin />
              </RoleGuard>
            } />
            <Route path="admin/settings" element={
              <RoleGuard require={['admin']}>
                <SystemSettings />
              </RoleGuard>
            } />
            <Route path="admin/members" element={
              <RoleGuard require={['admin']}>
                <MemberAdmin />
              </RoleGuard>
            } />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
