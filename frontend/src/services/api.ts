// 1. 優先取用環境變數 (Build-time)
const envUrl = import.meta.env.VITE_API_BASE_URL;

// 2. 執行期 Hostname 自動導航 (Run-time 雙重保險)
export const API_BASE_URL = envUrl || (
  window.location.hostname.includes('localhost') || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000/api' :
  window.location.hostname.includes('linkora-frontend-uat') 
    ? 'https://linkora-backend-uat.onrender.com/api' :
  window.location.hostname.includes('linkora-frontend') 
    ? 'https://linkora-backend.onrender.com/api' :
  '/api' // 最後的相對路徑回退
);

// v3.7 Security Secret (應與後端一致)
export const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('token');
  const headers: any = {
    'Content-Type': 'application/json',
  };
  
  if (token && token !== 'undefined' && token !== 'null') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

export const fetchWithAuth = async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
  const headers: any = getAuthHeaders();
  
  if (options.headers) {
    Object.assign(headers, options.headers);
  }

  // v3.7: HMAC 安全簽名核查 (於 v3.7.12 停用，回歸標準 Auth 模型)
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    // Implement token expiration logout logic here later (e.g., dispatch auth clear)
    localStorage.removeItem('token');
    window.dispatchEvent(new Event('auth-unauthorized'));
  }

  return response;
};

export const getSearchHistory = () => fetchWithAuth('/search-history');

// Scraper
export const triggerScrape = (data: any) => fetchWithAuth('/scrape', {
  method: 'POST',
  body: JSON.stringify(data)
});
export const triggerScrapeSimple = (data: any) => fetchWithAuth('/scrape-simple', {
  method: 'POST',
  body: JSON.stringify(data)
});
export const getScraperHealthStats = () => fetchWithAuth('/health/stats');

// Inbound Inbox
export const getInboundEmails = (status?: string) => {
  const query = status ? `?status=${status}` : '';
  return fetchWithAuth(`/inbound${query}`);
};
export const getInboundDetail = (id: number) => fetchWithAuth(`/inbound/${id}`);
export const archiveInboundEmail = (id: number) => fetchWithAuth(`/inbound/${id}/archive`, { method: 'POST' });

// Analytics Real Stats
export const getDeliveryStats = (days = 30) => fetchWithAuth(`/analytics/delivery-stats?days=${days}`);
export const getTagFunnel = () => fetchWithAuth('/analytics/tag-funnel');
export const generateAnalyticsSummary = () => fetchWithAuth('/ai/stats-insight'); // Fixed matching backend naming

// Admin - Vendors
export const getEngagements = (vendorId?: number) => {
  const query = vendorId ? `?vendor_id=${vendorId}` : '';
  return fetchWithAuth(`/engagements${query}`);
};
export const getAdminVendors = () => fetchWithAuth('/admin/vendors');
export const createAdminVendor = (data: any) => fetchWithAuth('/admin/vendors', {
  method: 'POST',
  body: JSON.stringify(data)
});
export const updateAdminVendor = (id: number, data: any) => fetchWithAuth(`/admin/vendors/${id}`, {
  method: 'PATCH',
  body: JSON.stringify(data)
});
export const deleteAdminVendor = (id: number) => fetchWithAuth(`/admin/vendors/${id}`, {
  method: 'DELETE'
});

// Admin - Global Pool (v2.7.1)
export const getGlobalPoolStats = () => fetchWithAuth('/admin/global-pool/stats');
export const clearGlobalPool = () => fetchWithAuth('/admin/global-pool/clear', {
  method: 'POST'
});
export const getAdminGlobalLeads = () => fetchWithAuth('/admin/global-leads');
export const getAdminAllLeads = () => fetchWithAuth('/admin/all-leads');

// Admin - Global Pool CRUD (v3.7.29)
export const updateGlobalLead = (id: number, data: any) => 
  fetchWithAuth(`/admin/global-leads/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data)
  });

export const deleteGlobalLead = (id: number) => 
  fetchWithAuth(`/admin/global-leads/${id}`, {
    method: 'DELETE'
  });

export const batchDeleteGlobalLeads = (ids: number[]) => 
  fetchWithAuth('/admin/global-leads/batch-delete', {
    method: 'POST',
    body: JSON.stringify({ ids })
  });

// Admin - User Leads CRUD (v3.7.29)
export const updateAdminLead = (id: number, data: any) => 
  fetchWithAuth(`/admin/leads/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data)
  });

