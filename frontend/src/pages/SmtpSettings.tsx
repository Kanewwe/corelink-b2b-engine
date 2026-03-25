import React, { useState, useEffect } from 'react';
import { getSmtpSettings, saveSmtpSettings } from '../services/api';
import { Mail, Shield, Server, User, Key, Save, AlertCircle, CheckCircle2, Sparkles, Globe, Zap } from 'lucide-react';
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
          if (data) setForm({ smtp_host: data.smtp_host || '', smtp_port: data.smtp_port || 587, smtp_user: data.smtp_user || '', smtp_password: data.smtp_password || '', smtp_encryption: data.smtp_encryption || 'tls', from_email: data.from_email || '', from_name: data.from_name || 'Linkora Prospecting' });
        }
      } catch { toast.error('讀取設定失敗'); }
      finally { setLoading(false); }
    };
    fetchSettings();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const id = toast.loading('正在儲存發信通道設定...');
    try {
      const resp = await saveSmtpSettings(form);
      if (resp.ok) toast.success('發信通道設定已更新', { id });
      else { const err = await resp.json(); toast.error(err.detail || '儲存失敗', { id }); }
    } catch { toast.error('網路連線錯誤', { id }); }
    finally { setSaving(false); }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <span>Initializing Channels...</span>
      </div>
    );
  }

  return (
    <div className="page-wrapper">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              發信通道配置
              <span className="page-title__en">Email Channels</span>
            </h1>
            <span className="version-badge">LINKORA V2</span>
          </div>
          <p className="page-subtitle">配置您的專業 SMTP 伺服器，確保開發信能精準投遞至客戶收件箱。</p>
        </div>
        <div className="page-header__right">
          <div className="badge badge--success" style={{ padding: '6px 14px', fontSize: '12px' }}>
            <CheckCircle2 size={13} style={{ marginRight: 6 }} />
            系統運作中
          </div>
        </div>
      </div>

      {/* ── Main Content ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24 }}>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* 伺服器連線配置 */}
          <div className="card">
            <div className="card__header">
              <h3 className="card__title">
                <Server size={16} style={{ color: 'var(--color-primary)' }} />
                伺服器連線配置
              </h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              <div>
                <label className="form-label">SMTP 主機位址 (Host)</label>
                <div className="form-input-wrapper">
                  <Server size={14} className="input-icon" />
                  <input required placeholder="e.g. smtp.gmail.com" className="form-input"
                    value={form.smtp_host} onChange={e => setForm({ ...form, smtp_host: e.target.value })} />
                </div>
              </div>
              <div>
                <label className="form-label">傳輸埠號 (Port)</label>
                <div className="form-input-wrapper">
                  <Globe size={14} className="input-icon" />
                  <input required type="number" placeholder="587" className="form-input"
                    value={form.smtp_port} onChange={e => setForm({ ...form, smtp_port: parseInt(e.target.value) })} />
                </div>
              </div>
              <div>
                <label className="form-label">加密協議 (Encryption)</label>
                <div className="form-input-wrapper">
                  <Shield size={14} className="input-icon" />
                  <select className="form-select" style={{ paddingLeft: 38 }}
                    value={form.smtp_encryption} onChange={e => setForm({ ...form, smtp_encryption: e.target.value })}>
                    <option value="tls">STARTTLS（推薦 587）</option>
                    <option value="ssl">SSL/TLS（465）</option>
                    <option value="none">不加密（不建議）</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* 認證與寄件人身份 */}
          <div className="card">
            <div className="card__header">
              <h3 className="card__title">
                <Sparkles size={16} style={{ color: 'var(--color-accent-teal)' }} />
                認證與寄件人身份
              </h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              <div>
                <label className="form-label">認證帳號 (Username)</label>
                <div className="form-input-wrapper">
                  <User size={14} className="input-icon" />
                  <input required placeholder="your-email@gmail.com" className="form-input"
                    value={form.smtp_user} onChange={e => setForm({ ...form, smtp_user: e.target.value })} />
                </div>
              </div>
              <div>
                <label className="form-label">授權密碼 (Password)</label>
                <div className="form-input-wrapper">
                  <Key size={14} className="input-icon" />
                  <input required type="password" placeholder="••••••••" className="form-input"
                    value={form.smtp_password} onChange={e => setForm({ ...form, smtp_password: e.target.value })} />
                </div>
              </div>
              <div>
                <label className="form-label">顯示寄件人名稱</label>
                <input placeholder="Linkora Sales Team" className="form-input"
                  value={form.from_name} onChange={e => setForm({ ...form, from_name: e.target.value })} />
              </div>
              <div>
                <label className="form-label">預設回信 Email（選填）</label>
                <input type="email" placeholder="sales@yourcompany.com" className="form-input"
                  value={form.from_email} onChange={e => setForm({ ...form, from_email: e.target.value })} />
              </div>
            </div>
          </div>

          {/* Submit */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: 8 }}>
            <button type="submit" disabled={saving} className="btn-primary btn--lg">
              {saving
                ? <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />儲存中...</>
                : <><Save size={16} />儲存並啟用發信通道</>
              }
            </button>
          </div>
        </form>

        {/* Sidebar */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card" style={{ borderColor: 'rgba(91,127,255,0.2)', background: 'rgba(91,127,255,0.05)' }}>
            <div className="card__header">
              <h4 className="card__title">
                <AlertCircle size={15} style={{ color: 'var(--color-primary)' }} />
                發信指南
              </h4>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="card" style={{ padding: 12 }}>
                <strong style={{ color: 'var(--color-primary)', display: 'block', marginBottom: 4, fontSize: 12 }}>Google Gmail</strong>
                <p style={{ fontSize: 11, color: 'var(--color-text-muted)', lineHeight: 1.6, margin: 0 }}>
                  必須使用「網頁應用程式密碼」。請至 Google 帳戶 → 安全性 → 2 步驗證 → 應用程式密碼中產生。
                </p>
              </div>
              <div className="card" style={{ padding: 12 }}>
                <strong style={{ color: 'var(--color-accent-teal)', display: 'block', marginBottom: 4, fontSize: 12 }}>Outlook / O365</strong>
                <p style={{ fontSize: 11, color: 'var(--color-text-muted)', lineHeight: 1.6, margin: 0 }}>
                  主機: smtp.office365.com<br />埠號: 587 (TLS)
                </p>
              </div>
              <div className="page-banner page-banner--warning" style={{ margin: 0, padding: '10px 14px', fontSize: 11 }}>
                <Zap size={13} style={{ flexShrink: 0 }} />
                頻繁發送開發信建議配置專門的營收域名，以防主域名權重受損。
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card__header">
              <h4 className="card__title">
                <Mail size={15} />
                通道測試工具
              </h4>
            </div>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.6, marginBottom: 12 }}>
              系統將發送一封測試郵件至您的帳號，確保連線協議、TLS 握手及認證參數完全正確。
            </p>
            <button disabled className="btn-outline" style={{ width: '100%', opacity: 0.5, cursor: 'not-allowed', justifyContent: 'center' }}>
              通道測試即將推出
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default SmtpSettings;
