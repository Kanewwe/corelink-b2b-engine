export const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? 'http://localhost:8000/api'
  : '/api';

export const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  };
};

export const fetchWithAuth = async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
  const headers = getAuthHeaders();
  
  if (options.headers) {
    Object.assign(headers, options.headers);
  }

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

// Settings - SMTP
export const getSmtpSettings = () => fetchWithAuth('/settings/smtp');
export const saveSmtpSettings = (data: any) => fetchWithAuth('/settings/smtp', {
  method: 'POST',
  body: JSON.stringify(data)
});

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
export const findEmail = (leadId: number) => fetchWithAuth(`/leads/${leadId}/find-email`, {
  method: 'POST'
});
export const batchFindEmails = (data: any) => fetchWithAuth('/leads/batch-find-emails', {
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

export const getAdminScrapeTaskLogs = (taskId: number, level?: string) => {
  const params = new URLSearchParams();
  if (level) params.append('level', level);
  return fetchWithAuth(`/admin/scrape-tasks/${taskId}/logs?${params}`);
};

export const retryAdminScrapeTask = (taskId: number) =>
  fetchWithAuth(`/admin/scrape-tasks/${taskId}/retry`, { method: 'PUT' });

export const cleanupStaleTasks = () =>
  fetchWithAuth('/admin/scrape-tasks/stale', { method: 'DELETE' });
