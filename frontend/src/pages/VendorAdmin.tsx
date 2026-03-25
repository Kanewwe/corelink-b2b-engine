import React, { useState, useEffect } from 'react';
import { getAdminVendors, createAdminVendor, updateAdminVendor, deleteAdminVendor } from '../services/api';
import { UserPlus, Edit, Trash2, Building2, X, Save } from 'lucide-react';

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
      } else {
        const err = await resp.json();
        alert(err.detail || "操作失敗");
      }
    } catch (e) {
      alert("網路錯誤");
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
    if (!confirm("確定要刪除此委外廠商嗎？這將會停用該用戶帳號。")) return;
    try {
      const resp = await deleteAdminVendor(id);
      if (resp.ok) fetchVendors();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col h-full gap-6">
      <header className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Building2 className="w-7 h-7 text-primary" />
            委外廠商 (Vendor) 管理中心
          </h2>
          <p className="text-text-muted text-sm mt-1">管理全國委外接案廠商、批發定價與帳務</p>
        </div>
        <button 
          onClick={() => { setEditingVendor(null); setForm({ email: '', password: '', company_name: '', contact_name: '', contact_phone: '', per_lead: 50 }); setShowModal(true); }}
          className="flex items-center gap-2 bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg transition-all shadow-lg shadow-primary/20"
        >
          <UserPlus className="w-5 h-5" />
          新增委外廠商
        </button>
      </header>

      <section className="glass-panel overflow-hidden border border-white/10">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 text-text-muted text-sm uppercase tracking-wider">
                <th className="px-6 py-4 font-semibold">廠商名稱 / ID</th>
                <th className="px-6 py-4 font-semibold">聯絡人</th>
                <th className="px-6 py-4 font-semibold">帳號 (Email)</th>
                <th className="px-6 py-4 font-semibold">批發單價</th>
                <th className="px-6 py-4 font-semibold">狀態</th>
                <th className="px-6 py-4 font-semibold text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-text-muted">載入中...</td>
                </tr>
              ) : vendors.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-text-muted">尚無廠商資料</td>
                </tr>
              ) : (
                vendors.map(v => (
                  <tr key={v.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4">
                      <div className="font-medium text-white">{v.company_name}</div>
                      <div className="text-xs text-text-muted">#{v.id}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">{v.contact_name}</div>
                      <div className="text-xs text-text-muted">{v.contact_phone}</div>
                    </td>
                    <td className="px-6 py-4 text-sm font-mono text-primary-light">{v.email}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className="bg-white/10 px-2 py-1 rounded text-xs">
                        ${v.pricing_config?.per_lead || 50} / lead
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {v.is_active ? (
                        <span className="flex items-center gap-1.5 text-xs text-green-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                          合作中
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-xs text-red-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                          已終止
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => handleEdit(v)} className="p-2 hover:bg-white/10 rounded-lg text-blue-400 transition-colors">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button onClick={() => handleDelete(v.id)} className="p-2 hover:bg-white/10 rounded-lg text-red-400 transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-lg shadow-2xl border border-white/20 animate-in fade-in zoom-in duration-200">
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
              <h3 className="text-xl font-bold flex items-center gap-2">
                {editingVendor ? '編輯廠商資料' : '新增委外廠商'}
              </h3>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-text-muted ml-1">廠商/公司名稱</label>
                  <input 
                    required
                    value={form.company_name}
                    onChange={e => setForm({...form, company_name: e.target.value})}
                    placeholder="廠商名稱"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:border-primary outline-none transition-all"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-text-muted ml-1">窗口姓名</label>
                  <input 
                    value={form.contact_name}
                    onChange={e => setForm({...form, contact_name: e.target.value})}
                    placeholder="王小明"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:border-primary outline-none transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-text-muted ml-1">登入帳號 (Email)</label>
                <input 
                  required
                  type="email"
                  disabled={!!editingVendor}
                  value={form.email}
                  onChange={e => setForm({...form, email: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:border-primary outline-none transition-all disabled:opacity-50"
                />
              </div>

              {!editingVendor && (
                <div className="space-y-1">
                  <label className="text-xs text-text-muted ml-1">初始密碼</label>
                  <input 
                    required
                    type="password"
                    value={form.password}
                    onChange={e => setForm({...form, password: e.target.value})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:border-primary outline-none transition-all"
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-text-muted ml-1">聯絡電話</label>
                  <input 
                    value={form.contact_phone}
                    onChange={e => setForm({...form, contact_phone: e.target.value})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:border-primary outline-none transition-all"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-text-muted ml-1">批發單價 (TWD)</label>
                  <input 
                    type="number"
                    value={form.per_lead}
                    onChange={e => setForm({...form, per_lead: parseInt(e.target.value)})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 focus:border-primary outline-none transition-all"
                  />
                </div>
              </div>

              <div className="pt-4 flex gap-3">
                <button 
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-white/10 rounded-lg hover:bg-white/5 transition-all text-sm"
                >
                  取消
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2 text-sm font-bold"
                >
                  <Save className="w-4 h-4" />
                  {editingVendor ? '儲存變更' : '確認建立'}
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
