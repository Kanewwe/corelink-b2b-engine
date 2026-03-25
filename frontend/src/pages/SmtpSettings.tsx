import React, { useState, useEffect } from 'react';
import { getSmtpSettings, saveSmtpSettings } from '../services/api';
import { Mail, Shield, Server, User, Key, Save, AlertCircle, CheckCircle2 } from 'lucide-react';

const SmtpSettings: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  
  const [form, setForm] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_encryption: 'tls',
    from_email: '',
    from_name: 'Linkora Prospecting'
  });

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const resp = await getSmtpSettings();
        if (resp.ok) {
          const data = await resp.json();
          if (data) {
            setForm({
              smtp_host: data.smtp_host || '',
              smtp_port: data.smtp_port || 587,
              smtp_user: data.smtp_user || '',
              smtp_password: data.smtp_password || '', // Usually we shouldn't show it but for now we follow the simple logic
              smtp_encryption: data.smtp_encryption || 'tls',
              from_email: data.from_email || '',
              from_name: data.from_name || 'Linkora Prospecting'
            });
          }
        }
      } catch (e) {
        console.error("Failed to load SMTP settings", e);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const resp = await saveSmtpSettings(form);
      if (resp.ok) {
        setMessage({ type: 'success', text: 'SMTP 設定已成功儲存！' });
      } else {
        const err = await resp.json();
        setMessage({ type: 'error', text: err.detail || '儲存失敗' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: '網路錯誤，請稍後再試' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-text-muted">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mr-3"></div>
        載入設定中...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full gap-6">
      <header>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Mail className="w-7 h-7 text-primary" />
          SMTP 發信設定
        </h2>
        <p className="text-text-muted text-sm mt-1">設定您的郵件伺服器，以便系統自動發送開發信與觸及客戶。</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="glass-panel p-8 space-y-6 border border-white/10">
            {message && (
              <div className={`p-4 rounded-lg flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300 ${
                message.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
              }`}>
                {message.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                <span className="text-sm font-medium">{message.text}</span>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-muted flex items-center gap-2">
                  <Server className="w-4 h-4" /> SMTP 主機位址
                </label>
                <input 
                  required
                  placeholder="e.g. smtp.gmail.com"
                  className="input-field"
                  value={form.smtp_host}
                  onChange={e => setForm({...form, smtp_host: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-muted flex items-center gap-2">
                  <Shield className="w-4 h-4" /> 埠號 (Port)
                </label>
                <input 
                  required
                  type="number"
                  placeholder="587"
                  className="input-field"
                  value={form.smtp_port}
                  onChange={e => setForm({...form, smtp_port: parseInt(e.target.value)})}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-muted flex items-center gap-2">
                  <User className="w-4 h-4" /> 帳號 (Username)
                </label>
                <input 
                  required
                  placeholder="your-email@gmail.com"
                  className="input-field"
                  value={form.smtp_user}
                  onChange={e => setForm({...form, smtp_user: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-muted flex items-center gap-2">
                  <Key className="w-4 h-4" /> 密碼 (Password)
                </label>
                <input 
                  required
                  type="password"
                  placeholder="••••••••"
                  className="input-field"
                  value={form.smtp_password}
                  onChange={e => setForm({...form, smtp_password: e.target.value})}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-muted">加密方式</label>
                <select 
                  className="input-field bg-transparent"
                  value={form.smtp_encryption}
                  onChange={e => setForm({...form, smtp_encryption: e.target.value})}
                >
                  <option value="tls" className="bg-bg-dark text-white">STARTTLS (推薦)</option>
                  <option value="ssl" className="bg-bg-dark text-white">SSL/TLS</option>
                  <option value="none" className="bg-bg-dark text-white">無 (不安全)</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-muted">寄件者名稱</label>
                <input 
                  placeholder="Linkora Sales Team"
                  className="input-field"
                  value={form.from_name}
                  onChange={e => setForm({...form, from_name: e.target.value})}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-text-muted">預設寄件 Email (選填)</label>
              <input 
                type="email"
                placeholder="sales@yourcompany.com"
                className="input-field"
                value={form.from_email}
                onChange={e => setForm({...form, from_email: e.target.value})}
              />
              <p className="text-[10px] text-text-muted italic mt-1">若留空，將預設使用登入帳號作為寄件者。</p>
            </div>

            <div className="pt-4 border-t border-white/5">
              <button 
                type="submit"
                disabled={saving}
                className="flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white px-8 py-3 rounded-xl transition-all shadow-xl shadow-primary/20 font-bold w-full md:w-auto disabled:opacity-50"
              >
                {saving ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Save className="w-5 h-5" />
                )}
                儲存設定
              </button>
            </div>
          </form>
        </div>

        <div className="space-y-6">
          <div className="glass-panel p-6 border border-white/10 bg-primary/5">
            <h4 className="font-bold text-white mb-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-primary" /> 常見設定指南
            </h4>
            <div className="space-y-4 text-xs text-text-muted leading-relaxed">
              <div>
                <strong className="text-white block mb-1">Gmail 設定：</strong>
                <ul className="list-disc ml-4 space-y-1">
                  <li>主機：smtp.gmail.com</li>
                  <li>埠號：587 (TLS)</li>
                  <li>需使用 <span className="text-primary-light">「應用程式密碼」</span>，直接使用 Google 密碼會被拒絕。</li>
                </ul>
              </div>
              <div>
                <strong className="text-white block mb-1">Outlook / Office 365：</strong>
                <ul className="list-disc ml-4 space-y-1">
                  <li>主機：smtp.office365.com</li>
                  <li>埠號：587 (TLS)</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 border border-white/10">
            <h4 className="font-bold text-white mb-3 underline decoration-primary">測試功能 (即將推出)</h4>
            <p className="text-xs text-text-muted">
              儲存後，您可以嘗試點擊「傳送測試信」按鈕來驗證設定是否正確。目前功能開發中。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SmtpSettings;
