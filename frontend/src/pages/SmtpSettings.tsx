import React, { useState, useEffect } from 'react';
import { getSmtpSettings, saveSmtpSettings } from '../services/api';
import { Mail, Shield, Server, User, Key, Save, AlertCircle, CheckCircle2, Sparkles, Globe, Zap, Cpu } from 'lucide-react';
import { toast } from 'react-hot-toast';

const SmtpSettings: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
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
              smtp_password: data.smtp_password || '',
              smtp_encryption: data.smtp_encryption || 'tls',
              from_email: data.from_email || '',
              from_name: data.from_name || 'Linkora Prospecting'
            });
          }
        }
      } catch (e) {
        toast.error("讀取設定失敗");
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const loadingToast = toast.loading("正在儲存發信通道設定...");
    try {
      const resp = await saveSmtpSettings(form);
      if (resp.ok) {
        toast.success("發信通道設定已更新", { id: loadingToast });
      } else {
        const err = await resp.json();
        toast.error(err.detail || "儲存失敗", { id: loadingToast });
      }
    } catch (e) {
      toast.error("網路連線錯誤", { id: loadingToast });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-text-muted gap-4">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
        <div className="text-sm font-medium tracking-widest uppercase animate-pulse">Initializing Channels...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-500 pb-20">
      <div className="flex items-center justify-between bg-glass-panel p-6 rounded-2xl border border-white/5">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
              <Zap className="w-6 h-6 text-primary" />
            </div>
            發信通道配置 (Email Channels)
          </h2>
          <p className="text-text-muted text-sm mt-1 ml-13">配置您的專業 SMTP 伺服器，確保開發信能精準投遞至客戶收件箱。</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-400 rounded-full border border-green-500/20 text-xs font-bold">
          <CheckCircle2 className="w-4 h-4" /> 系統連線狀態: 運作中
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <form onSubmit={handleSubmit} className="lg:col-span-2 flex flex-col gap-6">
          
          {/* Section 1: Server Config */}
          <div className="glass-panel p-8 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
              <Server size={120} />
            </div>
            <div className="flex items-center gap-2 mb-6 text-primary">
              <Cpu className="w-5 h-5" />
              <h3 className="text-lg font-bold text-white uppercase tracking-wider">01. 伺服器連線配置</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-muted uppercase flex items-center gap-2 ml-1">
                  SMTP 主機位址 (Host)
                </label>
                <div className="relative">
                  <Server className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input 
                    required
                    placeholder="e.g. smtp.gmail.com"
                    className="input-field pl-11"
                    value={form.smtp_host}
                    onChange={e => setForm({...form, smtp_host: e.target.value})}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-muted uppercase flex items-center gap-2 ml-1">
                  傳輸埠號 (Port)
                </label>
                <div className="relative">
                  <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input 
                    required
                    type="number"
                    placeholder="587"
                    className="input-field pl-11"
                    value={form.smtp_port}
                    onChange={e => setForm({...form, smtp_port: parseInt(e.target.value)})}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-muted uppercase flex items-center gap-2 ml-1">
                  加密協議 (Encryption)
                </label>
                <div className="relative">
                  <Shield className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <select 
                    className="input-field pl-11 appearance-none"
                    value={form.smtp_encryption}
                    onChange={e => setForm({...form, smtp_encryption: e.target.value})}
                  >
                    <option value="tls" className="bg-[#1e2330]">STARTTLS (推薦 587)</option>
                    <option value="ssl" className="bg-[#1e2330]">SSL/TLS (465)</option>
                    <option value="none" className="bg-[#1e2330]">不加密 (不建議)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Auth Profile */}
          <div className="glass-panel p-8 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
              <User size={120} />
            </div>
            <div className="flex items-center gap-2 mb-6 text-accent">
              <Sparkles className="w-5 h-5" />
              <h3 className="text-lg font-bold text-white uppercase tracking-wider">02. 認證與寄件人身份</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-muted uppercase flex items-center gap-2 ml-1">
                  認證帳號 (Username)
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input 
                    required
                    placeholder="your-email@gmail.com"
                    className="input-field pl-11"
                    value={form.smtp_user}
                    onChange={e => setForm({...form, smtp_user: e.target.value})}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-muted uppercase flex items-center gap-2 ml-1">
                  授權密碼 (Password)
                </label>
                <div className="relative">
                  <Key className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input 
                    required
                    type="password"
                    placeholder="••••••••"
                    className="input-field pl-11"
                    value={form.smtp_password}
                    onChange={e => setForm({...form, smtp_password: e.target.value})}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-muted uppercase flex items-center gap-2 ml-1">
                  顯示寄件人名稱
                </label>
                <input 
                  placeholder="Linkora Sales Team"
                  className="input-field"
                  value={form.from_name}
                  onChange={e => setForm({...form, from_name: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-muted uppercase flex items-center gap-2 ml-1">
                  預設回信 Email (選填)
                </label>
                <input 
                  type="email"
                  placeholder="sales@yourcompany.com"
                  className="input-field text-primary"
                  value={form.from_email}
                  onChange={e => setForm({...form, from_email: e.target.value})}
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4 pb-10">
            <button 
              type="submit"
              disabled={saving}
              className="flex items-center gap-3 bg-primary hover:bg-primary-dark text-white px-10 py-4 rounded-2xl transition-all shadow-2xl shadow-primary/30 font-bold group disabled:opacity-50"
            >
              {saving ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <Save className="w-5 h-5 group-hover:scale-110 transition-transform" />
              )}
              儲存並啟用發信通道
            </button>
          </div>
        </form>

        <aside className="space-y-6">
          <div className="glass-panel p-6 border border-primary/20 bg-primary/5 relative overflow-hidden">
            <div className="absolute -right-4 -top-4 text-primary opacity-10">
              <AlertCircle size={80} />
            </div>
            <h4 className="font-bold text-white mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-primary" /> 發信指南
            </h4>
            <div className="space-y-5 text-sm leading-relaxed">
              <div className="bg-bg-dark/50 p-3 rounded-xl border border-white/5">
                <strong className="text-primary block mb-1">Google Gmail:</strong>
                <p className="text-[11px] text-text-muted">必須使用「網頁應用程式密碼」。請至 Google 帳戶 {"->"} 安全性 {"->"} 2 步驗證 {"->"} 應用程式密碼中產生。</p>
              </div>
              <div className="bg-bg-dark/50 p-3 rounded-xl border border-white/5">
                <strong className="text-accent block mb-1">Outlook / O365:</strong>
                <p className="text-[11px] text-text-muted">主機: smtp.office365.com<br/>埠號: 587 (TLS)</p>
              </div>
              <div className="p-2 border border-warning/20 bg-warning/5 rounded-lg">
                <p className="text-[10px] text-warning">提醒：頻繁發送開發信建議配置專門的營收域名，以防主域名權重受損。</p>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 border border-white/10 group cursor-help">
            <h4 className="font-bold text-white mb-2 flex items-center gap-2 group-hover:text-primary transition-colors">
              <Mail className="w-4 h-4" /> 通道測試工具
            </h4>
            <p className="text-xs text-text-muted leading-relaxed">
              系統將會發送一封數位簽名的測試郵件至您的帳號，以確保連線協議、TLS 握手及認證參數完全正確。
            </p>
            <button disabled className="mt-4 w-full py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold text-text-muted hover:bg-white/10 transition-all">
              通道測試即將推出
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default SmtpSettings;
