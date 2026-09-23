import { useEffect, useState } from 'react'
import { addMilestone, decideProposal, getTask, getTaskProposals } from '../api.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'

const statuses = { submitted: 'На рассмотрении', accepted: 'Принят', rejected: 'Отклонён' }

export default function TaskProposals({ id }) {
  const { identity } = useApp()
  const [task, setTask] = useState(null)
  const [items, setItems] = useState([])
  const [comments, setComments] = useState({})
  const [milestoneTitles, setMilestoneTitles] = useState({})
  const [milestoneResults, setMilestoneResults] = useState({})
  const [pendingId, setPendingId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    Promise.all([getTask(id), getTaskProposals(id)]).then(([nextTask, proposals]) => { if (active) { setTask(nextTask); setItems(proposals); setComments(Object.fromEntries(proposals.map((item) => [item.id, item.comment || '']))) } }).catch((cause) => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id])

  async function decide(proposalId, decision) {
    if (pendingId) return
    setPendingId(proposalId)
    setError('')
    try {
      const updated = await decideProposal(proposalId, decision, comments[proposalId]?.trim() || '')
      setItems((current) => current.map((item) => item.id === proposalId ? updated : item))
    } catch (cause) { setError(cause.message) }
    finally { setPendingId(null) }
  }

  async function confirmMilestone(proposalId) {
    const title = milestoneTitles[proposalId]?.trim()
    if (pendingId || !title) return
    setPendingId(proposalId)
    setError('')
    try {
      const result = await addMilestone(proposalId, title)
      setMilestoneResults((current) => ({ ...current, [proposalId]: { title, points: result.team_points } }))
      setMilestoneTitles((current) => ({ ...current, [proposalId]: '' }))
    } catch (cause) { setError(cause.message) }
    finally { setPendingId(null) }
  }

  if (loading) return <Loader>Загружаем отклики…</Loader>
  if (!task) return <ErrorBox message={error || 'Задача не найдена'} />
  if (identity.role !== 'business' || task.business?.id !== identity.id) return <ErrorBox message="Отклики доступны бизнесу, который создал задачу." />

  return <section className="flow-page list-page"><div className="eyebrow">ЗАДАЧА №{id} · РЕШЕНИЕ БИЗНЕСА</div><h1>Предложения команд</h1><p className="flow-lead">{task.card?.title || task.draft_text}. Сравните идеи, планы и сроки, затем выберите вручную. Можно принять несколько предложений или ни одного.</p><a className="text-link back-link" href={`#/task/${id}`}>← Вернуться к карточке</a><ErrorBox message={error} />{items.length ? <div className="business-proposals">{items.map((item) => <article key={item.id} className="surface proposal-compare"><div className="proposal-card-head"><div><span className="section-kicker">ОТКЛИК №{item.id}</span><h2>{item.team?.name}</h2></div><span className={`proposal-status status-${item.status}`}>{statuses[item.status] || item.status}</span></div><div className="team-tags">{item.team?.skills?.map((skill) => <span key={`skill-${skill}`}>{skill}</span>)}{item.team?.technologies?.map((technology) => <span key={`tech-${technology}`}>{technology}</span>)}</div><div className="proposal-section-line"><span>Идея</span><p>{item.idea}</p></div><div className="proposal-section-line"><span>План</span><p>{item.plan}</p></div><div className="proposal-section-line"><span>Срок</span><p>{item.timeline}</p></div><div className="proposal-section-line"><span>Ссылка</span><a href={item.link} target="_blank" rel="noreferrer">{item.link}</a></div><label className="field-label" htmlFor={`decision-${item.id}`}>Комментарий команде (необязательно)</label><textarea id={`decision-${item.id}`} className="field-control" rows={3} value={comments[item.id] || ''} onChange={(event) => setComments((current) => ({ ...current, [item.id]: event.target.value }))} disabled={!!pendingId} /><div className="decision-actions"><button type="button" className="primary-button" onClick={() => decide(item.id, 'accept')} disabled={!!pendingId}>{pendingId === item.id ? 'Сохраняем…' : 'Выбрать'}</button><button type="button" className="secondary-button" onClick={() => decide(item.id, 'reject')} disabled={!!pendingId}>Отклонить</button></div>{item.status === 'accepted' && <div className="milestone-confirm"><span className="section-kicker">ФАКТИЧЕСКИЙ ПРОГРЕСС</span><h3>Подтвердить этап работы</h3><p>Когда команда покажет результат этапа, укажите его название и подтвердите. Команда получит 10 баллов.</p><label className="field-label" htmlFor={`milestone-${item.id}`}>Выполненный этап</label><input id={`milestone-${item.id}`} className="field-control" value={milestoneTitles[item.id] || ''} onChange={(event) => setMilestoneTitles((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Например, прототип показан бизнесу" disabled={!!pendingId} /><button type="button" className="secondary-button" onClick={() => confirmMilestone(item.id)} disabled={!!pendingId || !milestoneTitles[item.id]?.trim()}>{pendingId === item.id ? 'Подтверждаем…' : 'Подтвердить этап · +10 баллов'}</button>{milestoneResults[item.id] && <p className="milestone-result" role="status">Этап «{milestoneResults[item.id].title}» подтверждён. У команды теперь {milestoneResults[item.id].points} баллов. <a href="#/stats">Открыть панель программы →</a></p>}</div>}</article>)}</div> : <div className="surface empty-state">Пока нет откликов на эту задачу.</div>}</section>
}
