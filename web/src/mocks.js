// Демо-данные повторяют формы ответов из partner/01-api.md.
const STORAGE_KEY = 'challenge-hub-mocks-v1'
const now = () => new Date().toISOString()
const copy = (value) => JSON.parse(JSON.stringify(value))

const meta = {
  industries: ['Агро', 'Ритейл', 'Логистика', 'Образование', 'Финансы'],
  fields: [
    { key: 'title', label: 'Название' }, { key: 'context', label: 'Контекст' },
    { key: 'need', label: 'Потребность' }, { key: 'users', label: 'Пользователи' },
    { key: 'data', label: 'Данные и материалы' }, { key: 'constraints', label: 'Ограничения' },
    { key: 'expected_result', label: 'Ожидаемый результат' },
    { key: 'success_criteria', label: 'Критерии успеха' }, { key: 'contact', label: 'Контакт' },
    { key: 'interaction_format', label: 'Формат взаимодействия' },
  ],
  indicators: [
    { key: 'context_need', label: 'Контекст и потребность', max: 20, fields: ['context', 'need'] },
    { key: 'data', label: 'Данные и материалы', max: 20, fields: ['data'] },
    { key: 'expected_result', label: 'Ожидаемый результат', max: 15, fields: ['expected_result'] },
    { key: 'success_criteria', label: 'Критерии успеха', max: 15, fields: ['success_criteria'] },
    { key: 'constraints', label: 'Ограничения', max: 10, fields: ['constraints'] },
    { key: 'users', label: 'Пользователи', max: 10, fields: ['users'] },
    { key: 'business_link', label: 'Связь с бизнесом', max: 10, fields: ['contact', 'interaction_format'] },
  ],
  levels: [
    { key: 'draft', label: 'черновик', min: 0, max: 39 },
    { key: 'working', label: 'рабочая', min: 40, max: 69 },
    { key: 'ready', label: 'готовая', min: 70, max: 89 },
    { key: 'priority', label: 'приоритетная', min: 90, max: 100 },
  ],
  draft_examples: [
    { industry: 'Агро', text: 'Хотим понимать, какие поля скоро потребуют полива.' },
    { industry: 'Ритейл', text: 'Нужен удобный отчёт по продажам. Есть выгрузки касс в CSV за 6 месяцев, но сотрудники собирают сводку вручную.' },
    { industry: 'Логистика', text: 'У нас 80 доставок в день. Хотим сократить время построения маршрутов до 15 минут. Есть адреса заказов в Excel, нужен пилот для диспетчеров.' },
    { industry: 'Образование', text: 'Преподавателям нужен обзор посещаемости. Есть журнал в Excel за 2 года. Результат — панель по 20 группам; успешность — отчёт за 5 минут, данные обезличены.' },
    { industry: 'Финансы', text: 'Команда поддержки вручную сверяет 1200 платежей в день по выгрузке SQL. Нужен сервис сверки с точностью 98% за 3 месяца, бюджет до 900000 тенге, пилот и еженедельные встречи.' },
  ],
}

const businesses = [
  { id: 1, name: 'ТОО «Агро Север»', industry: 'Агро' },
  { id: 2, name: 'ТОО «Городской Маркет»', industry: 'Ритейл' },
  { id: 3, name: 'ТОО «Путь Логистик»', industry: 'Логистика' },
]
const teams = [
  { id: 1, name: 'DataCats', interests: ['агро', 'полив'], skills: ['python', 'аналитика'], technologies: ['FastAPI', 'pandas'], points: 0 },
  { id: 2, name: 'Retail Pulse', interests: ['ритейл', 'продажи'], skills: ['аналитика', 'дизайн'], technologies: ['React', 'SQL'], points: 0 },
  { id: 3, name: 'RouteLab', interests: ['логистика', 'маршруты'], skills: ['оптимизация', 'python'], technologies: ['FastAPI', 'PostgreSQL'], points: 0 },
  { id: 4, name: 'EduVector', interests: ['образование', 'обучение'], skills: ['аналитика', 'интерфейсы'], technologies: ['React', 'Python'], points: 0 },
  { id: 5, name: 'FinCraft', interests: ['финансы', 'платежи'], skills: ['безопасность', 'аналитика'], technologies: ['SQL', 'Python'], points: 0 },
]

