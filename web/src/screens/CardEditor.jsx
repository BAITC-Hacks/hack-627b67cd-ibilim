import { useEffect, useMemo, useState } from 'react'
import { previewRating, updateCard } from '../api.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'
import RatingPanel from '../components/RatingPanel.jsx'

export default function CardEditor({ task, onTaskChange }) {
  const { meta } = useApp()
  const [card, setCard] = useState(task.card)
  const [rating, setRating] = useState(task.rating)
  const [pending, setPending] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [error, setError] = useState('')
  const changes = useMemo(() => Object.fromEntries((meta?.fields || []).filter(({ key }) => card[key] !== task.card[key]).map(({ key }) => [key, card[key]])), [card, task.card, meta])
  const hasChanges = Object.keys(changes).length > 0

  useEffect(() => {
    if (!hasChanges) { setRating(task.rating); setPreviewing(false); return }
    let active = true
    const timer = setTimeout(async () => {
      setPreviewing(true)
      try {
        const result = await previewRating(card)
        if (active) setRating(result)
      } catch (cause) {
        if (active) setError(cause.message)
      } finally {
        if (active) setPreviewing(false)
      }
    }, 400)
    return () => { active = false; clearTimeout(timer) }
  }, [card, hasChanges, task.rating])

  async function save() {
    if (!hasChanges || pending) return
    setPending(true)
    setError('')
    try {
      const result = await updateCard(task.id, changes)
      onTaskChange(result)
      setCard(result.card)
      setRating(result.rating)
    } catch (cause) {
      setError(cause.message)
    } finally {
      setPending(false)
    }
  }

  return <section className="flow-page task-flow-page"><div className="task-topline"><span className="eyebrow">ЗАДАЧА №{task.id} · КАРТОЧКА</span><span className="task-status">{task.status === 'published' ? 'Опубликована' : 'Карточка собрана'}</span></div><h1>{task.card.title || 'Карточка задачи'}</h1><p className="flow-lead">Уточняйте поля по подсказкам рейтинга. Значок цитаты показывает исходный текст, на котором основан ответ ИИ.</p><ErrorBox message={error} />{task.ai?.mode === 'stub' && <div className="notice-box">ИИ недоступен, работает локальная заглушка</div>}{!!task.ai?.warnings?.length && <div className="warning-box"><strong>Что требует проверки</strong><ul>{task.ai.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></div>}<div className="task-layout"><div className="task-main"><div className="surface draft-card"><span className="section-kicker">ВАШ ЧЕРНОВИК · {task.industry}</span><p>{task.draft_text}</p></div><div className="card-editor"><div className="section-heading"><div><span className="section-kicker">ШАГ 03 / 04</span><h2>Карточка задачи</h2></div><span>{hasChanges ? 'Есть несохранённые изменения' : 'Все изменения сохранены'}</span></div><div className="card-fields">{meta?.fields?.map(({ key, label }) => <div className="surface editor-field" key={key}><div className="editor-field-heading"><label className="field-label" htmlFor={`card-${key}`}>{label}</label>{task.sources?.[key] && task.sources[key] !== 'manual' && <span className="citation-mark" title={task.sources[key]} aria-label={`Цитата: ${task.sources[key]}`}>“ <span>цитата</span></span>}</div>{key === 'title' ? <input id={`card-${key}`} className="field-control" value={card[key] || ''} onChange={(event) => setCard((current) => ({ ...current, [key]: event.target.value }))} /> : <textarea id={`card-${key}`} className="field-control" rows={3} value={card[key] || ''} onChange={(event) => setCard((current) => ({ ...current, [key]: event.target.value }))} />}</div>)}</div><div className="editor-actions"><button type="button" className="primary-button" onClick={save} disabled={!hasChanges || pending}>{pending ? 'Сохраняем…' : 'Сохранить изменения'}</button>{pending && <Loader>Сохраняем карточку…</Loader>}</div></div></div><div className="task-sidebar"><span className="section-kicker">ПРЕДПРОСМОТР РЕЙТИНГА {previewing ? '· ПЕРЕСЧИТЫВАЕМ…' : ''}</span><RatingPanel rating={rating} /></div></div></section>
}
