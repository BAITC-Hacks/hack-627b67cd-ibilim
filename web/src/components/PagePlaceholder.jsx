export default function PagePlaceholder({ eyebrow, title, description }) {
  return <section className="page-placeholder"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p><div className="placeholder-card"><span className="placeholder-icon" aria-hidden="true">↗</span><div><strong>Экран подключается</strong><span>Каркас навигации готов. Следующий шаг добавит данные и действия.</span></div></div></section>
}
