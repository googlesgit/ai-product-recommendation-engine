const STORAGE_KEY = 'rec_engine_session_id';

/** Persistent anonymous id — survives refresh, per browser. */
export function getSessionId() {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = `sess_${crypto.randomUUID()}`;
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}

export function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
}

export function isSessionId(id) {
  return typeof id === 'string' && id.startsWith('sess_');
}
