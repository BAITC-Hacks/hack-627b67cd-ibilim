import { useEffect, useState } from 'react'
import { decideProposal, getTask, getTaskProposals } from '../api.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'

const statuses = { submitted: 'На рассмотрении', accepted: 'Принят', rejected: 'Отклонён' }

export default function TaskProposals({ id }) {
  const [task, setTask] = useState(null)
  const [items, setItems] = useState([])
  const [comments, setComments] = useState({})
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

  if (loading) return <Loader>Загружаем отклики…</Loader>
  return <section className="flow-page list-page"><div className="eyebrow">ЗАДАЧА №{id} · РЕШЕНИЕ БИЗНЕСА</div><h1>Предложения команд</h1><p className="flow-lead">{task?.card?.title || task?.draft_text}. Сравните идеи, планы и сроки, затем выберите вручную. Можно принять несколько предложений или ни одного.</p><a className="text-link back-link" href={`#/task/${id}`}>← Вернуться к карточке</a><ErrorBox message={error} />{items.length ? <div className="business-proposals">{items.map((item) => <article key={item.id} className="surface proposal-compare"><div className="proposal-card-head"><div><span className="section-kicker">ОТКЛИК №{item.id}</span><h2>{item.team?.name}</h2></div><span className={`proposal-status status-${item.status}`}>{statuses[item.status] || item.status}</span></div><div className="team-tags">{item.team?.skills?.map((skill) => <span key={`skill-${skill}`}>{skill}</span>)}{item.team?.technologies?.map((technology) => <span key={`tech-${technology}`}>{technology}</span>)}</div><div className="proposal-section-line"><span>Идея</span><p>{item.idea}</p></div><div className="proposal-section-line"><span>План</span><p>{item.plan}</p></div><div className="proposal-section-line"><span>Срок</span><p>{item.timeline}</p></div><div className="proposal-section-line"><span>Ссылка</span><a href={item.link} target="_blank" rel="noreferrer">{item.link}</a></div><label className="field-label" htmlFor={`decision-${item.id}`}>Комментарий команде (необязательно)</label><textarea id={`decision-${item.id}`} className="field-control" rows={3} value={comments[item.id] || ''} onChange={(event) => setComments((current) => ({ ...current, [item.id]: event.target.value }))} disabled={pendingId === item.id} /><div className="decision-actions"><button type="button" className="primary-button" onClick={() => decide(item.id, 'accept')} disabled={!!pendingId}>{pendingId === item.id ? 'Сохраняем…' : 'Выбрать'}</button><button type="button" className="secondary-button" onClick={() => decide(item.id, 'reject')} disabled={!!pendingId}>Отклонить</button></div></article>)}</div> : <div className="surface empty-state">Пока нет откликов на эту задачу.</div>}</section>
}
