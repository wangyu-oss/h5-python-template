export interface RuleResult {
  ok: boolean
  message: string
}

export function required(value: unknown, message = '必填') {
  const empty = value === undefined || value === null || String(value).trim() === ''
  return { ok: !empty, message: empty ? message : '' }
}

export function minLength(value: unknown, length: number, message?: string) {
  const ok = String(value || '').trim().length >= length
  return { ok, message: ok ? '' : message || `至少 ${length} 个字符` }
}

export function phone(value: unknown) {
  const ok = /^1\d{10}$/.test(String(value || ''))
  return { ok, message: ok ? '' : '手机号格式不正确' }
}

export async function runRules(value: unknown, rules: Array<(value: unknown) => RuleResult | Promise<RuleResult>>) {
  for (const rule of rules) {
    const result = await rule(value)
    if (!result.ok) return result
  }
  return { ok: true, message: '' }
}
