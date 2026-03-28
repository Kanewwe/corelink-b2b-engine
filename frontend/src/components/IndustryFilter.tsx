// Industry Filter Component (v3.7.30)
// 行業篩選器組件

import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, Factory, Cpu, ShoppingCart, Building2, DollarSign, Heart, HardHat, Truck, Zap, Leaf, X } from 'lucide-react';

interface IndustryTag {
  id: number;
  code: string;
  parent_code: string | null;
  name_en: string;
  name_zh: string;
  name_short: string;
  level: number;
  keywords: string;
  company_count: number;
  icon: string;
  color: string;
  children?: IndustryTag[];
}

interface IndustryFilterProps {
  selectedCodes: string[];
  onChange: (codes: string[]) => void;
  singleSelect?: boolean;
}

const INDUSTRY_ICONS: Record<string, React.ReactNode> = {
  'MFG': <Factory size={16} />,
  'TECH': <Cpu size={16} />,
  'RETAIL': <ShoppingCart size={16} />,
  'SERVICE': <Building2 size={16} />,
  'FINANCE': <DollarSign size={16} />,
  'HEALTH': <Heart size={16} />,
  'CONSTRUCTION': <HardHat size={16} />,
  'TRANSPORT': <Truck size={16} />,
  'ENERGY': <Zap size={16} />,
  'AGRICULTURE': <Leaf size={16} />,
};

export const IndustryFilter: React.FC<IndustryFilterProps> = ({
  selectedCodes,
  onChange,
  singleSelect = false
}) => {
  const [industries, setIndustries] = useState<IndustryTag[]>([]);
  const [expanded, setExpanded] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIndustries();
  }, []);

  const fetchIndustries = async () => {
    try {
      const resp = await fetch('/api/industries/tree');
      if (resp.ok) {
        const data = await resp.json();
        setIndustries(data.tree || []);
      }
    } catch (e) {
      console.error('Failed to fetch industries:', e);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (code: string) => {
    setExpanded(prev => 
      prev.includes(code) 
        ? prev.filter(c => c !== code)
        : [...prev, code]
    );
  };

  const toggleSelect = (code: string) => {
    if (singleSelect) {
      onChange([code]);
    } else {
      onChange(
        selectedCodes.includes(code)
          ? selectedCodes.filter(c => c !== code)
          : [...selectedCodes, code]
      );
    }
  };

  const renderIndustry = (industry: IndustryTag, level: number = 0) => {
    const hasChildren = industry.children && industry.children.length > 0;
    const isExpanded = expanded.includes(industry.code);
    const isSelected = selectedCodes.includes(industry.code);

    return (
      <div key={industry.code} style={{ marginLeft: level * 16 }}>
        <div
          className={`industry-item ${isSelected ? 'selected' : ''}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            cursor: 'pointer',
            borderRadius: 8,
            background: isSelected ? 'var(--color-primary-glow)' : 'transparent',
            border: isSelected ? '1px solid var(--color-primary-border)' : '1px solid transparent',
            marginBottom: 4
          }}
          onClick={() => toggleSelect(industry.code)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpand(industry.code);
              }}
              style={{ padding: 2, background: 'none', border: 'none', cursor: 'pointer' }}
            >
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          )}
          {!hasChildren && <span style={{ width: 18 }} />}
          
          <span style={{ fontSize: 14 }}>
            {INDUSTRY_ICONS[industry.code] || industry.icon}
          </span>
          
          <span style={{ flex: 1, fontSize: 13 }}>
            {industry.name_zh}
          </span>
          
          <span style={{ 
            fontSize: 11, 
            color: 'var(--color-text-muted)',
            background: 'var(--color-neutral-glow)',
            padding: '2px 6px',
            borderRadius: 4
          }}>
            {industry.company_count || 0}
          </span>
        </div>
        
        {hasChildren && isExpanded && (
          <div>
            {industry.children!.map(child => renderIndustry(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div style={{ padding: 20, textAlign: 'center' }}>載入中...</div>;
  }

  return (
    <div className="industry-filter" style={{ maxHeight: 400, overflowY: 'auto' }}>
      {industries.map(industry => renderIndustry(industry))}
    </div>
  );
};


// 行業選擇器 Modal
interface IndustrySelectModalProps {
  open: boolean;
  onClose: () => void;
  onSelect: (industry: IndustryTag) => void;
}

export const IndustrySelectModal: React.FC<IndustrySelectModalProps> = ({
  open,
  onClose,
  onSelect
}) => {
  const [industries, setIndustries] = useState<IndustryTag[]>([]);
  const [selectedParent, setSelectedParent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (open) fetchIndustries();
  }, [open]);

  const fetchIndustries = async () => {
    try {
      const resp = await fetch('/api/industries/tree');
      if (resp.ok) {
        const data = await resp.json();
        setIndustries(data.tree || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div className="bg-slate-800 border border-white/10 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[80vh]">
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <h3 className="text-xl font-bold text-white">選擇行業</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg text-text-muted">
            <X size={20} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-12 text-text-muted">載入中...</div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {/* 一級行業 */}
              <div className="space-y-2">
                <h4 className="text-xs text-text-muted uppercase tracking-wider mb-2">一級行業</h4>
                {industries.map(ind => (
                  <button
                    key={ind.code}
                    onClick={() => setSelectedParent(ind.code)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedParent === ind.code 
                        ? 'bg-primary-glow border-primary-border' 
                        : 'bg-slate-700/50 border-transparent hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span>{INDUSTRY_ICONS[ind.code] || '🏢'}</span>
                      <span className="text-sm">{ind.name_zh}</span>
                      <span className="ml-auto text-xs text-text-muted">{ind.company_count || 0}</span>
                    </div>
                  </button>
                ))}
              </div>
              
              {/* 二級行業 */}
              <div className="space-y-2">
                <h4 className="text-xs text-text-muted uppercase tracking-wider mb-2">二級行業</h4>
                {selectedParent ? (
                  industries
                    .find(i => i.code === selectedParent)
                    ?.children?.map(child => (
                      <button
                        key={child.code}
                        onClick={() => onSelect(child)}
                        className="w-full text-left p-3 rounded-lg border border-transparent hover:border-primary-border bg-slate-700/50 transition-all"
                      >
                        <span className="text-sm">{child.name_zh}</span>
                        <span className="ml-2 text-xs text-text-muted">({child.company_count || 0})</span>
                      </button>
                    ))
                ) : (
                  <div className="text-text-muted text-sm italic p-4">
                    請先選擇一級行業
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IndustryFilter;
