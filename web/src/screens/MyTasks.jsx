import { useEffect, useState } from 'react'
import { getBusinessTasks } from '../api.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'
import LevelBadge from '../components/LevelBadge.jsx'

const statuses = { new: 'Ждёт ответов', card: 'Карточка', published: 'Опубликована' }

export default function MyTasks() {
  const { identity, selected } = useApp()
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!identity.id) return
    let active = true
    setLoading(true)
    setError('')
    getBusinessTasks(identity.id).then((items) => { if (active) setTasks(items) }).catch((cause) => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [identity.id])

  return <section className="flow-page list-page"><div className="eyebrow">КАБИНЕТ БИЗНЕСА</div><h1>Мои задачи</h1><p className="flow-lead">{selected?.name} · черновики, карточки и предложения команд в одном месте.</p><ErrorBox message={error} />{loading ? <Loader>Загружаем задачи…</Loader> : tasks.length ? <div className="business-task-list">{tasks.map((task) => <article className="surface business-task" key={task.id}><div className="business-task-main"><div className="business-task-top"><span className="section-kicker">ЗАДАЧА №{task.id} · {task.industry}</span><span className={`task-status ${task.status === 'published' ? 'status-published' : ''}`}>{statuses[task.status] || task.status}</span></div><h2><a href={`#/task/${task.id}`}>{task.card?.title || task.draft_text}</a></h2><p>{task.draft_text}</p><div className="business-task-actions"><a className="text-link" href={`#/task/${task.id}`}>{task.status === 'new' ? 'Ответить на вопросы' : 'Открыть карточку'} →</a>{task.status === 'published' && <a className="text-link" href={`#/task/${task.id}/proposals`}>Отклики ({task.proposals}) →</a>}</div></div><div className="business-task-score"><strong>{task.rating?.score ?? 0}<small> / 100</small></strong><LevelBadge level={task.rating?.level} />{task.position && <span>#{task.position.place} из {task.position.of}{task.position.projected ? ' · прогноз' : ''}</span>}</div></article>)}</div> : <div className="surface empty-state">Пока нет задач. <a className="text-link" href="#/new">Создать первую →</a></div>}</section>
}
