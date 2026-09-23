export default function RatingTimeline({ history = [] }) {
  if (!history.length) return null
  const labels = { draft: 'Черновик', answers: 'Ответы', edit: 'Правка', confirm: 'Подтверждение' }
  return <div className="rating-timeline" aria-label="История рейтинга">{history.map((item, index) => <div className="timeline-point" key={`${item.at}-${index}`}><span className="timeline-step">{String(index + 1).padStart(2, '0')}</span><strong>{item.score}<small> / 100</small></strong><span>{labels[item.event] || item.event}</span></div>)}</div>
}
