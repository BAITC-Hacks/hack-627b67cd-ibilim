import { useEffect, useState } from 'react'
import { getStats } from '../api.js'
import ErrorBox from '../components/ErrorBox.jsx'
import Loader from '../components/Loader.jsx'

const number = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 })
const display = (value) => value == null ? '—' : number.format(value)
const growth = (value) => value == null ? '—' : `${value > 0 ? '+' : ''}${display(value)}`

export default function ProgramStats() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setStats(null)
    setError('')
    getStats().then((result) => { if (active) setStats(result) })
      .catch((cause) => { if (active) setError(cause.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [refresh])

  const tasks = stats?.tasks
  const proposals = stats?.proposals
  const published = tasks?.published || 0

  return <section className="flow-page program-stats-page">
    <div className="stats-page-heading"><div><span className="eyebrow">AI SANA · ПАНЕЛЬ ПРОГРАММЫ</span><h1>Что происходит с задачами</h1><p className="flow-lead">Общие показатели по задачам бизнеса и откликам команд. Данные обновляются из программы без персональной информации.</p></div><button className="secondary-button" type="button" onClick={() => setRefresh((value) => value + 1)} disabled={loading}>{loading ? 'Обновляем…' : 'Обновить показатели'}</button></div>
    <ErrorBox message={error} />
    {loading && <Loader>Загружаем показатели программы…</Loader>}
    {stats && <>
      <div className="stats-overview">
        <div className="surface stats-growth"><span className="section-kicker">ЭФФЕКТ УТОЧНЕНИЯ</span><strong>{growth(tasks.avg_growth)}<small>{tasks.avg_growth == null ? '' : ' баллов'}</small></strong><p>Средний рост рейтинга задачи от черновика до последней версии.</p></div>
        <div className="surface stats-summary"><span>Всего задач</span><strong>{display(tasks.total)}</strong></div>
        <div className="surface stats-summary"><span>Опубликовано</span><strong>{display(tasks.published)}</strong></div>
        <div className="surface stats-summary"><span>Средний рейтинг опубликованных</span><strong>{display(tasks.avg_score)}<small>{tasks.avg_score == null ? '' : ' / 100'}</small></strong></div>
      </div>

      <div className="stats-panels">
        <section className="surface stats-panel"><span className="section-kicker">КАЧЕСТВО ЗАДАЧ</span><h2>Опубликованные по уровням</h2><p>Уровень определяется подтверждённым рейтингом.</p><div className="stats-level-list">{tasks.by_level?.map((level) => <div className="stats-level" key={level.key}><div><span>{level.label}</span><strong>{display(level.count)}</strong></div><progress value={level.count || 0} max={Math.max(1, published)} aria-label={`${level.label}: ${level.count} из ${published}`} /></div>)}</div>{!published && <p className="stats-empty">Опубликованных задач пока нет.</p>}</section>
        <section className="surface stats-panel"><span className="section-kicker">РАБОТА С КОМАНДАМИ</span><h2>Отклики и решения</h2><div className="stats-proposal-grid"><div><span>Всего откликов</span><strong>{display(proposals.total)}</strong></div><div><span>Ожидают решения</span><strong>{display(proposals.pending)}</strong></div><div><span>Приняты</span><strong>{display(proposals.accepted)}</strong></div><div><span>Отклонены</span><strong>{display(proposals.rejected)}</strong></div></div><p className="stats-decision-time">Среднее время до решения: <strong>{display(proposals.avg_hours_to_decision)}{proposals.avg_hours_to_decision == null ? '' : ' ч'}</strong></p></section>
      </div>

      <section className="surface stats-table-panel"><div className="stats-section-heading"><div><span className="section-kicker">НАПРАВЛЕНИЯ</span><h2>Отрасли</h2></div><span>Только опубликованные задачи</span></div>{stats.industries?.length ? <div className="stats-table-wrap"><table><thead><tr><th>Отрасль</th><th>Задачи</th><th>Средний рейтинг</th><th>Отклики</th></tr></thead><tbody>{stats.industries.map((item) => <tr key={item.industry}><th scope="row">{item.industry}</th><td>{display(item.tasks)}</td><td>{display(item.avg_score)}</td><td>{display(item.proposals)}</td></tr>)}</tbody></table></div> : <p className="stats-empty">Пока нет опубликованных задач по отраслям.</p>}</section>

      <section className="surface stats-table-panel"><div className="stats-section-heading"><div><span className="section-kicker">УЧАСТНИКИ</span><h2>Команды</h2></div><span>Баллы и участие</span></div>{stats.teams?.length ? <div className="stats-table-wrap"><table><thead><tr><th>Команда</th><th>Навыки</th><th>Отклики</th><th>Принято</th><th>Баллы</th></tr></thead><tbody>{stats.teams.map((team, index) => <tr key={team.id}><th scope="row"><span className="stats-team-rank">#{index + 1}</span>{team.name}</th><td>{team.skills?.length ? team.skills.join(' · ') : '—'}</td><td>{display(team.proposals)}</td><td>{display(team.accepted)}</td><td className="stats-team-points">{display(team.points)}</td></tr>)}</tbody></table></div> : <p className="stats-empty">Команды пока не добавлены.</p>}</section>
    </>}
  </section>
}
