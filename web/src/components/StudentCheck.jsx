import { useState } from 'react'
import { checkTaskAsStudent } from '../api.js'
import { useApp } from '../state.js'
import ErrorBox from './ErrorBox.jsx'
import Loader from './Loader.jsx'

export default function StudentCheck({ taskId, hasChanges, onFocusField }) {
  const { meta } = useApp()
  const [result, setResult] = useState(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const fieldLabel = (key) => meta?.fields?.find((field) => field.key === key)?.label || key

  async function run() {
    if (pending || hasChanges) return
    setPending(true)
    setError('')
    setResult(null)
    try {
      setResult(await checkTaskAsStudent(taskId))
    } catch (cause) {
      setError(cause.message)
    } finally {
      setPending(false)
    }
  }

  return <section className="student-check surface" aria-busy={pending}>
    <span className="section-kicker">ПРОВЕРКА ГЛАЗАМИ СТУДЕНТА</span>
    <h2>Сможет ли команда начать?</h2>
    <p>ИИ пробует составить план первой недели по сохранённой карточке и показывает места, где ему пришлось делать допущения. Проверка ничего не сохраняет.</p>
    <button className="secondary-button" type="button" onClick={run} disabled={pending || hasChanges}>{pending ? 'Проверяем…' : result ? 'Проверить ещё раз' : 'Проверить карточку'}</button>
    {hasChanges && <p className="student-check-help">Сначала сохраните изменения карточки.</p>}
    {pending && <Loader>ИИ смотрит на задачу глазами студента…</Loader>}
    <ErrorBox message={error} />
    {!hasChanges && result && <div className="student-check-result" role="status">
      <strong className={result.can_start ? 'check-ready' : 'check-needs-work'}>{result.can_start ? 'Команда может начать' : 'Команде нужны уточнения'}</strong>
      {result.ai?.mode === 'stub' && <p className="student-check-help">ИИ недоступен, проверены только пустые поля.</p>}
      {!!result.ai?.warnings?.length && <ul className="student-check-warnings">{result.ai.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>}
      {!!result.first_week?.length && <div><h3>План первой недели</h3><ol>{result.first_week.map((step, index) => <li key={index}>{step}</li>)}</ol></div>}
      {!!result.assumptions?.length && <div><h3>Что пришлось предположить</h3><ul className="student-assumptions">{result.assumptions.map((item, index) => <li key={`${item.field}-${index}`}><span className="field-tag">{fieldLabel(item.field)}</span><p>{item.assumption}</p><strong>{item.question}</strong>{meta?.fields?.some((field) => field.key === item.field) && <button type="button" onClick={() => onFocusField(item.field)}>Уточнить в карточке →</button>}</li>)}</ul></div>}
    </div>}
  </section>
}
