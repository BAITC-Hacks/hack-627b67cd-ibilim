import LevelBadge from './LevelBadge.jsx'

export default function RatingPanel({ rating }) {
  if (!rating) return null
  return <aside className="rating-panel"><div className="rating-score"><strong>{rating.score}</strong><span>/ 100</span></div><LevelBadge level={rating.level} />{rating.next_level && <p className="next-level-note">До уровня «{rating.next_level.label}» — ещё <strong>{rating.next_level.points_needed}</strong> баллов</p>}<div className="rating-breakdown">{rating.breakdown?.map((item) => <div className="rating-breakdown-item" key={item.key}><div><span>{item.label}</span><strong>{item.points} / {item.max}</strong></div><progress value={item.points} max={item.max} /><small>{item.explain}</small>{item.hint && <small className="rating-hint">{item.hint}</small>}</div>)}</div>{!!rating.next_best?.length && <div className="rating-next"><h3>Что поднимет рейтинг</h3>{rating.next_best.map((item) => <div key={item.key}><strong>{item.label}</strong><span>+{item.gain}</span><small>{item.hint}</small></div>)}</div>}</aside>
}
