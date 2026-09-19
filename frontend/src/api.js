const API_BASE = '/api';

export async function fetchStatus() {
  const res = await fetch(`${API_BASE}/status`);
  return res.json();
}

export async function fetchConfig() {
  const res = await fetch(`${API_BASE}/config`);
  return res.json();
}

export async function saveConfig(configData) {
  const res = await fetch(`${API_BASE}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(configData)
  });
  return res.json();
}

export async function testEmby(data = {}) {
  const res = await fetch(`${API_BASE}/test/emby`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function testTelegram(data = {}) {
  const res = await fetch(`${API_BASE}/test/telegram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function testDiscord(data = {}) {
  const res = await fetch(`${API_BASE}/test/discord`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function testWebhook(data = {}) {
  const res = await fetch(`${API_BASE}/test/webhook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function fetchMediaRanks(days = 1) {
  const res = await fetch(`${API_BASE}/ranks/media?days=${days}`);
  return res.json();
}

export async function fetchUserRanks(days = 7, page = 1, pageSize = 10) {
  const res = await fetch(`${API_BASE}/ranks/users?days=${days}&page=${page}&page_size=${pageSize}`);
  return res.json();
}

export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/ranks/sessions`);
  return res.json();
}

export async function triggerTask(taskName) {
  const res = await fetch(`${API_BASE}/trigger/${taskName}`, {
    method: 'POST'
  });
  return res.json();
}

export async function uploadUserCover(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/poster/upload_user_cover`, {
    method: 'POST',
    body: formData
  });
  return res.json();
}
