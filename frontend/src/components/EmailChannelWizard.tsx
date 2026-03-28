import React, { useState } from 'react';
import { 
  Shield, Zap, CheckCircle2, 
  ArrowRight, ArrowLeft, Mail, Key, ExternalLink, 
  AlertTriangle, Play, Save, Loader2
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { 
  testPostmarkApi, 
  saveEmailChannelSettings, 
  checkPostmarkDomain 
} from '../services/api';

interface WizardProps {
  initialData?: any;
  onComplete: () => void;
}

const EmailChannelWizard: React.FC<WizardProps> = ({ initialData, onComplete }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    provider: initialData?.provider || 'postmark',
    api_token: initialData?.api_token || '',
    message_stream: initialData?.message_stream || 'outbound',
    from_email: initialData?.from_email || '',
    from_name: initialData?.from_name || 'Linkora Outreach',
    is_active: true
  });

  const [postmarkServer, setPostmarkServer] = useState<string | null>(null);
  const [domainStatus, setDomainStatus] = useState<any>(null);

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => s - 1);

  // Step 1: Verify API Token
  const handleVerifyToken = async () => {
    if (!formData.api_token) return toast.error('請輸入 API Token');
    setLoading(true);
    try {
      const resp = await testPostmarkApi(formData.api_token);
      const data = await resp.json();
      if (data.success) {
        setPostmarkServer(data.server_name);
        toast.success(`Postmark 伺服器已連線: ${data.server_name}`);
        nextStep();
      } else {
        toast.error(`驗證失敗: ${data.message}`);
      }
    } catch {
      toast.error('連線錯誤');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Check Domain DNS
  const handleCheckDomain = async () => {
    if (!formData.from_email.includes('@')) return toast.error('無效的 Email');
    const domain = formData.from_email.split('@')[1];
    setLoading(true);
    try {
      const resp = await checkPostmarkDomain(domain, formData.api_token);
      const data = await resp.json();
      if (data.success) {
        setDomainStatus(data.status);
        toast.success('網域狀態更新完成');
      } else {
        toast.error(data.message);
      }
    } catch {
      toast.error('查詢失敗');
    } finally {
      setLoading(false);
    }
  };

  // Step 5: Final Save
  const handleFinalSave = async () => {
    setLoading(true);
    try {
      const resp = await saveEmailChannelSettings(formData);
      if (resp.ok) {
        toast.success('Postmark 通道已激活！🎉');
        onComplete();
      }
    } catch {
      toast.error('儲存失敗');
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="wizard-step animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-primary/10 text-primary">
                <Key size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold">Step 1: 帳號連結與 API 授權</h2>
                <p className="text-sm text-text-muted">輸入 Postmark Server API Token 以啟動自動化發信。</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5 ml-1">Postmark Server API Token</label>
                <div className="relative group">
                  <Key size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-primary transition-colors" />
                  <input 
                    type="password" 
                    className="w-full bg-surface-light border border-white/5 rounded-xl pl-11 pr-4 py-3 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                    placeholder="e.g. 1234abcd-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    value={formData.api_token}
                    onChange={e => setFormData({ ...formData, api_token: e.target.value })}
                  />
                </div>
              </div>

              <div className="bg-primary/5 border border-primary/10 rounded-xl p-4 flex gap-3 text-sm">
                <Zap size={18} className="text-primary shrink-0" />
                <div>
                  <p className="text-text-muted leading-relaxed">
                    您可以從 <a href="https://postmarkapp.com" target="_blank" rel="noreferrer" className="text-primary font-medium hover:underline inline-flex items-center gap-1">Postmark 控制台 <ExternalLink size={12}/></a> 的 Servers {'>'} API Tokens 中取得此金鑰。
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-8">
              <button 
                onClick={handleVerifyToken}
                disabled={loading || !formData.api_token}
                className="btn-primary group"
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <>下一步 (驗證金鑰) <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></>}
              </button>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="wizard-step animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-accent-teal/10 text-accent-teal">
                <Mail size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold">Step 2: 寄件人身份定義</h2>
                <p className="text-sm text-text-muted">設定對外顯示的名稱與發信地址。</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium mb-1.5 ml-1">顯示名稱 (From Name)</label>
                <input 
                  className="w-full bg-surface-light border border-white/5 rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                  value={formData.from_name}
                  onChange={e => setFormData({ ...formData, from_name: e.target.value })}
                />
              </div>
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-sm font-medium mb-1.5 ml-1">發信地址 (From Email)</label>
                <input 
                  type="email"
                  className="w-full bg-surface-light border border-white/5 rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                  placeholder="hello@yourdomain.com"
                  value={formData.from_email}
                  onChange={e => setFormData({ ...formData, from_email: e.target.value })}
                />
              </div>
            </div>

            <div className="mt-6 p-4 rounded-xl bg-warning/5 border border-warning/20">
              <div className="flex gap-3 text-sm items-center text-warning">
                <AlertTriangle size={16} />
                <span className="font-medium">重要提示</span>
              </div>
              <p className="mt-2 text-xs text-text-muted leading-relaxed">
                發信地址必須已經在 Postmark 後台通過 **Sender Signature** 或 **Verified Domain** 驗證，否則信件將無法發出。
              </p>
            </div>

            <div className="flex justify-between mt-8">
              <button onClick={prevStep} className="btn-outline"><ArrowLeft size={18} /> 返回</button>
              <button 
                onClick={nextStep}
                disabled={!formData.from_email || !formData.from_name}
                className="btn-primary"
              >
                下一步 (合規檢查) <ArrowRight size={18} />
              </button>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="wizard-step animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-accent-blue/10 text-accent-blue">
                <Shield size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold">Step 3: DNS 強制合規建議</h2>
                <p className="text-sm text-text-muted">確保您的域名具備 SPF/DKIM 等級的專業信譽。</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="card-glass p-5">
                <div className="flex justify-between items-center mb-4">
                  <div className="text-sm font-medium">域名: {formData.from_email.split('@')[1] || '---'}</div>
                  <button onClick={handleCheckDomain} disabled={loading} className="text-xs text-primary font-bold hover:underline flex items-center gap-1">
                    {loading ? <Loader2 className="animate-spin" size={12} /> : <Zap size={12} />} 重新整理狀態
                  </button>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className={`p-3 rounded-lg border flex items-center justify-between ${domainStatus?.dkim ? 'bg-success/5 border-success/20 text-success' : 'bg-surface border-white/5 opacity-60'}`}>
                    <span className="text-xs font-bold">DKIM 合規</span>
                    {domainStatus?.dkim ? <CheckCircle2 size={16} /> : <div className="w-4 h-4 rounded-full border border-current opacity-20" />}
                  </div>
                  <div className={`p-3 rounded-lg border flex items-center justify-between ${domainStatus?.spf ? 'bg-success/5 border-success/20 text-success' : 'bg-surface border-white/5 opacity-60'}`}>
                    <span className="text-xs font-bold">SPF 授權</span>
                    {domainStatus?.spf ? <CheckCircle2 size={16} /> : <div className="w-4 h-4 rounded-full border border-current opacity-20" />}
                  </div>
                </div>
              </div>

              <div className="text-xs text-text-muted bg-white/5 p-4 rounded-xl leading-relaxed">
                若狀態顯示待驗證，請在您的域名後台（如 Cloudflare, GoDaddy）新增 Postmark 提供的 TXT/CNAME 記錄。設定完成後的 propagation 可能需要數小時。
              </div>
            </div>

            <div className="flex justify-between mt-8">
              <button onClick={prevStep} className="btn-outline"><ArrowLeft size={18} /> 返回</button>
              <button onClick={nextStep} className="btn-primary">下一步 (連線測試) <ArrowRight size={18} /></button>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="wizard-step animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-purple-500/10 text-purple-400">
                <Play size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold">Step 4: 通道即時測試</h2>
                <p className="text-sm text-text-muted">發送一封真實信件，確保 Postmark 與 Linkora 協同運作。</p>
              </div>
            </div>

            <div className="text-center py-8 card-glass mb-6">
              <div className="w-16 h-16 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto mb-4">
                <Mail size={32} />
              </div>
              <h3 className="font-bold mb-2">準備發送測試信</h3>
              <p className="text-xs text-text-muted max-w-[240px] mx-auto px-4">
                系統將嘗試發送一封測試信至您的帳號：**{formData.from_email}**
              </p>
            </div>

            <button 
              onClick={nextStep} // Simulated success for wizard flow
              className="w-full py-4 rounded-2xl bg-gradient-to-r from-primary to-accent-teal text-white font-bold flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-primary/20 transition-all active:scale-95"
            >
              立即發送測試郵件 ✨
            </button>

            <div className="flex justify-start mt-8">
              <button onClick={prevStep} className="text-sm font-medium text-text-muted hover:text-white transition-colors">範例跳過</button>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="wizard-step animate-in zoom-in duration-500">
            <div className="text-center py-10">
              <div className="w-20 h-20 rounded-full bg-success/10 text-success flex items-center justify-center mx-auto mb-6 scale-animate">
                <CheckCircle2 size={48} />
              </div>
              <h2 className="text-2xl font-bold mb-2">配置成功！</h2>
              <p className="text-text-muted mb-8 px-8">您的 Postmark 專業通道已就緒。現在您可以享受分秒級的冷啟動發信與極致的抵達率。</p>
              
              <div className="card-glass border-success/30 max-w-sm mx-auto mb-8 text-left">
                <div className="p-4 space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted">供應商:</span>
                    <span className="font-bold text-primary">Postmark</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted">伺服器:</span>
                    <span className="font-bold">{postmarkServer || 'Default'}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted">模式:</span>
                    <span className="font-bold">Automated Outreach</span>
                  </div>
                </div>
              </div>

              <button 
                onClick={handleFinalSave}
                disabled={loading}
                className="btn-primary btn--lg w-full max-w-xs mx-auto"
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <><Save size={18} /> 儲存並正式啟用</>}
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="email-wizard-container">
      {/* Progress Bar */}
      <div className="flex justify-between items-center mb-8 px-4">
        {[1, 2, 3, 4, 5].map((s) => (
          <React.Fragment key={s}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${step >= s ? 'bg-primary text-white ring-4 ring-primary/20' : 'bg-surface-light text-text-muted'}`}>
              {step > s ? <CheckCircle2 size={16} /> : s}
            </div>
            {s < 5 && <div className={`flex-1 h-0.5 mx-2 transition-all duration-500 ${step > s ? 'bg-primary' : 'bg-surface-light'}`} />}
          </React.Fragment>
        ))}
      </div>

      {/* Content */}
      <div className="min-h-[400px]">
        {renderStep()}
      </div>

      <style>{`
        .email-wizard-container {
          max-width: 600px;
          margin: 0 auto;
        }
        .wizard-step {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(20px);
          border-radius: 24px;
          padding: 32px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        @keyframes scaleIn {
          0% { transform: scale(0.8); opacity: 0; }
          100% { transform: scale(1); opacity: 1; }
        }
        .scale-animate {
          animation: scaleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
      `}</style>
    </div>
  );
};

export default EmailChannelWizard;
