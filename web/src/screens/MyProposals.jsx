import { useEffect, useState } from 'react'
import { getCatalog, getTeamProposals } from '../api.js'
import { useApp } from '../state.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'

const statuses = { submitted: 'Отправлен', accepted: 'Принят', rejected: 'Отклонён' }

export default function MyProposals() {
  const { identity, selected } = useApp()
  const [items, setItems] = useState([])
  const [taskTitles, setTaskTitles] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!identity.id) return
    let active = true
    setLoading(true)
    setError('')
    setItems([])
    setTaskTitles({})
    Promise.allSettled([getTeamProposals(identity.id), getCatalog()]).then(([proposals, catalog]) => {
      if (!active) return
      if (proposals.status === 'rejected') {
        setError(proposals.reason.message)
        return
      }
      setItems(proposals.value)
      setTaskTitles(catalog.status === 'fulfilled' ? Object.fromEntries(catalog.value.map((task) => [task.id, task.title])) : {})
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [identity.id])

  return <section className="flow-page list-page"><div className="eyebrow">ДЛЯ КОМАНД</div><h1>Мои отклики</h1><p className="flow-lead">{selected?.name} · здесь видны отправленные предложения и решения бизнеса.</p><ErrorBox message={error} />{loading ? <Loader>Загружаем отклики…</Loader> : items.length ? <div className="proposal-list">{items.map((item) => <article className="surface my-proposal" key={item.id}><div className="proposal-card-head"><div><span className="section-kicker">ЗАДАЧА №{item.task_id} · ОТКЛИК №{item.id}</span><h2><a href={`#/task/${item.task_id}`}>{taskTitles[item.task_id] || `Задача №${item.task_id}`}</a></h2></div><span className={`proposal-status status-${item.status}`}>{statuses[item.status] || item.status}</span></div><div className="proposal-detail-grid"><div><span>Идея</span><p>{item.idea}</p></div><div><span>План</span><p>{item.plan}</p></div><div><span>Срок</span><p>{item.timeline}</p></div></div>{item.comment && <div className="decision-comment"><strong>Комментарий бизнеса</strong><p>{item.comment}</p></div>}</article>)}</div> : <div className="surface empty-state">Вы пока не отправили ни одного отклика. <a className="text-link" href="#/catalog">Открыть каталог →</a></div>}</section>
}