const emptyCard = () => Object.fromEntries(meta.fields.map(({ key }) => [key, '']))
const levelFor = (score) => meta.levels.find((item) => score >= item.min && score <= item.max)

function rate(card) {
  const breakdown = meta.indicators.map((indicator) => {
    const filled = indicator.fields.filter((field) => String(card?.[field] || '').trim()).length
    const points = Math.round(indicator.max * filled / indicator.fields.length)
    return {
      key: indicator.key, label: indicator.label, points, max: indicator.max,
      explain: points ? `Заполнено ${filled} из ${indicator.fields.length} полей` : 'Пока нет сведений',
      hint: points === indicator.max ? '' : `Добавьте сведения: ${indicator.fields.map((key) => meta.fields.find((field) => field.key === key)?.label).join(', ')}`,
    }
  })
  const score = breakdown.reduce((sum, item) => sum + item.points, 0)
  const level = levelFor(score)
  const next = meta.levels.find((item) => item.min > score)
  return {
    score, level: level.key, level_label: level.label, breakdown,
    missing: breakdown.filter((item) => item.points === 0).map((item) => item.key),
    next_best: breakdown.filter((item) => item.points < item.max)
      .map((item) => ({ key: item.key, label: item.label, gain: item.max - item.points, hint: item.hint }))
      .sort((a, b) => b.gain - a.gain),
    next_level: next ? { key: next.key, label: next.label, points_needed: next.min - score } : null,
    penalties: [],
  }
}

function seededTask(id, businessId, industry, draftText, cardFields, hoursAgo) {
  const card = { ...emptyCard(), ...cardFields }
  const rating = rate(card)
  return {
    id, status: 'published', business: copy(businesses.find((item) => item.id === businessId)),
    industry, draft_text: draftText, card,
    sources: Object.fromEntries(Object.entries(card).filter(([, value]) => value).map(([key]) => [key, 'manual'])),
    questions: [], rating, confirmed: true,
    official: { score: rating.score, level: rating.level },
    history: [{ at: new Date(Date.now() - hoursAgo * 3600000).toISOString(), event: 'confirm', score: rating.score, level: rating.level, confirmed: true }],
    ai: { mode: 'stub', attempts: 0, warnings: [] },
    published_at: new Date(Date.now() - hoursAgo * 3600000).toISOString(),
  }
}

