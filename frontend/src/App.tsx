// App.tsx entry
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';

// Pages
import LeadEngine from './pages/LeadEngine';
import Templates from './pages/Templates';
import Campaigns from './pages/Campaigns';
import Analytics from './pages/Analytics';
import History from './pages/History';

// Placeholder Pages (To be migrated)
const Smtp = () => <div className="p-4 glass-panel flex-1 h-full"><h1>SMTP Settings (WIP)</h1></div>;

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
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
            <Route path="smtp" element={<Smtp />} />
            
            {/* Admin Routes (WIP) */}
            <Route path="admin/partners" element={<div className="p-4 glass-panel text-warning flex-1 h-full">Partner Admin (WIP)</div>} />
            <Route path="admin/settings" element={<div className="p-4 glass-panel text-warning flex-1 h-full">System Settings (WIP)</div>} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
