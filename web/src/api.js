import { mockRequest } from './mocks.js'

export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

async function request(path, method = 'GET', body) {
  if (USE_MOCKS) return mockRequest(method, path, body)
  let response
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    const error = new Error('Бэкенд не отвечает. Проверьте подключение и попробуйте снова.')
    error.status = 0
    throw error
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const error = new Error(payload?.error?.message || 'Не удалось выполнить запрос')
    error.status = response.status
    error.code = payload?.error?.code
    throw error
  }
  return payload
}

function query(params) {
  const values = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') values.set(key, String(value))
  })
  const suffix = values.toString()
  return suffix ? `?${suffix}` : ''
}

export const getHealth = () => request('/health')
export const getMeta = () => request('/meta')
export const getBusinesses = () => request('/businesses')
export const getTeams = () => request('/teams')

export const createTask = ({ businessId, industry, draftText }) => request('/tasks', 'POST', {
  business_id: businessId, industry, draft_text: draftText,
})
export const getTask = (id) => request(`/tasks/${id}`)
export const getBusinessTasks = (businessId) => request(`/tasks${query({ business_id: businessId })}`)
export const submitAnswers = (id, answers) => request(`/tasks/${id}/answers`, 'POST', { answers })
export const updateCard = (id, card) => request(`/tasks/${id}/card`, 'PUT', { card })
export const confirmCard = (id) => request(`/tasks/${id}/confirm`, 'POST')
export const publishTask = (id) => request(`/tasks/${id}/publish`, 'POST')
export const assistCard = (id) => request(`/tasks/${id}/assist`, 'POST')
export const checkTaskAsStudent = (id) => request(`/tasks/${id}/student-check`, 'POST')
export const previewRating = (card) => request('/rating/preview', 'POST', { card })

export const getCatalog = ({ industry, level } = {}) => request(`/catalog${query({ industry, level })}`)
export const getRecommendations = (teamId) => request(`/teams/${teamId}/recommendations`)

export const createProposal = (taskId, { teamId, idea, plan, timeline, link }) =>
  request(`/tasks/${taskId}/proposals`, 'POST', { team_id: teamId, idea, plan, timeline, link })
export const getTaskProposals = (taskId) => request(`/tasks/${taskId}/proposals`)
export const getTeamProposals = (teamId) => request(`/teams/${teamId}/proposals`)
export const decideProposal = (proposalId, decision, comment = '') =>
  request(`/proposals/${proposalId}/decision`, 'POST', { decision, comment })
export const addMilestone = (proposalId, title) =>
  request(`/proposals/${proposalId}/milestones`, 'POST', { title })

export const getAiSpec = () => request('/ai/spec')
export const getStats = () => request('/stats')