function freshState() {
  return {
    tasks: [
      seededTask(1, 1, 'Агро', 'Хотим понимать, какие поля скоро потребуют полива.', {
        title: 'Понять, когда полям нужен полив', context: 'Хотим понимать, какие поля скоро потребуют полива.',
      }, 4),
      seededTask(2, 2, 'Ритейл', 'Нужен удобный отчёт по продажам для команды магазина.', {
        title: 'Отчёт по продажам магазина', context: 'Сейчас сотрудники собирают сводку продаж вручную.',
        need: 'Сократить ручную работу при подготовке ежедневного отчёта.',
        data: 'Выгрузки касс в CSV за 6 месяцев.', expected_result: 'Рабочая панель с продажами по дням и категориям.',
        constraints: 'Пилот за 4 недели.', users: 'Аналитики и управляющие магазина.',
      }, 3),
      seededTask(3, 3, 'Логистика', 'Хотим быстрее строить маршруты для 80 доставок в день.', {
        title: 'Оптимизация маршрутов доставки', context: 'Диспетчеры планируют 80 доставок в день вручную.',
        need: 'Сократить время построения маршрутов до 15 минут.', users: 'Диспетчеры доставки.',
        data: 'Адреса заказов в Excel за последние 6 месяцев.', constraints: 'Пилот за 6 недель, доступ только к обезличенным данным.',
        expected_result: 'Прототип сервиса маршрутизации и демонстрация на 80 заказах.',
        success_criteria: 'Время построения маршрута не более 15 минут.',
        contact: 'logistics@example.kz', interaction_format: 'Созвон раз в неделю и письменная обратная связь.',
      }, 2),
    ],
    proposals: [
      { id: 1, task_id: 2, team: { id: 2, name: 'Retail Pulse', skills: ['аналитика', 'дизайн'], technologies: ['React', 'SQL'] }, idea: 'Панель продаж по данным касс', plan: '1) очистка данных 2) дизайн 3) пилот', timeline: '4 недели', link: 'https://example.com/retail-pulse', status: 'submitted', comment: '', created_at: now(), decided_at: null },
      { id: 2, task_id: 3, team: { id: 3, name: 'RouteLab', skills: ['оптимизация', 'python'], technologies: ['FastAPI', 'PostgreSQL'] }, idea: 'Поиск оптимального маршрута', plan: '1) анализ адресов 2) алгоритм 3) проверка', timeline: '6 недель', link: 'https://example.com/route-lab', status: 'submitted', comment: '', created_at: now(), decided_at: null },
    ],
    teams: copy(teams),
  }
}

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    if (saved?.tasks && saved?.proposals && saved?.teams) return saved
  } catch { /* браузер может запрещать хранилище */ }
  return freshState()
}

const state = loadState()
function persist() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)) } catch { /* работает в памяти */ }
}
function error(status, message) {
  const result = new Error(message)
  result.status = status
  return result
}
function taskById(id) {
  const task = state.tasks.find((item) => item.id === Number(id))
  if (!task) throw error(404, 'Задача не найдена')
  return task
}
function presentTask(task) {
  const published = state.tasks.filter((item) => item.status === 'published' && item.id !== task.id)
  const placeAt = (score) => ({ place: 1 + published.filter((item) => (item.official?.score ?? 0) > score).length, of: published.length + 1 })
  const rating = rate(task.card)
  const score = task.status === 'published' ? task.official?.score ?? 0 : rating.score
  const position = { ...placeAt(score), projected: task.status !== 'published' }
  const searchable = `${task.industry} ${Object.values(task.card).join(' ')}`.toLowerCase()
  const audienceTeams = state.teams.map((team) => ({ id: team.id, name: team.name,
    match: [...team.interests, ...team.skills, ...team.technologies].filter((term) => searchable.includes(term.toLowerCase())),
  })).filter((team) => team.match.length)
  const audience = { recommended: ['working', 'ready', 'priority'].includes(task.status === 'published' ? task.official?.level : rating.level), teams: audienceTeams }
  rating.next_best = rating.next_best.map((item) => {
    const thenScore = Math.min(100, rating.score + item.gain)
    const thenLevel = levelFor(thenScore)
    return { ...item, then: { score: thenScore, level: thenLevel.key, ...placeAt(thenScore),
      teams: ['working', 'ready', 'priority'].includes(thenLevel.key) ? audienceTeams.map((team) => team.name) : [],
    } }
  })
  return copy({ ...task, rating, position, audience, privacy: task.privacy || [], proposals: state.proposals.filter((item) => item.task_id === task.id).length })
}
function record(task, event) {
  task.rating = rate(task.card)
  task.history.push({ at: now(), event, score: task.rating.score, level: task.rating.level, confirmed: task.confirmed })
  persist()
  return presentTask(task)
}

const questionTemplates = [
  ['data', 'Какие данные уже есть: выгрузки, документы, примеры?'],
  ['success_criteria', 'По какому измеримому показателю вы примете результат?'],
  ['expected_result', 'Что конкретно команда должна показать в конце работы?'],
  ['users', 'Кто будет пользоваться решением?'],
  ['constraints', 'Какие сроки, технологии или ограничения доступа нужно учесть?'],
]

