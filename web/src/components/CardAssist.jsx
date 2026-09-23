import { useState } from 'react'
import { assistCard, updateCard } from '../api.js'
import ErrorBox from './ErrorBox.jsx'
import Loader from './Loader.jsx'

const pointPlural = new Intl.PluralRules('ru-RU')
const pointsLabel = (value) => ({ one: 'балл', few: 'балла', many: 'баллов', other: 'балла' })[pointPlural.select(value)]

export default function CardAssist({ task, hasChanges, busy, onBusyChange, onApplied }) {
  const [result, setResult] = useState(null)
  const [revision, setRevision] = useState(null)
  const [hadSuggestions, setHadSuggestions] = useState(false)
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState('')
  const [error, setError] = useState('')
  const stale = result && revision !== (task.history?.length || 0)
  const locked = hasChanges || busy || loading || !!applying

  async function suggest() {
    if (locked) return
    setLoading(true)
    onBusyChange(true)
    setError('')
    try {
      const response = await assistCard(task.id)
      setResult(response)
      setRevision(task.history?.length || 0)
      setHadSuggestions(Boolean(response.suggestions?.length))
    } catch (cause) {
      setError(cause.message)
    } finally {
      setLoading(false)
      onBusyChange(false)
    }
  }

  async function apply(suggestion) {
    if (locked || stale) return
    setApplying(suggestion.field)
    onBusyChange(true)
    setError('')
    try {
      const updated = await updateCard(task.id, { [suggestion.field]: suggestion.value })
      setResult((current) => ({ ...current, suggestions: current.suggestions.filter((item) => item.field !== suggestion.field) }))
      onApplied(updated, suggestion.field)
    } catch (cause) {
      setError(cause.message)
    } finally {
      setApplying('')
      onBusyChange(false)
    }
  }

  function hide(field) {
    setResult((current) => ({ ...current, suggestions: current.suggestions.filter((item) => item.field !== field) }))
  }

  return <section className="card-assist surface" aria-busy={loading || !!applying}>
    <span className="section-kicker">ПОМОЩЬ В ПОДГОТОВКЕ ЗАДАЧИ</span>
    <h2>Помощник: дописать карточку</h2>
    <p>Собирает текст только из того, что вы уже написали. Ничего не сохраняет без вашего согласия.</p>
    <button type="button" className="secondary-button" onClick={suggest} disabled={locked}>{loading ? 'Подбираем…' : result ? 'Предложить ещё раз' : 'Предложить формулировки'}</button>
    {hasChanges && <p className="assist-help">Сохраните правки, чтобы помощник видел актуальную карточку.</p>}
    {loading && <Loader>Помощник подбирает формулировки…</Loader>}
    <ErrorBox message={error} />
    {stale && <p className="assist-stale">Баллы посчитаны до последнего изменения. Запросите новые формулировки.</p>}
    {!!result?.suggestions?.length && <div className="assist-suggestions">{result.suggestions.map((item) => <article className="assist-suggestion" key={item.field}>
      <div className="assist-suggestion-heading"><span className="field-tag">{item.label}</span><strong>+{item.gain} {pointsLabel(item.gain)} <small>· рейтинг станет {item.then_score}</small></strong></div>
      {item.current && <p className="assist-current"><span>Сейчас:</span> <del>{item.current}</del></p>}
      <p className="assist-value">{item.value}</p>
      <p className="assist-source">Источник: «{item.quote}»</p>
      <div className="assist-actions"><button type="button" className="primary-button" onClick={() => apply(item)} disabled={locked || stale}>{applying === item.field ? 'Применяем…' : 'Применить'}</button><button type="button" className="secondary-button" onClick={() => hide(item.field)} disabled={locked}>Скрыть</button></div>
    </article>)}</div>}
    {result && !result.suggestions?.length && <p className="assist-empty">{hadSuggestions ? 'Предложения обработаны. Можно запросить новые формулировки.' : result.ai?.mode === 'stub' ? result.ai.warnings?.join(' ') || 'Помощник работает только с ИИ.' : 'Слабых мест, которые можно закрыть вашими же словами, нет. Допишите поля по подсказкам рейтинга.'}</p>}
    {!!result?.suggestions?.length && !!result.ai?.warnings?.length && <details className="assist-warnings"><summary>Что отброшено проверкой</summary><ul>{result.ai.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></details>}
  </section>
}
