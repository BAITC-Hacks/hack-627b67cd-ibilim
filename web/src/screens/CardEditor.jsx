import { useEffect, useMemo, useState } from 'react'
import { confirmCard, previewRating, publishTask, updateCard } from '../api.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'
import RatingPanel from '../components/RatingPanel.jsx'
import RatingTimeline from '../components/RatingTimeline.jsx'

export default function CardEditor({ task, onTaskChange }) {
  const { meta } = useApp()
  const [card, setCard] = useState(task.card)
  const [rating, setRating] = useState(task.rating)
  const [activeAction, setActiveAction] = useState('')
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
    if (!hasChanges || activeAction) return
    setActiveAction('save')
    setError('')
    try {
      const result = await updateCard(task.id, changes)
      onTaskChange(result)
      setCard(result.card)
      setRating(result.rating)
    } catch (cause) {
      setError(cause.message)
    } finally {
      setActiveAction('')
    }
  }

  async function confirm() {
    if (hasChanges || activeAction) return
    setActiveAction('confirm')
    setError('')
    try { onTaskChange(await confirmCard(task.id)) }
    catch (cause) { setError(cause.message) }
    finally { setActiveAction('') }
  }

  async function publish() {
    if (!task.confirmed || hasChanges || activeAction) return
    setActiveAction('publish')
    setError('')
    try { onTaskChange(await publishTask(task.id)) }
    catch (cause) { setError(cause.message) }
    finally { setActiveAction('') }
  }

  return <section className="flow-page task-flow-page">
    <div className="task-topline"><span className="eyebrow">ЗАДАЧА №{task.id} · КАРТОЧКА</span><span className="task-status">{task.status === 'published' ? 'Опубликована' : 'Карточка собрана'}</span></div>
    <h1>{task.card.title || 'Карточка задачи'}</h1>
    <p className="flow-lead">Уточняйте поля по подсказкам рейтинга. Значок цитаты показывает исходный текст, на котором основан ответ ИИ.</p>
    <ErrorBox message={error} />
    {task.ai?.mode === 'stub' && <div className="notice-box">ИИ недоступен, работает локальная заглушка</div>}
    {!!task.ai?.warnings?.length && <div className="warning-box"><strong>Что требует проверки</strong><ul>{task.ai.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></div>}
    <div className="timeline-section"><div className="section-heading"><div><span className="section-kicker">КАК ЗАДАЧА СТАЛА ЯСНЕЕ</span><h2>Рост рейтинга</h2></div><span>История изменений</span></div><RatingTimeline history={task.history} /></div>
    <div className="task-layout"><div className="task-main">
      <div className="surface draft-card"><span className="section-kicker">ВАШ ЧЕРНОВИК · {task.industry}</span><p>{task.draft_text}</p></div>
      <div className="card-editor"><div className="section-heading"><div><span className="section-kicker">ШАГ 03 / 04</span><h2>Карточка задачи</h2></div><span>{hasChanges ? 'Есть несохранённые изменения' : 'Все изменения сохранены'}</span></div>
        <div className="card-fields">{meta?.fields?.map(({ key, label }) => <div className="surface editor-field" key={key}><div className="editor-field-heading"><label className="field-label" htmlFor={`card-${key}`}>{label}</label>{task.sources?.[key] && task.sources[key] !== 'manual' && <span className="citation-mark" title={task.sources[key]} aria-label={`Цитата: ${task.sources[key]}`}>“ <span>цитата</span></span>}</div>{key === 'title' ? <input id={`card-${key}`} className="field-control" value={card[key] || ''} onChange={(event) => setCard((current) => ({ ...current, [key]: event.target.value }))} /> : <textarea id={`card-${key}`} className="field-control" rows={3} value={card[key] || ''} onChange={(event) => setCard((current) => ({ ...current, [key]: event.target.value }))} />}</div>)}</div>
        <div className="editor-actions"><button type="button" className="primary-button" onClick={save} disabled={!hasChanges || !!activeAction}>{activeAction === 'save' ? 'Сохраняем…' : 'Сохранить изменения'}</button>{activeAction === 'save' && <Loader>Сохраняем карточку…</Loader>}</div>
      </div>
      <div className="publish-panel surface"><span className="section-kicker">ШАГ 04 / 04</span><h2>Подтвердить и опубликовать</h2><p>После подтверждения рейтинг становится официальным. Позиция опубликованной задачи в каталоге обновится.</p><div className="publish-actions"><button type="button" className="secondary-button" onClick={confirm} disabled={hasChanges || !!activeAction}>{activeAction === 'confirm' ? 'Подтверждаем…' : task.confirmed ? 'Подтвердить снова' : 'Подтвердить карточку'}</button><button type="button" className="primary-button" onClick={publish} disabled={!task.confirmed || hasChanges || !!activeAction || task.status === 'published'}>{activeAction === 'publish' ? 'Публикуем…' : task.status === 'published' ? 'Опубликована' : 'Опубликовать'}</button></div>{task.status === 'published' && <a className="text-link" href="#/catalog">Посмотреть в каталоге →</a>}</div>
    </div><div className="task-sidebar"><span className="section-kicker">ТЕКУЩИЙ РЕЙТИНГ {previewing ? '· ПЕРЕСЧИТЫВАЕМ…' : ''}</span><RatingPanel rating={rating} />{task.position && <div className="position-card surface"><span className="section-kicker">МЕСТО В КАТАЛОГЕ</span><strong>#{task.position.place} <small>из {task.position.of}</small></strong><span>{task.position.projected ? 'Если подтвердить и опубликовать' : 'Текущая позиция'}</span></div>}<div className="official-score surface"><span className="section-kicker">В КАТАЛОГЕ</span><strong>{task.official ? task.official.score : '—'}<small>{task.official ? ' / 100' : 'пока нет'}</small></strong>{task.official?.score !== rating.score && <p>Подтвердите, чтобы позиция в каталоге обновилась.</p>}</div></div></div>
  </section>
}
