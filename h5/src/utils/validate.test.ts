import { describe, expect, it } from 'vitest'
import { phone, required, runRules } from './validate'

describe('validate', () => {
  it('rejects empty and bad phone numbers', async () => {
    expect(required('').ok).toBe(false)
    expect(phone('123').ok).toBe(false)
    const result = await runRules('13800138000', [required, phone])
    expect(result.ok).toBe(true)
  })
})
