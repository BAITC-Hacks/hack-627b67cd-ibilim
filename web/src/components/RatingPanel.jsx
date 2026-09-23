import LevelBadge from './LevelBadge.jsx'

export default function RatingPanel({ rating }) {
  if (!rating) return null
  return <aside className="rating-panel"><div className="rating-score"><strong>{rating.score}</strong><span>/ 100</span></div><LevelBadge level={rating.level} /><div className="rating-breakdown">{rating.breakdown?.map((item) => <div key={item.key}><div><span>{item.label}</span><strong>{item.points} / {item.max}</strong></div><progress value={item.points} max={item.max} /><small>{item.explain}</small></div>)}</div></aside>
}
