import { useState } from 'react'
import { createTask } from '../api.js'
import { navigate } from '../router.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'

export default function NewTask() {
  const { identity, selected, meta } = useApp()
  const [industry, setIndustry] = useState('')
  const [draftText, setDraftText] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const industries = meta?.industries || []
  const chosenIndustry = industry || selected?.industry || industries[0] || ''

  function chooseExample(example) {
    setIndustry(example.industry)
    setDraftText(example.text)
    setError('')
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
      <select id="task-industry" className="field-control" value={chosenIndustry} onChange={(event) => setIndustry(event.target.value)} disabled={pending}>{industries.map((value) => <option key={value}>{value}</option>)}</select>
      <div className="field-heading"><label className="field-label" htmlFor="task-draft">Черновик задачи</label><span>{draftText.length} символов</span></div>
      <textarea id="task-draft" className="field-control draft-input" value={draftText} onChange={(event) => { setDraftText(event.target.value); setError('') }} placeholder="Например: хотим понимать, какие поля скоро потребуют полива…" disabled={pending} />
      <ErrorBox message={error} />
      <div className="form-actions"><button className="primary-button" type="submit" disabled={!draftText.trim() || !identity.id || pending}>{pending ? 'Разбираем черновик…' : 'Разобрать черновик'}<span aria-hidden="true">→</span></button><span>ИИ задаст минимум 3 вопроса</span></div>
      {pending && <Loader>ИИ разбирает черновик… Обычно это занимает до 20 секунд.</Loader>}
    </form><aside className="surface example-card"><div className="eyebrow">НАЧНИТЕ С ПРИМЕРА</div><h2>Достаточно одной мысли</h2><p>Можно начать с короткого описания. Недостающие детали платформа спросит на следующем шаге.</p><div className="example-list">{meta?.draft_examples?.map((example, index) => <button type="button" className="example-chip" key={`${example.industry}-${index}`} onClick={() => chooseExample(example)} disabled={pending}><span>{example.industry}</span><strong>Пример: {example.text}</strong><span aria-hidden="true">↗</span></button>)}</div></aside></div>
  </section>
}
