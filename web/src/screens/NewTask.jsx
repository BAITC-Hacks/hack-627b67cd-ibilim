import { useRef, useState } from 'react'
import { createTask } from '../api.js'
import { navigate } from '../router.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'

export default function NewTask() {
  const { identity, selected, meta } = useApp()
  const [industryChoice, setIndustryChoice] = useState(null)
  const [draftText, setDraftText] = useState('')
  const [showAllExamples, setShowAllExamples] = useState(false)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const draftRef = useRef(null)
  const industries = meta?.industries || []
  const examples = meta?.draft_examples || []
  const chosenIndustry = industryChoice?.businessId === identity.id
    ? industryChoice.value
    : selected?.industry || industries[0] || ''

  function chooseExample(example) {
    setIndustryChoice({ businessId: identity.id, value: example.industry })
    setDraftText(example.text)
    setError('')
    draftRef.current?.focus()
  }

  async function submit(event) {
    event.preventDefault()
    if (!draftText.trim() || !identity.id || pending) return
    setPending(true)
    setError('')
    try {
      const task = await createTask({ businessId: identity.id, industry: chosenIndustry, draftText: draftText.trim() })
      navigate(`/task/${task.id}`)
    } catch (cause) {
      setError(cause.message)
    } finally {
      setPending(false)
    }
  }

  return <section className="flow-page new-task-page">
    <div className="flow-intro"><div className="eyebrow">ДЛЯ БИЗНЕСА · ШАГ 01 / 04</div><h1>Опишите задачу своими словами</h1><p>Расскажите, что происходит сейчас и что хотите изменить. ИИ выделит факты, покажет первые баллы и задаст уточняющие вопросы.</p></div>
    <div className="form-layout"><form className="surface form-card" onSubmit={submit}>
      <label className="field-label" htmlFor="task-industry">Отрасль</label>
      <select id="task-industry" className="field-control" value={chosenIndustry} onChange={(event) => { setIndustryChoice({ businessId: identity.id, value: event.target.value }); setError('') }} disabled={pending}>{industries.map((value) => <option key={value}>{value}</option>)}</select>
      <div className="field-heading"><label className="field-label" htmlFor="task-draft">Черновик задачи</label><span>{draftText.length} символов</span></div>
      <textarea id="task-draft" ref={draftRef} className="field-control draft-input" value={draftText} onChange={(event) => { setDraftText(event.target.value); setError('') }} placeholder="Например: хотим понимать, какие поля скоро потребуют полива…" readOnly={pending} />
      <ErrorBox message={error} />
      <div className="form-actions"><button className="primary-button" type="submit" disabled={!draftText.trim() || !identity.id || pending}>{pending ? 'Разбираем черновик…' : 'Разобрать черновик'}<span aria-hidden="true">→</span></button><span>ИИ задаст минимум 3 вопроса</span></div>
      {pending && <Loader>ИИ разбирает черновик… Обычно это занимает до 20 секунд.</Loader>}
    </form><aside className="surface example-card"><div className="eyebrow">НАЧНИТЕ С ПРИМЕРА</div><h2>Достаточно одной мысли</h2><p>Можно начать с короткого описания. Недостающие детали платформа спросит на следующем шаге.</p><div className="example-list">{(showAllExamples ? examples : examples.slice(0, 3)).map((example, index) => {
      const chosen = draftText === example.text && chosenIndustry === example.industry
      return <button type="button" className={`example-chip ${chosen ? 'is-selected' : ''}`} aria-pressed={chosen} key={`${example.industry}-${index}`} onClick={() => chooseExample(example)} disabled={pending}><span>{example.industry}</span><strong>Пример: {example.text}</strong><span className="example-action">{chosen ? 'Выбрано' : 'Подставить'}</span></button>
    })}</div>{examples.length > 3 && <button type="button" className="example-more" onClick={() => setShowAllExamples((current) => !current)} aria-expanded={showAllExamples}>{showAllExamples ? 'Скрыть примеры' : `Показать ещё ${examples.length - 3}`}</button>}</aside></div>
  </section>
}
