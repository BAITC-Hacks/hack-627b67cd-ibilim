import { useEffect, useState } from 'react'
import { getTask, submitAnswers } from '../api.js'
import { useApp } from '../state.js'
import Loader from '../components/Loader.jsx'
import ErrorBox from '../components/ErrorBox.jsx'
import RatingPanel from '../components/RatingPanel.jsx'
import PrivacyNotice from '../components/PrivacyNotice.jsx'
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
    setTask(null)
    setError('')
    getTask(id).then((value) => {
      if (!active) return
      setTask(value)
      setAnswers(Object.fromEntries((value.questions || []).map((question) => [question.id, question.answer || ''])))
    }).catch((cause) => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id])

  const questions = task?.questions || []
  const answeredCount = questions.filter((question) => (answers[question.id] || '').trim()).length
  const fieldLabel = (key) => key === 'draft' ? 'Черновик' : meta?.fields?.find((field) => field.key === key)?.label || key

  async function submit() {
    if (!task || pending) return
    setPending(true)
    setError('')
    const filled = questions.map((question) => ({ question_id: question.id, answer: (answers[question.id] || '').trim() })).filter((item) => item.answer)
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

  return <section className="flow-page task-flow-page">
    <div className="task-topline"><span className="eyebrow">ЗАДАЧА №{task.id} · УТОЧНЕНИЕ</span><span className="task-status">Ждём ответов</span></div>
    <h1>Уточним детали задачи</h1>
    <p className="flow-lead">ИИ использует только факты из вашего текста и ответов. Отвечайте на то, что уже знаете; остальные вопросы можно пропустить.</p>
    {task.ai?.mode === 'stub' && <div className="notice-box" role="status">ИИ недоступен, работает локальная заглушка</div>}
    {!!task.ai?.warnings?.length && <div className="warning-box"><strong>Что требует проверки</strong><ul>{task.ai.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></div>}
    <PrivacyNotice findings={task.privacy} fieldLabel={fieldLabel} />
    <div className="task-layout"><div className="task-main">
      <div className="surface draft-card"><span className="section-kicker">ВАШ ЧЕРНОВИК · {task.industry}</span><p>{task.draft_text}</p></div>
      <div className="questions-section" aria-busy={pending}><div className="section-heading"><div><span className="section-kicker">ШАГ 02 / 04</span><h2>Вопросы к задаче</h2></div><span>{answeredCount} из {questions.length} ответов</span></div>
        <div className="question-list">{questions.map((question, index) => { const answered = Boolean((answers[question.id] || '').trim()); return <div className={`surface question-card ${answered ? 'is-answered' : ''}`} key={question.id}><div className="question-number">{String(index + 1).padStart(2, '0')}</div><div className="question-content"><div className="question-labels"><span className="field-tag">{fieldLabel(question.field)}</span>{answered && <span className="answer-state">Ответ добавлен</span>}</div><label htmlFor={`question-${question.id}`}>{question.text}</label><textarea id={`question-${question.id}`} className="field-control" value={answers[question.id] || ''} onChange={(event) => { setAnswers((current) => ({ ...current, [question.id]: event.target.value })); setError('') }} placeholder="Ваш ответ…" rows={3} readOnly={pending} /></div></div> })}</div>
        <ErrorBox message={error} /><div className="question-actions"><button className="primary-button" type="button" onClick={submit} disabled={pending}>{pending ? 'Собираем карточку…' : 'Собрать карточку'} <span aria-hidden="true">→</span></button><span>Пустые ответы можно пропустить</span></div>{pending && <Loader>ИИ собирает карточку из черновика и ответов…</Loader>}
      </div>
    </div><div className="task-sidebar"><span className="section-kicker">ТЕКУЩИЙ РЕЙТИНГ</span><RatingPanel rating={task.rating} /><p className="rating-caption">Рейтинг растёт по мере уточнения задачи.</p>{task.position && <div className="position-card surface"><span className="section-kicker">МЕСТО В КАТАЛОГЕ</span><strong>#{task.position.place} <small>из {task.position.of}</small></strong><span>{task.position.projected ? 'Если подтвердить и опубликовать' : 'Текущая позиция'}</span></div>}{task.audience && <div className="audience-card surface"><span className="section-kicker">КОМУ ПОДОЙДЁТ ЗАДАЧА</span>{task.audience.teams?.length ? <><ul>{task.audience.teams.map((team) => <li key={team.id}><strong>{team.name}</strong><span>{team.match?.join(' · ')}</span></li>)}</ul><p>{task.audience.recommended ? 'После публикации задача сможет попасть в рекомендации этим командам.' : `Рекомендации откроются с уровня «${meta?.levels?.find((level) => level.key === 'working')?.label || 'рабочая'}». В каталоге задача будет видна и раньше.`}</p></> : <p>Совпадений с профилями команд пока нет.</p>}</div>}</div></div>
  </section>
}