export const deleteAdminLead = (id: number) => 
  fetchWithAuth(`/admin/leads/${id}`, {
    method: 'DELETE'
  });

// Industry Tags API (v3.7.30)
export const getIndustries = (level?: number, parentCode?: string) => {
  const params = new URLSearchParams();
  if (level) params.append('level', level.toString());
  if (parentCode) params.append('parent_code', parentCode);
  return fetchWithAuth(`/industries?${params.toString()}`);
};

export const getIndustryTree = () => fetchWithAuth('/industries/tree');

// Hunter.io API (v3.7.30)
export const hunterDomainSearch = (domain: string, limit: number = 10, seniority?: string, department?: string) => 
  fetchWithAuth('/scrape/hunter/domain', {
    method: 'POST',
    body: JSON.stringify({ domain, limit, seniority, department })
  });

export const hunterEmailFinder = (firstName: string, lastName: string, domain: string) => 
  fetchWithAuth('/scrape/hunter/finder', {
    method: 'POST',
    body: JSON.stringify({ first_name: firstName, last_name: lastName, domain })
  });

export const hunterEmailVerify = (email: string) => 
  fetchWithAuth('/scrape/hunter/verify', {
    method: 'POST',
    body: JSON.stringify({ email })
  });

export const hunterAccountInfo = () => fetchWithAuth('/scrape/hunter/account');

export const saveLeadsToGlobal = (leads: any[], source: string = 'hunter', sourceMode: string = 'manufacturer') => 
  fetchWithAuth('/scrape/save-to-global', {
    method: 'POST',
    body: JSON.stringify({ leads, source, source_mode: sourceMode })
  });

export const syncGlobalToPrivate = (globalIds: number[]) => 
  fetchWithAuth('/scrape/sync-to-private', {
    method: 'POST',
    body: JSON.stringify(globalIds)
  });

// Settings - SMTP
export const getSmtpSettings = () => fetchWithAuth('/settings/smtp');
export const saveSmtpSettings = (data: any) => fetchWithAuth('/settings/smtp', {
  method: 'POST',
  body: JSON.stringify(data)
});

// Settings - Email Channel (v3.5)
export const getEmailChannelSettings = () => fetchWithAuth('/settings/email-channel');
export const saveEmailChannelSettings = (data: any) => fetchWithAuth('/settings/email-channel', {
  method: 'POST',
  body: JSON.stringify(data)
});
export const testPostmarkApi = (apiToken: string) => fetchWithAuth(`/test/postmark?api_token=${apiToken}`, {
  method: 'POST'
});
export const checkPostmarkDomain = (domain: string, apiToken: string) => 
  fetchWithAuth(`/test/postmark/domain?domain=${domain}&api_token=${apiToken}`);

// Templates
export const getTemplates = () => fetchWithAuth('/templates');
export const createTemplate = (data: any) => fetchWithAuth('/templates', {
  method: 'POST',
  body: JSON.stringify(data)
});
export const updateTemplate = (id: number, data: any) => fetchWithAuth(`/templates/${id}`, {
  method: 'PUT',
  body: JSON.stringify(data)
});
export const deleteTemplate = (id: number) => fetchWithAuth(`/templates/${id}`, {
  method: 'DELETE'
});
export const generateAiTemplate = (data: any) => fetchWithAuth('/templates/ai-generate', {
  method: 'POST',
  body: JSON.stringify(data)
});

// Dashboard & Leads
export const getDashboardStats = () => fetchWithAuth('/dashboard/stats');
export const getLeads = () => fetchWithAuth('/leads');

// v3.5: Crawler Research Bench
export const testStrategy = (data: any) => fetchWithAuth('/test-strategy', {
  method: 'POST',
  body: JSON.stringify(data)
});

export const findEmail = (leadId: number) => fetchWithAuth(`/leads/${leadId}/find-email`, {
  method: 'POST'
});
export const batchFindEmails = (data: any) => fetchWithAuth('/leads/batch-find-emails', {
  method: 'POST',
  body: JSON.stringify(data)
});

// Leads v3.0 (Shared Intelligence)
export const updateLead = (id: number, data: any) => fetchWithAuth(`/leads/${id}`, {
  method: 'PATCH',
  body: JSON.stringify(data)
});

