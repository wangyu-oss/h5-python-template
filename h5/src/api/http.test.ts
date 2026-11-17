import { describe, expect, it } from 'vitest'
import { requestKey } from './http'

describe('requestKey', () => {
  it('keeps different pages from sharing one cancel key', () => {
    const first = requestKey({ method: 'get', url: '/api/v1/announcements', params: { page: 1, page_size: 10 } })
    const second = requestKey({ method: 'get', url: '/api/v1/announcements', params: { page: 2, page_size: 10 } })
    expect(first).not.toBe(second)
  })

  it('ignores param order and method case', () => {
    const left = requestKey({ method: 'GET', url: '/api/v1/messages', params: { page: 1, category: 'system' } })
    const right = requestKey({ method: 'get', url: '/api/v1/messages', params: { category: 'system', page: 1 } })
    expect(left).toBe(right)
  })
})
