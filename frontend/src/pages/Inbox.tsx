import React, { useState, useEffect } from 'react';
import { Mail, Inbox as InboxIcon, MessageSquare, Trash2, Clock, Copy, Edit3, RefreshCw } from 'lucide-react';
import { getInboundEmails, getInboundDetail, archiveInboundEmail } from '../services/api';
import toast from 'react-hot-toast';

const Inbox: React.FC = () => {
  const [emails, setEmails] = useState<any[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => { fetchEmails(); }, []);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      const res = await getInboundEmails();
      const data = await res.json();
      setEmails(data);
      if (data.length > 0 && !selectedEmail) {
        handleSelectEmail(data[0].id);
      }
    } catch (err) {
      toast.error('無法讀取收件匣');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEmail = async (id: number) => {
    try {
      setDetailLoading(true);
      const res = await getInboundDetail(id);
      const data = await res.json();
      setSelectedEmail(data);
      // 更新列表中的狀態為 read
      setEmails(prev => prev.map(e => e.id === id ? { ...e, status: 'read' } : e));
    } catch (err) {
      toast.error('讀取郵件詳情失敗');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleArchive = async (id: number) => {
    try {
      await archiveInboundEmail(id);
      toast.success('郵件已存檔');
      setEmails(prev => prev.filter(e => e.id !== id));
      if (selectedEmail?.id === id) {
        setSelectedEmail(null);
      }
      fetchEmails();
    } catch (err) {
      toast.error('存檔失敗');
    }
  };

  const getIntentBadge = (intent: string) => {
    switch (intent) {
      case 'positive': return <span className="badge badge--success">🤝 有興趣 / Positive</span>;
      case 'needs_info': return <span className="badge badge--primary">ℹ️ 詢問資訊 / Info</span>;
      case 'follow_up': return <span className="badge badge--warning">🕒 需要跟進 / Follow-up</span>;
      case 'declined': return <span className="badge badge--outline">❌ 婉拒 / Declined</span>;
      default: return <span className="badge badge--secondary">❓ 待分析 / Unknown</span>;
    }
  };

  return (
    <div className="page-container h-[calc(100vh-120px)] flex flex-col animate-fade-in">
      <div className="page-header shrink-0">
        <div className="page-header__left">
          <h1 className="page-title">
            AI 智慧收件匣
            <span className="page-title__en">Managed Reply Bench</span>
          </h1>
          <p className="page-subtitle">自動捕捉回信意圖，並為您產生最佳回饋草稿 (Sprint 3.3)</p>
        </div>
        <div className="page-header__right">
          <div className="flex gap-2 items-center">
            {loading && <RefreshCw size={14} className="animate-spin text-primary" />}
            <span className="text-xs text-text-muted mt-1 mr-2 flex items-center gap-1">
              <Clock size={12} /> 最後同步: {new Date().toLocaleTimeString()}
            </span>
            <button onClick={fetchEmails} className="btn-icon">
              <RefreshCw size={16} />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex gap-6 overflow-hidden min-h-0">
        {/* ── 列表區域 ── */}
        <div className="w-[350px] shrink-0 card !p-0 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-glass-border flex justify-between items-center">
            <span className="text-xs font-bold text-text-muted uppercase">所有訊息 ({emails.length})</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            {emails.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-text-muted opacity-50 p-6">
                <InboxIcon size={48} className="mb-4" />
                <p className="text-sm font-medium">尚無回信內容</p>
                <p className="text-[10px]">開發信發出後，回信將自動顯示於此</p>
              </div>
            ) : (
              emails.map((email) => (
                <div
                  key={email.id}
                  onClick={() => handleSelectEmail(email.id)}
                  className={`p-4 border-b border-white/[0.03] cursor-pointer transition-all hover:bg-white/[0.05] ${
                    selectedEmail?.id === email.id ? 'bg-primary/10 border-l-4 border-l-primary' : ''
                  }`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className={`text-sm font-bold ${email.status === 'unread' ? 'text-white' : 'text-text-muted'}`}>
                      {email.from_name || email.from_email}
                    </span>
                    <span className="text-[10px] text-text-muted">{new Date(email.received_at).toLocaleDateString()}</span>
                  </div>
                  <div className="text-xs text-text-muted truncate mb-2">{email.subject}</div>
                  <div className="mt-1">{getIntentBadge(email.reply_intent)}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ── 內容區域 ── */}
        <div className="flex-1 card p-0 flex flex-col overflow-hidden">
          {!selectedEmail ? (
            <div className="flex-1 flex flex-col items-center justify-center text-text-muted opacity-40">
              <Mail size={64} className="mb-4" />
              <p>請從左側選擇一封郵件來查看 AI 回覆建議</p>
            </div>
          ) : (
            <>
              <div className="p-6 border-b border-glass-border flex justify-between items-start shrink-0">
                <div>
                  <h2 className="text-xl font-bold text-white mb-2">{selectedEmail.subject}</h2>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="text-primary font-medium">{selectedEmail.from_name || selectedEmail.from_email}</span>
                    <span className="text-text-muted">&lt;{selectedEmail.from_email}&gt;</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleArchive(selectedEmail.id)} className="btn-icon text-text-muted hover:text-danger">
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
                {detailLoading ? (
                  <div className="flex flex-col items-center justify-center h-full text-primary/40">
                    <RefreshCw size={48} className="animate-spin mb-4" />
                    <p className="text-sm font-medium">正在讀取郵件內容與 AI 分析...</p>
                  </div>
                ) : (
                  <>
                    {/* 原始內容 */}
                    <div className="mb-8">
                      <div className="flex items-center gap-2 text-xs text-text-muted mb-4">
                        <div className="w-6 h-px bg-white/10" />
                        <span>Lead 回信內容 / Customer Reply</span>
                        <div className="flex-1 h-px bg-white/10" />
                      </div>
                      <div className="bg-white/[0.03] p-6 rounded-2xl border border-white/[0.05] whitespace-pre-wrap text-sm leading-relaxed text-text-main shadow-inner">
                        {selectedEmail.body_text || '(無內文)'}
                      </div>
                    </div>

                    {/* AI 助手建議 */}
                    <div className="animate-slide-up">
                      <div className="flex items-center gap-2 text-xs text-primary mb-4 font-bold tracking-widest">
                        <div className="w-10 h-px bg-primary/30" />
                        <span className="flex items-center gap-2">
                          <MessageSquare size={14} /> AI 智慧回覆建議 / Reply Assistant
                        </span>
                        <div className="flex-1 h-px bg-primary/30" />
                      </div>
                      
                      <div className="bg-gradient-to-br from-primary/10 to-accent/10 p-8 rounded-3xl border border-primary/20 shadow-xl relative group">
                        <div className="absolute -top-4 -right-4 bg-primary text-bg-dark text-[10px] font-black py-1 px-3 rounded-full shadow-lg">
                          AI RECOMENDED
                        </div>
                        
                        <div className="flex items-center gap-2 mb-6 text-sm font-bold text-white">
                          💡 建議語氣: 
                          <span className="text-primary uppercase tracking-tighter">
                            {selectedEmail.reply_intent === 'positive' ? 'Professional & Warm' : 'Polite & Follow-up'}
                          </span>
                        </div>

                        <div className="bg-bg-dark/60 p-6 rounded-2xl border border-white/5 text-sm leading-relaxed text-text-main font-mono whitespace-pre-wrap">
                          {selectedEmail.ai_draft_suggested || 'AI 正在分析最佳回覆策略...'}
                        </div>

                        <div className="mt-6 flex gap-4">
                          <button 
                            onClick={() => {
                              navigator.clipboard.writeText(selectedEmail.ai_draft_suggested);
                              toast.success('草稿已複製到剪貼簿');
                            }}
                            className="btn-primary flex-1 flex items-center justify-center gap-2"
                          >
                            <Copy size={16} /> 複製草稿內容
                          </button>
                          <button className="btn-outline flex-1 flex items-center justify-center gap-2">
                            <Edit3 size={16} /> 進入編輯並回覆
                          </button>
                        </div>
                      </div>
                      
                      <div className="mt-6 p-4 bg-white/[0.02] rounded-2xl border border-white/[0.05]">
                        <div className="flex items-start gap-3">
                          <Clock size={16} className="text-text-muted mt-1" />
                          <div>
                            <h4 className="text-xs font-bold text-white mb-1">AI 決策建議</h4>
                            <p className="text-[10px] text-text-muted leading-relaxed">
                              根據客戶的意圖「{selectedEmail.reply_intent}」，建議在 24 小時內完成回覆。此草稿已考量 Corelink 的 B2B 產品線優勢與台灣供應鏈整合能力。
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Inbox;
