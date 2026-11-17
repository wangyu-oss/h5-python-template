import type { App, Directive } from 'vue'

type CleanupEl = HTMLElement & { _cleanup?: () => void }

const debounce: Directive = {
  mounted(el, binding) {
    let timer = 0
    const onClick = () => {
      window.clearTimeout(timer)
      timer = window.setTimeout(() => binding.value?.(), Number(binding.arg || 300))
    }
    el.addEventListener('click', onClick)
    ;(el as CleanupEl)._cleanup = () => {
      window.clearTimeout(timer)
      el.removeEventListener('click', onClick)
    }
  },
  unmounted(el) {
    ;(el as CleanupEl)._cleanup?.()
  },
}

const longpress: Directive = {
  mounted(el, binding) {
    let timer = 0
    const start = (event: Event) => {
      if (event.cancelable) event.preventDefault()
      timer = window.setTimeout(() => binding.value?.(), 600)
    }
    const clear = () => window.clearTimeout(timer)
    el.addEventListener('touchstart', start)
    el.addEventListener('mousedown', start)
    el.addEventListener('touchend', clear)
    el.addEventListener('mouseup', clear)
    el.addEventListener('mouseleave', clear)
    ;(el as CleanupEl)._cleanup = () => {
      clear()
      el.removeEventListener('touchstart', start)
      el.removeEventListener('mousedown', start)
      el.removeEventListener('touchend', clear)
      el.removeEventListener('mouseup', clear)
      el.removeEventListener('mouseleave', clear)
    }
  },
  unmounted(el) {
    ;(el as CleanupEl)._cleanup?.()
  },
}

const lazy: Directive = {
  mounted(el: HTMLImageElement, binding) {
    el.dataset.src = binding.value
    el.style.background = '#eee'
    const observer = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return
      el.src = el.dataset.src || ''
      observer.disconnect()
    })
    observer.observe(el)
    ;(el as CleanupEl)._cleanup = () => observer.disconnect()
  },
  unmounted(el) {
    ;(el as CleanupEl)._cleanup?.()
  },
}

export function setupDirectives(app: App) {
  app.directive('debounce', debounce)
  app.directive('longpress', longpress)
  app.directive('lazy', lazy)
}