function createTask(body) {
  const business = businesses.find((item) => item.id === Number(body.business_id))
  if (!business) throw error(404, 'Бизнес не найден')
  const draftText = String(body.draft_text || '').trim()
  if (!draftText) throw error(400, 'Опишите задачу перед отправкой')
  const id = Math.max(0, ...state.tasks.map((item) => item.id)) + 1
  const card = emptyCard()
  card.context = draftText
  const task = {
    id, status: 'new', business: copy(business), industry: body.industry || business.industry,
    draft_text: draftText, card, sources: { context: draftText },
    questions: questionTemplates.map(([field, text], index) => ({ id: id * 100 + index + 1, field, text, answer: '' })),
    rating: rate(card), confirmed: false, official: null, history: [],
    ai: { mode: 'stub', attempts: 0, warnings: [] }, published_at: null,
  }
  task.history.push({ at: now(), event: 'draft', score: task.rating.score, level: task.rating.level, confirmed: false })
  state.tasks.push(task)
  persist()
  return presentTask(task)
}

function answerTask(id, body) {
  const task = taskById(id)
  for (const item of body.answers || []) {
    const question = task.questions.find((entry) => entry.id === Number(item.question_id))
    if (!question) throw error(400, 'Вопрос не найден')
    const answer = String(item.answer || '').trim()
    if (!answer) continue
    question.answer = answer
    task.card[question.field] = answer
    task.sources[question.field] = answer
  }
  task.status = 'card'
  task.confirmed = false
  return record(task, 'answers')
}

function updateCard(id, body) {
  const task = taskById(id)
  for (const [key, value] of Object.entries(body.card || {})) {
    if (!meta.fields.some((field) => field.key === key)) throw error(400, 'Неизвестное поле карточки')
    task.card[key] = String(value)
    task.sources[key] = 'manual'
  }
  task.confirmed = false
  return record(task, 'edit')
}

function confirmTask(id) {
  const task = taskById(id)
  task.confirmed = true
  task.rating = rate(task.card)
  task.official = { score: task.rating.score, level: task.rating.level }
  return record(task, 'confirm')
}

function publishTask(id) {
  const task = taskById(id)
  if (!task.confirmed || !task.card.title.trim()) throw error(409, 'Подтвердите карточку и укажите название')
  task.status = 'published'
  task.published_at = now()
  persist()
  return presentTask(task)
}

function studentCheck(id) {
  const task = taskById(id)
  const gaps = [...meta.indicators.flatMap((item) => item.fields), 'title']
    .filter((key) => !String(task.card[key] || '').trim()).slice(0, 6)
  return {
    can_start: gaps.length === 0,
    first_week: [],
    assumptions: gaps.map((field) => ({
      field,
      assumption: `Сведения в поле «${meta.fields.find((item) => item.key === field)?.label}» пока не указаны`,
      question: `Что команде нужно знать про «${meta.fields.find((item) => item.key === field)?.label}» до начала работы?`,
    })),
    ai: { mode: 'stub', attempts: 0, warnings: [] },
  }
}

function catalog(industry, level) {
  return state.tasks.filter((task) => task.status === 'published')
    .filter((task) => !industry || task.industry === industry)
    .filter((task) => !level || task.official?.level === level)
    .sort((a, b) => (b.official?.score || 0) - (a.official?.score || 0) || String(b.published_at).localeCompare(String(a.published_at)))
    .map((task) => ({
      id: task.id, title: task.card.title, industry: task.industry, business: task.business.name,
      summary: task.draft_text.length > 140 ? `${task.draft_text.slice(0, 140)}…` : task.draft_text,
      score: task.official.score, level: task.official.level,
      level_label: levelFor(task.official.score).label,
      needs_clarification: task.official.level === 'draft', highlight: task.official.level === 'priority',
      proposals: state.proposals.filter((item) => item.task_id === task.id).length,
      published_at: task.published_at,
    }))
}

