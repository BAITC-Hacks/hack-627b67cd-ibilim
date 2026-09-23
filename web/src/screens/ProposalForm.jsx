import { useEffect, useState } from 'react'
import { createProposal, getTask } from '../api.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'
import RatingPanel from '../components/RatingPanel.jsx'

export default function ProposalForm({ id }) {
  const { identity, meta } = useApp()
  const [task, setTask] = useState(null)
  const [form, setForm] = useState({ idea: '', plan: '', timeline: '', link: '' })
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    setSubmitted(false)
    getTask(id).then((value) => { if (active) setTask(value) }).catch((cause) => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id])

  function update(key, value) { setForm((current) => ({ ...current, [key]: value })); setError('') }
  async function submit(event) {
    event.preventDefault()
    if (pending) return
    if (!form.idea.trim() || !form.plan.trim() || !form.timeline.trim() || !/^https?:\/\//i.test(form.link.trim())) {
      setError('Заполните идею, план, срок и ссылку, начинающуюся с http:// или https://')
      return
    }
    setPending(true)
    setError('')
    try {
      await createProposal(task.id, { teamId: identity.id, ...Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim()])) })
      setSubmitted(true)
    } catch (cause) { setError(cause.message) }
    finally { setPending(false) }
  }

  if (loading) return <Loader>Загружаем задачу…</Loader>
  if (!task) return <ErrorBox message={error || 'Задача не найдена'} />
  if (task.status !== 'published') return <ErrorBox message="Задача ещё не опубликована" />

  return <section className="flow-page proposal-page"><div className="eyebrow">ЗАДАЧА №{task.id} · ДЛЯ КОМАНД</div><h1>{task.card.title || 'Задача бизнеса'}</h1><p className="flow-lead">{task.business?.name} · {task.industry}</p><div className="task-layout"><div className="task-main"><div className="surface task-readonly"><span className="section-kicker">О ЗАДАЧЕ</span><p className="readonly-draft">{task.draft_text}</p><div className="readonly-fields">{meta?.fields?.filter(({ key }) => task.card?.[key]).map(({ key, label }) => <div key={key}><span>{label}</span><p>{task.card[key]}</p></div>)}</div></div>
      <div className="proposal-section surface"><span className="section-kicker">ВАШ ОТКЛИК</span><h2>Предложить решение</h2>{submitted ? <div className="success-state"><strong>Отклик отправлен</strong><p>Бизнес увидит вашу идею и сам примет решение.</p><a className="text-link" href="#/my-proposals">Посмотреть мои отклики →</a></div> : <form onSubmit={submit}><label className="field-label" htmlFor="proposal-idea">Идея</label><textarea id="proposal-idea" className="field-control" rows={4} value={form.idea} onChange={(event) => update('idea', event.target.value)} placeholder="Как вы решите задачу?" disabled={pending} /><label className="field-label" htmlFor="proposal-plan">План</label><textarea id="proposal-plan" className="field-control" rows={4} value={form.plan} onChange={(event) => update('plan', event.target.value)} placeholder="Основные шаги работы" disabled={pending} /><div className="proposal-pair"><div><label className="field-label" htmlFor="proposal-timeline">Срок</label><input id="proposal-timeline" className="field-control" value={form.timeline} onChange={(event) => update('timeline', event.target.value)} placeholder="Например: 2 недели" disabled={pending} /></div><div><label className="field-label" htmlFor="proposal-link">Ссылка</label><input id="proposal-link" className="field-control" type="url" value={form.link} onChange={(event) => update('link', event.target.value)} placeholder="https://…" disabled={pending} /></div></div><ErrorBox message={error} /><button className="primary-button" type="submit" disabled={pending || !identity.id}>{pending ? 'Отправляем…' : 'Отправить отклик'} <span aria-hidden="true">→</span></button></form>}</div>
    </div><div className="task-sidebar"><span className="section-kicker">РЕЙТИНГ ЗАДАЧИ</span><RatingPanel rating={task.rating} />{task.position && <div className="position-card surface"><span className="section-kicker">МЕСТО В КАТАЛОГЕ</span><strong>#{task.position.place} <small>из {task.position.of}</small></strong></div>}</div></div></section>
}
