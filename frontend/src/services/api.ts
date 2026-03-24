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