function recommendations(teamId) {
  const team = state.teams.find((item) => item.id === Number(teamId))
  if (!team) throw error(404, 'Команда не найдена')
  const terms = [...team.interests, ...team.skills, ...team.technologies]
  return catalog().filter((task) => task.score >= 40).map((task) => {
    const haystack = `${task.industry} ${task.title} ${task.summary}`.toLowerCase()
    return { task_id: task.id, title: task.title, score: task.score, level: task.level,
      match: terms.filter((term) => haystack.includes(term.toLowerCase())) }
  }).filter((task) => task.match.length)
}

function createProposal(id, body) {
  const task = taskById(id)
  if (task.status !== 'published') throw error(409, 'Задача ещё не опубликована')
  const team = state.teams.find((item) => item.id === Number(body.team_id))
  if (!team) throw error(404, 'Команда не найдена')
  if (!body.idea?.trim() || !body.plan?.trim() || !body.timeline?.trim() || !/^https?:\/\//.test(body.link || '')) {
    throw error(400, 'Заполните идею, план, срок и ссылку http(s)://')
  }
  const proposal = {
    id: Math.max(0, ...state.proposals.map((item) => item.id)) + 1,
    task_id: task.id, team: { id: team.id, name: team.name, skills: team.skills, technologies: team.technologies }, idea: body.idea.trim(),
    plan: body.plan.trim(), timeline: body.timeline.trim(), link: body.link.trim(),
    status: 'submitted', comment: '', created_at: now(), decided_at: null,
  }
  state.proposals.push(proposal)
  persist()
  return copy(proposal)
}

function decideProposal(id, body) {
  const proposal = state.proposals.find((item) => item.id === Number(id))
  if (!proposal) throw error(404, 'Отклик не найден')
  if (!['accept', 'reject'].includes(body.decision)) throw error(400, 'Неизвестное решение')
  proposal.status = body.decision === 'accept' ? 'accepted' : 'rejected'
  proposal.comment = body.comment || ''
  proposal.decided_at = now()
  persist()
  return copy(proposal)
}

function milestone(id) {
  const proposal = state.proposals.find((item) => item.id === Number(id))
  if (!proposal) throw error(404, 'Отклик не найден')
  if (proposal.status !== 'accepted') throw error(409, 'Сначала примите отклик')
  const team = state.teams.find((item) => item.id === proposal.team.id)
  team.points += 10
  persist()
  return { proposal_id: proposal.id, team_points: team.points }
}

function aiSpec() {
  return {
    mode: 'stub', model: 'локальная заглушка',
    calls: [
      { name: 'analyze_draft', system: 'Извлеки только сведения из черновика и задай уточняющие вопросы.', input_example: { draft_text: meta.draft_examples[0].text }, output_schema: { type: 'object', required: ['card', 'questions'] } },
      { name: 'build_card', system: 'Собери карточку из черновика и ответов без новых фактов.', input_example: { answers: [] }, output_schema: { type: 'object', required: ['card', 'sources'] } },
    ],
    invalid_response: 'строгая JSON-схема → до 2 повторов → проверка цитат → локальная заглушка',
  }
}

