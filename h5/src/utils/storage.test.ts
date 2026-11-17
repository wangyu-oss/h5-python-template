import { describe, expect, it } from 'vitest'
import { createCache } from './storage'

function memory() {
  const data = new Map<string, string>()
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => data.set(key, value),
    removeItem: (key: string) => data.delete(key),
  }
}

describe('cache', () => {
  it('reads a value before it expires', () => {
    const cache = createCache(memory())
    cache.set('name', 'h5', 60_000)
    expect(cache.get('name')).toBe('h5')
  })

  it('drops an expired value', () => {
    const cache = createCache(memory())
    cache.set('name', 'h5', -1)
    expect(cache.get('name')).toBeNull()
  })
})
