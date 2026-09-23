export default function PrivacyNotice({ findings = [], fieldLabel }) {
  if (!findings.length) return null

  return <section className="privacy-notice" role="alert">
    <div className="privacy-notice-heading"><span aria-hidden="true">!</span><div><strong>Проверьте данные перед публикацией</strong><p>Платформа обнаружила упоминания персональных данных в тексте задачи.</p></div></div>
    <ul>{findings.map((item, index) => <li key={`${item.kind}-${item.field}-${index}`}><span>{fieldLabel(item.field)}</span><div><strong>{item.message}</strong>{item.hint && <p>{item.hint}</p>}</div></li>)}</ul>
  </section>
}