function stats() {
  const published = state.tasks.filter((task) => task.status === 'published')
  const average = (values) => values.length ? Math.round(values.reduce((sum, value) => sum + value, 0) / values.length * 10) / 10 : 0
  const averageOrNull = (values) => values.length ? average(values) : null
  const decided = state.proposals.filter((proposal) => proposal.decided_at)
  const histories = state.tasks.filter((task) => task.history.length > 1)
  return {
    tasks: {
      total: state.tasks.length,
      published: published.length,
      avg_score: averageOrNull(published.map((task) => task.official?.score || 0)),
      avg_growth: averageOrNull(histories.map((task) => task.history.at(-1).score - task.history[0].score)),
      by_level: meta.levels.map((level) => ({ key: level.key, label: level.label, count: published.filter((task) => task.official?.level === level.key).length })),
    },
    industries: meta.industries.map((industry) => {
      const tasks = published.filter((task) => task.industry === industry)
      return { industry, tasks: tasks.length, avg_score: average(tasks.map((task) => task.official?.score || 0)), proposals: state.proposals.filter((proposal) => tasks.some((task) => task.id === proposal.task_id)).length }
    }).filter((item) => item.tasks).sort((a, b) => b.tasks - a.tasks || a.industry.localeCompare(b.industry)),
    proposals: {
      total: state.proposals.length,
      accepted: state.proposals.filter((proposal) => proposal.status === 'accepted').length,
      rejected: state.proposals.filter((proposal) => proposal.status === 'rejected').length,
      pending: state.proposals.filter((proposal) => proposal.status === 'submitted').length,
      avg_hours_to_decision: averageOrNull(decided.map((proposal) => (new Date(proposal.decided_at) - new Date(proposal.created_at)) / 3600000)),
    },
    teams: state.teams.map((team) => ({ id: team.id, name: team.name, points: team.points, proposals: state.proposals.filter((proposal) => proposal.team.id === team.id).length, accepted: state.proposals.filter((proposal) => proposal.team.id === team.id && proposal.status === 'accepted').length, skills: team.skills }))
      .sort((a, b) => b.points - a.points || b.accepted - a.accepted || b.proposals - a.proposals || a.id - b.id),
  }
}

export async function mockRequest(method, path, body) {
  if (method === 'POST') await new Promise((resolve) => setTimeout(resolve, 600))
  const url = new URL(path, 'http://mock.local')
  const route = url.pathname
  let match
  if (method === 'GET' && route === '/health') return { ok: true, db: 'ok', llm: 'stub', version: '0.2.0' }
  if (method === 'GET' && route === '/meta') return copy(meta)
  if (method === 'GET' && route === '/businesses') return copy(businesses)
  if (method === 'GET' && route === '/teams') return copy(state.teams)
  if (method === 'GET' && route === '/tasks') return state.tasks.filter((item) => item.business.id === Number(url.searchParams.get('business_id'))).sort((a, b) => b.id - a.id).map(presentTask)
  if (method === 'POST' && route === '/tasks') return createTask(body)
  if ((match = route.match(/^\/tasks\/(\d+)$/))) {
    if (method === 'GET') return presentTask(taskById(match[1]))
  }
  if ((match = route.match(/^\/tasks\/(\d+)\/answers$/)) && method === 'POST') return answerTask(match[1], body)
  if ((match = route.match(/^\/tasks\/(\d+)\/card$/)) && method === 'PUT') return updateCard(match[1], body)
  if ((match = route.match(/^\/tasks\/(\d+)\/confirm$/)) && method === 'POST') return confirmTask(match[1])
  if ((match = route.match(/^\/tasks\/(\d+)\/publish$/)) && method === 'POST') return publishTask(match[1])
  if ((match = route.match(/^\/tasks\/(\d+)\/student-check$/)) && method === 'POST') return studentCheck(match[1])
  if (method === 'POST' && route === '/rating/preview') return rate(body.card)
  if (method === 'GET' && route === '/catalog') return copy(catalog(url.searchParams.get('industry'), url.searchParams.get('level')))
  if ((match = route.match(/^\/teams\/(\d+)\/recommendations$/)) && method === 'GET') return copy(recommendations(match[1]))
  if ((match = route.match(/^\/tasks\/(\d+)\/proposals$/))) {
    if (method === 'GET') return copy(state.proposals.filter((item) => item.task_id === Number(match[1])))
    if (method === 'POST') return createProposal(match[1], body)
  }
  if ((match = route.match(/^\/teams\/(\d+)\/proposals$/)) && method === 'GET') return copy(state.proposals.filter((item) => item.team.id === Number(match[1])))
  if ((match = route.match(/^\/proposals\/(\d+)\/decision$/)) && method === 'POST') return decideProposal(match[1], body)
  if ((match = route.match(/^\/proposals\/(\d+)\/milestones$/)) && method === 'POST') return milestone(match[1])
  if (method === 'GET' && route === '/ai/spec') return aiSpec()
  if (method === 'GET' && route === '/stats') return stats()
  throw error(404, 'Маршрут не найден')
}
