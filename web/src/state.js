import { createContext, createElement, useContext, useEffect, useMemo, useState } from 'react'
import { getBusinesses, getHealth, getMeta, getTeams, USE_MOCKS } from './api.js'

const STORAGE_KEY = 'challenge-hub-identity'
const AppContext = createContext(null)

function savedIdentity() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    if (value?.role === 'business' || value?.role === 'team') return value
  } catch { /* без хранилища выбираем первый бизнес */ }
  return { role: 'business', id: null }
}

export function AppProvider({ children }) {
  const [identity, setIdentityState] = useState(savedIdentity)
  const [meta, setMeta] = useState(null)
  const [businesses, setBusinesses] = useState([])
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [backendDown, setBackendDown] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.allSettled([getHealth(), getMeta(), getBusinesses(), getTeams()]).then((results) => {
      if (!active) return
      const [health, metaResult, businessResult, teamResult] = results
      if (health.status === 'rejected') setBackendDown(!USE_MOCKS)
      if (metaResult.status === 'fulfilled') setMeta(metaResult.value)
      if (businessResult.status === 'fulfilled') setBusinesses(businessResult.value)
      if (teamResult.status === 'fulfilled') setTeams(teamResult.value)
      const failed = [metaResult, businessResult, teamResult].find((result) => result.status === 'rejected')
      if (failed) setError(failed.reason.message || 'Не удалось загрузить данные платформы')
      setLoading(false)
    })
    return () => { active = false }
  }, [])

  useEffect(() => {
    const list = identity.role === 'business' ? businesses : teams
    if (!list.length) return
    if (!list.some((item) => item.id === identity.id)) {
      setIdentityState((previous) => ({ ...previous, id: list[0].id }))
    }
  }, [businesses, teams, identity])

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(identity)) } catch { /* необязательно */ }
  }, [identity])

  function setIdentity(role, id) {
    const list = role === 'business' ? businesses : teams
    setIdentityState({ role, id: id ?? list[0]?.id ?? null })
  }

  const selected = (identity.role === 'business' ? businesses : teams).find((item) => item.id === identity.id) || null
  const value = useMemo(() => ({
    identity, selected, setIdentity, meta, businesses, teams, loading, backendDown, error, useMocks: USE_MOCKS,
  }), [identity, selected, meta, businesses, teams, loading, backendDown, error])
  return createElement(AppContext.Provider, { value }, children)
}

export function useApp() {
  const value = useContext(AppContext)
  if (!value) throw new Error('AppProvider не подключён')
  return value
}
