// src/api/client.ts

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export function notifyUnauthorized() {
  localStorage.removeItem('curato_token');
  window.dispatchEvent(new CustomEvent('auth:unauthorized'));
}

async function handleResponse<T = any>(res: Response, fallbackError: string): Promise<T> {
  if (res.status === 401) {
    notifyUnauthorized();
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Your session has expired. Please sign in again.');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || fallbackError);
  }

  return res.json();
}

export async function login(username: string, password: string) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Incorrect email or password');
  }
  return res.json();
}

export async function getMe(token: string) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return handleResponse(res, 'Failed to authenticate user');
}

export async function uploadDocuments(token: string, files: File[]) {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData,
  });

  return handleResponse(res, 'Upload failed');
}

export async function processDocument(token: string, id: string) {
  const res = await fetch(`${API_BASE}/documents/${id}/process`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  return handleResponse(res, 'Processing failed');
}

export async function getTransaction(token: string, id: string) {
  // Try expense first
  let res = await fetch(`${API_BASE}/expenses/${id}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (res.status === 401) {
    notifyUnauthorized();
    throw new Error('Your session has expired. Please sign in again.');
  }

  if (res.status === 404) {
    // Fallback to income ONLY on genuine 404
    res = await fetch(`${API_BASE}/income/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  }

  return handleResponse(res, 'Transaction not found or could not be loaded.');
}

export async function updateTransaction(token: string, id: string, type: string, data: any) {
  const endpoint = type === 'EXPENSE' ? 'expenses' : 'income';
  const res = await fetch(`${API_BASE}/${endpoint}/${id}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });

  return handleResponse(res, 'Failed to update transaction');
}

export async function approveTransaction(token: string, id: string, type: string) {
  const endpoint = type === 'EXPENSE' ? 'expenses' : 'income';
  const res = await fetch(`${API_BASE}/${endpoint}/${id}/approve`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return handleResponse(res, 'Failed to approve transaction');
}

export async function getDocument(token: string, id: string) {
  const res = await fetch(`${API_BASE}/documents/${id}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return handleResponse(res, 'Document not found');
}

export async function getDocumentFile(token: string, id: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/documents/${id}/file`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (res.status === 401) {
    notifyUnauthorized();
    throw new Error('Your session has expired. Please sign in again.');
  }

  if (!res.ok) {
    throw new Error('Failed to load document file. It may be unavailable or you do not have permission.');
  }

  return res.blob();
}

export async function getCategories(token: string) {
  const res = await fetch(`${API_BASE}/categories`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return handleResponse(res, 'Failed to fetch categories');
}

export async function getIncomes(token: string, params: Record<string, string> = {}) {
  const query = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') {
      query.append(k, v);
    }
  }
  const qStr = query.toString();
  const url = `${API_BASE}/income${qStr ? '?' + qStr : ''}`;
  
  const res = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return handleResponse(res, 'Failed to fetch income transactions');
}

export async function getExpenses(token: string) {
  const res = await fetch(`${API_BASE}/expenses`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return handleResponse(res, 'Failed to fetch expense transactions');
}

export async function getReports(token: string, params: Record<string, string> = {}) {
  const query = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') {
      query.append(k, v);
    }
  }
  const qStr = query.toString();
  const url = `${API_BASE}/reports${qStr ? '?' + qStr : ''}`;
  
  const res = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return handleResponse(res, 'Failed to fetch reports');
}

export async function getCAReadiness(token: string, params: Record<string, string> = {}) {
  const query = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') {
      query.append(k, v);
    }
  }
  const qStr = query.toString();
  const url = `${API_BASE}/ca/readiness${qStr ? '?' + qStr : ''}`;
  
  const res = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return handleResponse(res, 'Failed to fetch CA readiness data');
}

export async function downloadCAPack(token: string, params: Record<string, string> = {}) {
  const query = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') {
      query.append(k, v);
    }
  }
  const qStr = query.toString();
  const url = `${API_BASE}/ca/export${qStr ? '?' + qStr : ''}`;
  
  const res = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (res.status === 401) {
    notifyUnauthorized();
    throw new Error('Your session has expired. Please sign in again.');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to generate CA Pack');
  }

  // It's a file download (ZIP)
  const blob = await res.blob();
  const contentDisposition = res.headers.get('Content-Disposition');
  let filename = 'CA_Pack.zip';
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}
