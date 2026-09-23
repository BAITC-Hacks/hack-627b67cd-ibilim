export default function RatingTimeline({ history = [] }) {
  if (!history.length) return null
  return <div className="rating-timeline">{history.map((item, index) => <div className="timeline-point" key={`${item.at}-${index}`}><strong>{item.score}</strong><span>{item.event}</span></div>)}</div>
}
