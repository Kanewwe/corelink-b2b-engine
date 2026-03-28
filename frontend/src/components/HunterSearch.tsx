// Hunter Search Component (v3.7.30)
// Hunter.io Email 搜尋組件

import React, { useState } from 'react';
import { Search, Mail, Check, AlertCircle, Loader } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface HunterEmail {
  email: string;
  type: string;
  first_name: string;
  last_name: string;
  position: string;
  department: string;
  seniority: string;
  confidence: number;
  verified: boolean;
  linkedin: string;
}

interface HunterSearchProps {
  onSave?: (emails: HunterEmail[]) => void;
}

export const HunterSearch: React.FC<HunterSearchProps> = ({ onSave }) => {
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<HunterEmail[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [total, setTotal] = useState(0);

  const searchDomain = async () => {
    if (!domain) {
      toast.error('請輸入網域');
      return;
    }

    setLoading(true);
    setResults([]);
    setSelected([]);

    try {
      const resp = await fetch('/api/scrape/hunter/domain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ domain, limit: 20 })
      });

      const data = await resp.json();

      if (!resp.ok) {
        toast.error(data.detail || '搜尋失敗');
        return;
      }

      setResults(data.emails || []);
      setTotal(data.total || 0);
      toast.success(`找到 ${data.total} 個 Email`);

    } catch (e) {
      toast.error('連線錯誤');
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (email: string) => {
    setSelected(prev =>
      prev.includes(email)
        ? prev.filter(e => e !== email)
        : [...prev, email]
    );
  };

  const selectAll = () => {
    if (selected.length === results.length) {
      setSelected([]);
    } else {
      setSelected(results.map(r => r.email));
    }
  };

  const saveSelected = async () => {
    if (selected.length === 0) {
      toast.error('請選擇要儲存的 Email');
      return;
    }

    const leadsToSave = results
      .filter(r => selected.includes(r.email))
      .map(r => ({
        company_name: domain.split('.')[0].toUpperCase(),
        domain: domain,
        contact_email: r.email,
        contact_person: `${r.first_name} ${r.last_name}`.trim(),
        contact_position: r.position,
        email_verified: r.verified,
        email_confidence: r.confidence
      }));

    try {
      const resp = await fetch('/api/scrape/save-to-global', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          leads: leadsToSave,
          source: 'hunter',
          source_mode: 'manufacturer'
        })
      });

      const data = await resp.json();

      if (!resp.ok) {
        toast.error(data.detail || '儲存失敗');
        return;
      }

      toast.success(`已儲存 ${data.saved} 筆到全域庫`);
      onSave?.(results.filter(r => selected.includes(r.email)));

    } catch (e) {
      toast.error('儲存失敗');
    }
  };

  return (
    <div className="hunter-search" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Search Input */}
      <div style={{ display: 'flex', gap: 8 }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Mail 
            size={16} 
            style={{ 
              position: 'absolute', 
              left: 12, 
              top: '50%', 
              transform: 'translateY(-50%)',
              color: 'var(--color-text-muted)'
            }} 
          />
          <input
            type="text"
            className="form-input"
            style={{ paddingLeft: 36 }}
            placeholder="輸入公司網域 (例: company.com)"
            value={domain}
            onChange={e => setDomain(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && searchDomain()}
          />
        </div>
        <button 
          onClick={searchDomain} 
          disabled={loading}
          className="btn-primary"
        >
          {loading ? <Loader size={16} className="animate-spin" /> : <Search size={16} />}
          搜尋
        </button>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <>
          {/* Header */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            padding: '8px 16px',
            background: 'var(--color-neutral-glow)',
            borderRadius: 8
          }}>
            <div style={{ fontSize: 13 }}>
              找到 <strong>{total}</strong> 個 Email，已選取 <strong>{selected.length}</strong> 個
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={selectAll} className="btn-outline" style={{ fontSize: 12, padding: '4px 12px' }}>
                {selected.length === results.length ? '取消全選' : '全選'}
              </button>
              <button 
                onClick={saveSelected} 
                disabled={selected.length === 0}
                className="btn-primary"
                style={{ fontSize: 12, padding: '4px 12px' }}
              >
                儲存選取
              </button>
            </div>
          </div>

          {/* Email List */}
          <div style={{ 
            border: '1px solid var(--color-neutral-glow)', 
            borderRadius: 12,
            maxHeight: 400,
            overflowY: 'auto'
          }}>
            <table className="leads-table">
              <thead>
                <tr>
                  <th style={{ width: 40 }}></th>
                  <th>Email</th>
                  <th>姓名</th>
                  <th>職位</th>
                  <th>信心度</th>
                  <th>驗證</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, idx) => (
                  <tr 
                    key={idx}
                    onClick={() => toggleSelect(r.email)}
                    style={{ 
                      cursor: 'pointer',
                      background: selected.includes(r.email) ? 'var(--color-primary-glow)' : 'transparent'
                    }}
                  >
                    <td>
                      <input 
                        type="checkbox" 
                        checked={selected.includes(r.email)}
                        onChange={() => toggleSelect(r.email)}
                      />
                    </td>
                    <td className="font-medium">{r.email}</td>
                    <td>{r.first_name} {r.last_name}</td>
                    <td style={{ fontSize: 12 }}>{r.position}</td>
                    <td>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 4 
                      }}>
                        <div style={{ 
                          flex: 1, 
                          height: 4, 
                          background: 'var(--color-neutral-glow)',
                          borderRadius: 2,
                          overflow: 'hidden'
                        }}>
                          <div style={{ 
                            width: `${r.confidence}%`, 
                            height: '100%',
                            background: r.confidence >= 80 ? '#10b981' : r.confidence >= 50 ? '#f59e0b' : '#ef4444'
                          }} />
                        </div>
                        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                          {r.confidence}%
                        </span>
                      </div>
                    </td>
                    <td>
                      {r.verified ? (
                        <span style={{ 
                          color: '#10b981', 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: 4 
                        }}>
                          <Check size={14} /> 已驗證
                        </span>
                      ) : (
                        <span style={{ 
                          color: 'var(--color-text-muted)', 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: 4 
                        }}>
                          <AlertCircle size={14} /> 未驗證
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Empty State */}
      {!loading && results.length === 0 && domain && (
        <div style={{ 
          textAlign: 'center', 
          padding: 40, 
          color: 'var(--color-text-muted)' 
        }}>
          <Mail size={32} style={{ marginBottom: 8, opacity: 0.5 }} />
          <div>輸入網域後點擊搜尋</div>
        </div>
      )}
    </div>
  );
};

export default HunterSearch;
