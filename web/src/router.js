import { useEffect, useState } from 'react'

export function parseRoute(hash = window.location.hash) {
  const path = (hash || '#/new').replace(/^#/, '') || '/new'
  const match = path.match(/^\/task\/(\d+)(?:\/(proposals))?$/)
  if (match) return { name: match[2] === 'proposals' ? 'task-proposals' : 'task', id: Number(match[1]) }
  const routes = {
    '/new': 'new', '/my-tasks': 'my-tasks', '/catalog': 'catalog',
    '/my-proposals': 'my-proposals', '/stats': 'stats', '/ai': 'ai',
  }
  return { name: routes[path] || 'not-found' }
}

export function navigate(path) {
  window.location.hash = path.startsWith('#') ? path : `#${path}`
}

export function useRoute() {
  const [route, setRoute] = useState(() => parseRoute())
  useEffect(() => {
    const update = () => setRoute(parseRoute())
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [])
  return route
}
