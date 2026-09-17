// src/api/client.ts

const API_BASE = '/api/v1';

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
    throw new Error('Login failed');
  }
  return res.json();
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

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Upload failed');
  }

  return res.json();
}

export async function processDocument(token: string, id: string) {
  const res = await fetch(`${API_BASE}/documents/${id}/process`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Processing failed');
  }

  return res.json();
}

export async function getTransaction(token: string, id: string) {
  // Try expense first
  let res = await fetch(`${API_BASE}/expenses/${id}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (res.status === 404) {
    // Fallback to income ONLY on genuine 404
    res = await fetch(`${API_BASE}/income/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Transaction not found or could not be loaded.');
  }

  return res.json();
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

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update transaction');
  }

  return res.json();
}

export async function approveTransaction(token: string, id: string, type: string) {
  const endpoint = type === 'EXPENSE' ? 'expenses' : 'income';
  const res = await fetch(`${API_BASE}/${endpoint}/${id}/approve`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to approve transaction');
  }

  return res.json();
}

export async function getDocument(token: string, id: string) {
  const res = await fetch(`${API_BASE}/documents/${id}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Document not found');
  }

  return res.json();
}

export async function getDocumentFile(token: string, id: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/documents/${id}/file`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    throw new Error('Failed to load document file. It may be unavailable or you do not have permission.');
  }

  return res.blob();
}

export async function getCategories(token: string) {
  const res = await fetch(`${API_BASE}/categories`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch categories');
  }

  return res.json();
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

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch income transactions');
  }

  return res.json();
}

export async function getExpenses(token: string) {
  const res = await fetch(`${API_BASE}/expenses`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch expense transactions');
  }

  return res.json();
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

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch reports');
  }

  return res.json();
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

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch CA readiness data');
  }

  return res.json();
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
