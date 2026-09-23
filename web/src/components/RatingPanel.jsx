import LevelBadge from './LevelBadge.jsx'
import { useApp } from '../state.js'

export default function RatingPanel({ rating, hasChanges = false }) {
  const { meta } = useApp()
  if (!rating) return null

  const topStep = rating.next_best?.[0]
  const topOutcome = !hasChanges && topStep?.then
  const levelLabel = (key) => meta?.levels?.find((level) => level.key === key)?.label || key
  const thresholds = meta?.levels?.filter((level) => level.min > 0) || []

  return <aside className="rating-panel">
    <div className="rating-score"><strong>{rating.score}</strong><span>/ 100</span></div>
    <LevelBadge level={rating.level} />
    <div className="rating-roadmap" role="img" aria-label={`Рейтинг ${rating.score} из 100; пороги уровней: ${thresholds.map((level) => `${level.min} — ${level.label}`).join(', ')}`}>
      <div className="rating-roadmap-track"><span style={{ width: `${Math.max(0, Math.min(100, rating.score))}%` }} /></div>
      <div className="rating-roadmap-labels">{thresholds.map((level) => <span key={level.key} style={{ left: `${level.min}%` }}>{level.min}<small>{level.label}</small></span>)}</div>
    </div>
    {rating.next_level && <p className="next-level-note">До уровня «{rating.next_level.label}» — ещё <strong>{rating.next_level.points_needed}</strong> баллов</p>}
    {topStep && <div className="rating-opportunity">
      <span className="section-kicker">СЛЕДУЮЩИЙ ШАГ</span>
      <strong>{topStep.label} <span>+{topStep.gain}</span></strong>
      <p>{topStep.hint}</p>
      {topOutcome && <p className="rating-opportunity-outcome">Если улучшить показатель: <b>{topOutcome.score} / 100</b> · {levelLabel(topOutcome.level)} · <b>#{topOutcome.place} из {topOutcome.of}</b>{topOutcome.teams?.length ? <> · рекомендации: {topOutcome.teams.join(', ')}</> : null}</p>}
    </div>}
    <div className="rating-breakdown">{rating.breakdown?.map((item) => <div className="rating-breakdown-item" key={item.key}>
      <div><span>{item.label}</span><strong>{item.points} / {item.max}</strong></div>
      <progress value={item.points} max={item.max} />
      <small className={`indicator-state ${item.points === item.max ? 'indicator-complete' : ''}`}>{item.points === item.max ? '✓ Полно' : item.points === 0 ? 'Пусто' : 'Можно уточнить'}</small>
      <small>{item.explain}</small>
      {item.hint && <small className="rating-hint">{item.hint}</small>}
    </div>)}</div>
    {!!rating.penalties?.length && <div className="rating-penalties"><h3>Снятые баллы</h3>{rating.penalties.map((item) => <div key={item.key}><strong>{item.label}</strong><span>−{item.points}</span><small>{item.explain}</small></div>)}</div>}
    {!!rating.next_best?.length && <div className="rating-next">
      <h3>Что поднимет рейтинг</h3>
      {hasChanges && <p className="forecast-note">Место и аудиторию пересчитаем после сохранения карточки.</p>}
      {rating.next_best.map((item) => {
        const outcome = !hasChanges && item.then
        return <div key={item.key}>
          <strong>{item.label}</strong><span>+{item.gain}</span><small>{item.hint}</small>
          {outcome && <p className="rating-outcome">Если улучшить: <b>{outcome.score} / 100</b> · {levelLabel(outcome.level)} · <b>#{outcome.place} из {outcome.of}</b>{outcome.teams?.length ? <> · рекомендации: {outcome.teams.join(', ')}</> : null}</p>}
        </div>
      })}
    </div>}
  </aside>
}