export const proposeCorrection = (data: { global_id: number; field_name: string; suggested_value: string }) => fetchWithAuth('/leads/propose', {
  method: 'POST',
  body: JSON.stringify(data)
});

// Keywords
export const generateAiKeywords = (keyword: string, count: number = 5) => fetchWithAuth('/keywords/generate', {
  method: 'POST',
  body: JSON.stringify({ keyword, count })
});

// System Settings
export const getSystemSettings = () => fetchWithAuth('/system/settings');
export const updateSystemSetting = (key: string, value: any) => fetchWithAuth('/system/settings', {
  method: 'POST',
  body: JSON.stringify({ key, value })
});

// Admin - Members
export const getAdminMembers = (params?: { role?: string; is_active?: boolean; search?: string }) => {
  const query = new URLSearchParams();
  if (params?.role) query.append('role', params.role);
  if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
  if (params?.search) query.append('search', params.search);
  const queryString = query.toString();
  return fetchWithAuth(`/admin/members${queryString ? '?' + queryString : ''}`);
};
export const getAdminMemberDetail = (id: number) => fetchWithAuth(`/admin/members/${id}`);
export const updateAdminMember = (id: number, data: any) => fetchWithAuth(`/admin/members/${id}`, {
  method: 'PATCH',
  body: JSON.stringify(data)
});
export const deleteAdminMember = (id: number) => fetchWithAuth(`/admin/members/${id}`, {
  method: 'DELETE'
});
export const resetMemberPassword = (id: number) => fetchWithAuth(`/admin/members/${id}/reset-password`, {
  method: 'POST'
});
export const getAdminStats = () => fetchWithAuth('/admin/stats');

// ── Admin: 爬蟲監控 ──
export const getAdminScrapeTasks = (status?: string, limit: number = 50) => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', limit.toString());
  return fetchWithAuth(`/admin/scrape-tasks?${params}`);
};

export const getAdminScrapeTaskDetail = (taskId: number) => 
  fetchWithAuth(`/admin/scrape-tasks/${taskId}`);

// Admin - Proposals (v3.0)
export const getAdminProposals = (status: string = 'Pending') => fetchWithAuth(`/admin/proposals?status=${status}`);
export const resolveProposal = (id: number, data: { status: string; reason?: string }) => fetchWithAuth(`/admin/proposals/${id}/resolve`, {
  method: 'POST',
  body: JSON.stringify(data)
});

export const getAdminScrapeTaskLogs = (taskId: number, level?: string) => {
  const params = new URLSearchParams();
  if (level) params.append('level', level);
  return fetchWithAuth(`/admin/scrape-tasks/${taskId}/logs?${params}`);
};

export const retryAdminScrapeTask = (taskId: number) =>
  fetchWithAuth(`/admin/scrape-tasks/${taskId}/retry`, { method: 'PUT' });

export const cleanupStaleTasks = () =>
  fetchWithAuth('/admin/scrape-tasks/stale', { method: 'DELETE' });

// ── v3.2: AI 評分與情報 ──
export const getUserPoints = () => fetchWithAuth('/user/points');

export const scoreLeads = (leadIds?: number[]) => fetchWithAuth('/leads/ai-score', {
  method: 'POST',
  body: JSON.stringify({ lead_ids: leadIds ?? null })
});

export const generateLeadBrief = (leadId: number) =>
  fetchWithAuth(`/leads/${leadId}/ai-brief`, { method: 'POST' });

export const optimizeEmailSubject = (subject: string, companyName: string = '') =>
  fetchWithAuth('/templates/ai-optimize-subject', {
    method: 'POST',
    body: JSON.stringify({ subject, company_name: companyName })
  });

export const generateABVersions = (companyName: string, tag: string = '', keywords: string[] = []) =>
  fetchWithAuth('/templates/ai-generate-ab', {
    method: 'POST',
    body: JSON.stringify({ company_name: companyName, tag, keywords })
  });


// ── v3.2/v3.6: 最佳寄信時間 & 回覆意圖 ──
export const getOptimalSendTime = () =>
  fetchWithAuth('/ai/recommend-send-time');

export const analyzeReplyIntent = (emailBody: string, logId?: number) =>
  fetchWithAuth('/ai/classify-intent', {
    method: 'POST',
    body: JSON.stringify({ email_body: emailBody, log_id: logId })
  });

export const getAiStatsInsight = () =>
  fetchWithAuth('/ai/stats-insight');
