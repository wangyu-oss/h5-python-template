interface StorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

interface Envelope {
  value: unknown
  expireAt: number | null
}

export function createCache(storage: StorageLike) {
  return {
    set(key: string, value: unknown, ttlMs?: number) {
      const envelope: Envelope = {
        value,
        expireAt: ttlMs ? Date.now() + ttlMs : null,
      }
      storage.setItem(key, JSON.stringify(envelope))
    },
    get<T>(key: string): T | null {
      const raw = storage.getItem(key)
      if (!raw) return null
      try {
        const envelope = JSON.parse(raw) as Envelope
        if (envelope.expireAt && envelope.expireAt < Date.now()) {
          storage.removeItem(key)
          return null
        }
        return envelope.value as T
      } catch {
        storage.removeItem(key)
        return null
      }
    },
    remove(key: string) {
      storage.removeItem(key)
    },
  }
}

const memory = new Map<string, string>()
const memoryStorage: StorageLike = {
  getItem: (key) => memory.get(key) ?? null,
  setItem: (key, value) => memory.set(key, value),
  removeItem: (key) => memory.delete(key),
}

export const localCache = createCache(typeof localStorage === 'undefined' ? memoryStorage : localStorage)
export const sessionCache = createCache(typeof sessionStorage === 'undefined' ? memoryStorage : sessionStorage)

const KEEP_ON_CLEAR = new Set(['h5-theme', 'h5-locale', 'h5-theme-chosen'])

export function clearBusinessCache() {
  if (typeof localStorage === 'undefined') return
  const drop: string[] = []
  for (let index = 0; index < localStorage.length; index += 1) {
    const key = localStorage.key(index)
    if (key && !KEEP_ON_CLEAR.has(key)) drop.push(key)
  }
  drop.forEach((key) => localStorage.removeItem(key))
  sessionStorage.clear()
}

export function idbSet(key: string, value: unknown, ttlMs?: number) {
  return new Promise<void>((resolve, reject) => {
    const request = indexedDB.open('h5-template', 1)
    request.onupgradeneeded = () => request.result.createObjectStore('kv')
    request.onerror = () => reject(request.error)
    request.onsuccess = () => {
      const db = request.result
      const tx = db.transaction('kv', 'readwrite')
      tx.objectStore('kv').put({ value, expireAt: ttlMs ? Date.now() + ttlMs : null }, key)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    }
  })
}

export function idbGet<T>(key: string) {
  return new Promise<T | null>((resolve, reject) => {
    const request = indexedDB.open('h5-template', 1)
    request.onupgradeneeded = () => request.result.createObjectStore('kv')
    request.onerror = () => reject(request.error)
    request.onsuccess = () => {
      const db = request.result
      const tx = db.transaction('kv', 'readonly')
      const get = tx.objectStore('kv').get(key)
      get.onsuccess = () => {
        const row = get.result as { value: T; expireAt: number | null } | undefined
        if (!row || (row.expireAt && row.expireAt < Date.now())) {
          resolve(null)
          return
        }
        resolve(row.value)
      }
      get.onerror = () => reject(get.error)
    }
  })
}
