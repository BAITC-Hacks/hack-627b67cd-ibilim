import { useEffect, useState } from 'react'
import { getTask, submitAnswers } from '../api.js'
import { useApp } from '../state.js'
import Loader from '../components/Loader.jsx'
import ErrorBox from '../components/ErrorBox.jsx'
import RatingPanel from '../components/RatingPanel.jsx'
import CardEditor from './CardEditor.jsx'

export default function Clarify({ id }) {
  const { meta } = useApp()
  const [task, setTask] = useState(null)
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    getTask(id).then((value) => {
      if (!active) return
      setTask(value)
      setAnswers(Object.fromEntries((value.questions || []).map((question) => [question.id, question.answer || ''])))
    }).catch((cause) => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id])

  async function submit() {
    if (!task || pending) return
    setPending(true)
    setError('')
    const filled = (task.questions || []).map((question) => ({ question_id: question.id, answer: (answers[question.id] || '').trim() })).filter((item) => item.answer)
    try {
      setTask(await submitAnswers(task.id, filled))
    } catch (cause) {
      setError(cause.message)
    } finally {
      setPending(false)
    }
  }

  if (loading) return <Loader>Загружаем задачу…</Loader>
  if (!task) return <ErrorBox message={error || 'Задача не найдена'} />
  if (task.status !== 'new') return <CardEditor task={task} onTaskChange={setTask} />
  const fieldLabel = (key) => meta?.fields?.find((field) => field.key === key)?.label || key

  return <section className="flow-page task-flow-page">
    <div className="task-topline"><span className="eyebrow">ЗАДАЧА №{task.id} · УТОЧНЕНИЕ</span><span className="task-status">{task.status === 'new' ? 'Ждём ответов' : task.status === 'card' ? 'Карточка собрана' : 'Опубликована'}</span></div>
    <h1>{task.status === 'new' ? 'Уточним детали задачи' : task.card?.title || 'Карточка задачи'}</h1>
    <p className="flow-lead">ИИ использует только факты из вашего текста и ответов. Дополните то, чего пока не хватает для команды.</p>
    <ErrorBox message={error} />
    {task.ai?.mode === 'stub' && <div className="notice-box" role="status">ИИ недоступен, работает локальная заглушка</div>}
    {!!task.ai?.warnings?.length && <div className="warning-box"><strong>Что требует проверки</strong><ul>{task.ai.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></div>}
    <div className="task-layout"><div className="task-main">
      <div className="surface draft-card"><span className="section-kicker">ВАШ ЧЕРНОВИК · {task.industry}</span><p>{task.draft_text}</p></div>
      {task.status === 'new' && <div className="questions-section"><div className="section-heading"><div><span className="section-kicker">ШАГ 02 / 04</span><h2>Вопросы к задаче</h2></div><span>{task.questions?.length || 0} вопросов</span></div><div className="question-list">{task.questions?.map((question, index) => <div className="surface question-card" key={question.id}><div className="question-number">{String(index + 1).padStart(2, '0')}</div><div className="question-content"><span className="field-tag">{fieldLabel(question.field)}</span><label htmlFor={`question-${question.id}`}>{question.text}</label><textarea id={`question-${question.id}`} className="field-control" value={answers[question.id] || ''} onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))} placeholder="Ваш ответ…" rows={3} disabled={pending} /></div></div>)}</div><div className="question-actions"><button className="primary-button" type="button" onClick={submit} disabled={pending}>{pending ? 'Собираем карточку…' : 'Собрать карточку'} <span aria-hidden="true">→</span></button><span>Пустые ответы можно пропустить</span></div>{pending && <Loader>ИИ собирает карточку из черновика и ответов…</Loader>}</div>}
    </div><div className="task-sidebar"><span className="section-kicker">ТЕКУЩИЙ РЕЙТИНГ</span><RatingPanel rating={task.rating} /><p className="rating-caption">Рейтинг растёт по мере уточнения задачи.</p></div></div>
  </section>
}
