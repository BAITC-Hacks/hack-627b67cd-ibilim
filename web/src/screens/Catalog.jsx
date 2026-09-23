import { useEffect, useState } from 'react'
import { getCatalog, getRecommendations } from '../api.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'
import LevelBadge from '../components/LevelBadge.jsx'

const proposalPlural = new Intl.PluralRules('ru-RU')
const proposalCount = (count) => `${count} ${({ one: 'отклик', few: 'отклика', many: 'откликов', other: 'отклика' })[proposalPlural.select(count)]}`

export default function Catalog() {
  const { identity, meta } = useApp()
  const [industry, setIndustry] = useState('')
  const [level, setLevel] = useState('')
  const [tasks, setTasks] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    getCatalog({ industry, level }).then((items) => { if (active) setTasks(items) }).catch((cause) => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [industry, level])

  useEffect(() => {
    if (!identity.id) return
    let active = true
    getRecommendations(identity.id).then((items) => { if (active) setRecommendations(items) }).catch((cause) => { if (active) setError(cause.message) })
    return () => { active = false }
  }, [identity.id])

  return <section className="flow-page catalog-page"><div className="eyebrow">ДЛЯ КОМАНД · ОТКРЫТЫЕ ЗАДАЧИ</div><h1>Каталог задач</h1><p className="flow-lead">Выберите задачу, где ваша команда может предложить решение. Рейтинг помогает увидеть, насколько подробно бизнес описал ожидания.</p>
    {!!recommendations.length && <section className="recommendations surface"><div className="section-heading"><div><span className="section-kicker">ПОДСКАЗКА ДЛЯ ВАШЕЙ КОМАНДЫ</span><h2>Рекомендуем вам</h2></div></div><div className="recommendation-list">{recommendations.map((item) => <a key={item.task_id} href={`#/task/${item.task_id}`} className="recommendation-item"><strong>{item.title}</strong><span>{item.score} / 100</span><div>{item.match?.map((word) => <em key={word}>{word}</em>)}</div></a>)}</div></section>}
    <div className="catalog-toolbar"><div><span className="section-kicker">ОБЩИЙ КАТАЛОГ</span><h2>Все задачи <small>{loading ? '' : tasks.length}</small></h2></div><div className="catalog-filters"><label>Отрасль<select className="field-control" value={industry} onChange={(event) => setIndustry(event.target.value)}><option value="">Все отрасли</option>{meta?.industries?.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><label>Уровень<select className="field-control" value={level} onChange={(event) => setLevel(event.target.value)}><option value="">Все уровни</option>{meta?.levels?.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label></div></div>
    <ErrorBox message={error} />{loading ? <Loader>Загружаем каталог…</Loader> : tasks.length ? <div className="catalog-list">{tasks.map((task, index) => <a key={task.id} href={`#/task/${task.id}`} className={`catalog-item surface ${task.highlight ? 'catalog-highlight' : ''}`}><div className="catalog-rank">#{index + 1}</div><div className="catalog-body"><div className="catalog-meta">{task.industry}<span>·</span>{task.business}</div><h3>{task.title}</h3><p>{task.summary}</p><div className="catalog-tags">{task.needs_clarification && <span className="needs-clarification">Требует уточнения</span>}<span>{proposalCount(task.proposals)}</span></div></div><div className="catalog-score"><strong>{task.score}</strong><small>/ 100</small><LevelBadge level={task.level} /></div></a>)}</div> : <div className="surface empty-state">По выбранным фильтрам задач пока нет. Попробуйте другой уровень или отрасль.</div>}
  </section>
}
