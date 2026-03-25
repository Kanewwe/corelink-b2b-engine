import React, { useState, useEffect } from 'react';
import { getAdminVendors, createAdminVendor, updateAdminVendor, deleteAdminVendor } from '../services/api';
import { UserPlus, Edit, Trash2, X, Save } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Vendor {
  id: number;
  user_id: number;
  email: string;
  company_name: string;
  contact_name: string;
  contact_phone: string;
  pricing_config: any;
  is_active: boolean;
  created_at: string;
}

const VendorAdmin: React.FC = () => {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null);
  
  // Form State
  const [form, setForm] = useState({
    email: '',
    password: '',
    company_name: '',
    contact_name: '',
    contact_phone: '',
    per_lead: 50,
  });

  const fetchVendors = async () => {
    setLoading(true);
    try {
      const resp = await getAdminVendors();
      if (resp.ok) {
        const data = await resp.json();
        setVendors(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        pricing_config: { per_lead: form.per_lead }
      };

      let resp;
      if (editingVendor) {
        resp = await updateAdminVendor(editingVendor.id, payload);
      } else {
        resp = await createAdminVendor(payload);
      }

      if (resp.ok) {
        setShowModal(false);
        setEditingVendor(null);
        setForm({ email: '', password: '', company_name: '', contact_name: '', contact_phone: '', per_lead: 50 });
        fetchVendors();
        toast.success(editingVendor ? '廠商資料已更新' : '廠商已建立');
      } else {
        const err = await resp.json();
        toast.error(err.detail || '操作失敗');
      }
    } catch {
      toast.error('網路錯誤');
    }
  };

  const handleEdit = (v: Vendor) => {
    setEditingVendor(v);
    setForm({
      email: v.email,
      password: '', 
      company_name: v.company_name,
      contact_name: v.contact_name,
      contact_phone: v.contact_phone,
      per_lead: v.pricing_config?.per_lead || 50
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('確定要刪除此委外廠商嗎？這將會停用該用戶帳號。')) return;
    try {
      const resp = await deleteAdminVendor(id);
      if (resp.ok) { fetchVendors(); toast.success('廠商已刪除'); }
    } catch { toast.error('刪除失敗'); }
  };

  return (
    <div className="page-wrapper">

      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <div className="page-header__title-row">
            <h1 className="page-title">
              廠商管理
              <span className="page-title__en">Vendor Management</span>
            </h1>
            <span className="version-badge">LINKORA V2</span>
          </div>
          <p className="page-subtitle">管理全國委外接案廠商、批發定價與帳務。</p>
        </div>
        <div className="page-header__right">
          <button
            onClick={() => { setEditingVendor(null); setForm({ email: '', password: '', company_name: '', contact_name: '', contact_phone: '', per_lead: 50 }); setShowModal(true); }}
            className="btn-primary"
          >
            <UserPlus size={15} />
            新增委外廠商
          </button>
        </div>
      </div>

      {/* ── Table ── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>廠商名稱 / ID</th>
                <th>聯絡人</th>
                <th>帳號 (Email)</th>
                <th>批發單價</th>
                <th>狀態</th>
                <th style={{ textAlign: 'right' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr className="empty-row"><td colSpan={6}>載入中...</td></tr>
              ) : vendors.length === 0 ? (
                <tr><td colSpan={6}>
                  <div className="empty-state">
                    <div className="empty-state__icon">🏭</div>
                    <p className="empty-state__title">尚無廠商資料</p>
                    <p className="empty-state__desc">點擊右上角「新增委外廠商」開始建立合作關係</p>
                  </div>
                </td></tr>
              ) : vendors.map(v => (
                <tr key={v.id} className="group">
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{v.company_name}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>#{v.id}</div>
                  </td>
                  <td>
                    <div>{v.contact_name}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{v.contact_phone}</div>
                  </td>
                  <td style={{ fontFamily: 'monospace', color: 'var(--color-primary)', fontSize: 13 }}>{v.email}</td>
                  <td>
                    <span className="badge badge--neutral">${v.pricing_config?.per_lead || 50} / lead</span>
                  </td>
                  <td>
                    {v.is_active
                      ? <span className="badge badge--success">合作中</span>
                      : <span className="badge badge--danger">已終止</span>
                    }
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
                      <button onClick={() => handleEdit(v)} className="btn-icon-sm" title="編輯"><Edit size={14} /></button>
                      <button onClick={() => handleDelete(v.id)} className="btn-icon-sm danger" title="刪除"><Trash2 size={14} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Modal ── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setShowModal(false)}>
          <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 16, width: '100%', maxWidth: 520, boxShadow: 'var(--shadow-modal)' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px', borderBottom: '1px solid var(--color-border-light)' }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                {editingVendor ? '編輯廠商資料' : '新增委外廠商'}
              </h3>
              <button onClick={() => setShowModal(false)} className="btn-icon-sm"><X size={16} /></button>
            </div>

            <form onSubmit={handleSubmit} style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label className="form-label">廠商/公司名稱</label>
                  <input required value={form.company_name} onChange={e => setForm({ ...form, company_name: e.target.value })} placeholder="廠商名稱" className="form-input" />
                </div>
                <div>
                  <label className="form-label">窗口姓名</label>
                  <input value={form.contact_name} onChange={e => setForm({ ...form, contact_name: e.target.value })} placeholder="王小明" className="form-input" />
                </div>
              </div>

              <div>
                <label className="form-label">登入帳號 (Email)</label>
                <input required type="email" disabled={!!editingVendor} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="form-input" style={editingVendor ? { opacity: 0.5 } : {}} />
              </div>

              {!editingVendor && (
                <div>
                  <label className="form-label">初始密碼</label>
                  <input required type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} className="form-input" />
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label className="form-label">聯絡電話</label>
                  <input value={form.contact_phone} onChange={e => setForm({ ...form, contact_phone: e.target.value })} className="form-input" />
                </div>
                <div>
                  <label className="form-label">批發單價 (TWD)</label>
                  <input type="number" value={form.per_lead} onChange={e => setForm({ ...form, per_lead: parseInt(e.target.value) })} className="form-input" />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, paddingTop: 8 }}>
                <button type="button" onClick={() => setShowModal(false)} className="btn-outline" style={{ flex: 1, justifyContent: 'center' }}>取消</button>
                <button type="submit" className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
                  <Save size={14} />{editingVendor ? '儲存變更' : '確認建立'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default VendorAdmin;
