export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('token');
      // Force redirect to login if token is expired/invalid
      window.location.href = '/login';
    }
    const errorData = await response.json().catch(() => ({ detail: 'API request failed' }));
    throw new ApiError(response.status, errorData.detail || 'API request failed');
  }

  if (response.status !== 204) {
    return response.json();
  }
}

// Typed API Client
export const apiClient = {
  get: <T>(endpoint: string) => fetchWithAuth(endpoint, { method: 'GET' }) as Promise<T>,
  post: <T>(endpoint: string, data?: any) => fetchWithAuth(endpoint, { 
    method: 'POST', 
    body: data ? JSON.stringify(data) : undefined 
  }) as Promise<T>,
  put: <T>(endpoint: string, data?: any) => fetchWithAuth(endpoint, { 
    method: 'PUT', 
    body: data ? JSON.stringify(data) : undefined 
  }) as Promise<T>,
  delete: <T>(endpoint: string) => fetchWithAuth(endpoint, { method: 'DELETE' }) as Promise<T>,
};
