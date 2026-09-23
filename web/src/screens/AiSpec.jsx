import { useEffect, useState } from 'react'
import { getAiSpec } from '../api.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'

export default function AiSpec() {
  const [spec, setSpec] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getAiSpec().then((value) => { if (active) setSpec(value) }).catch((cause) => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  return <section className="flow-page ai-page"><div className="eyebrow">ПРОЗРАЧНОСТЬ ПЛАТФОРМЫ</div><h1>Как работает ИИ</h1><p className="flow-lead">ИИ превращает черновик в вопросы и карточку. Рейтинг считает код по фиксированным показателям, а каждое заполненное ИИ поле связано с цитатой из вашего текста.</p><ErrorBox message={error} />{loading ? <Loader>Загружаем схему ИИ…</Loader> : spec && <><div className="ai-mode surface"><div><span className="section-kicker">ТЕКУЩИЙ РЕЖИМ</span><strong>{spec.mode === 'stub' ? 'Локальная заглушка' : 'Языковая модель'}</strong></div><div><span className="section-kicker">МОДЕЛЬ</span><strong>{spec.model}</strong></div></div><div className="ai-calls">{spec.calls?.map((call, index) => <article className="surface ai-call" key={`${call.name}-${index}`}><div className="ai-call-heading"><span className="question-number">{String(index + 1).padStart(2, '0')}</span><div><span className="section-kicker">ВЫЗОВ МОДЕЛИ</span><h2>{call.name}</h2></div></div><div className="ai-call-grid"><div><h3>Системный промпт</h3><pre>{call.system}</pre></div><div><h3>Пример входа</h3><pre>{JSON.stringify(call.input_example, null, 2)}</pre></div><div><h3>JSON-схема выхода</h3><pre>{JSON.stringify(call.output_schema, null, 2)}</pre></div></div></article>)}</div><div className="surface invalid-response"><span className="section-kicker">КОНТРОЛЬ КАЧЕСТВА</span><h2>Обработка некорректного ответа</h2><p>{spec.invalid_response}</p></div></>}</section>
}
