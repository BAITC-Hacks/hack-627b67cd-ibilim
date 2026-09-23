export default function AiWarnings({ warnings = [] }) {
  if (!warnings.length) return null

  return <details className="ai-diagnostics">
    <summary>Детали проверки ИИ ({warnings.length})</summary>
    <p>Это технические замечания к разбору текста. Если важное сведение не попало в карточку, уточните ответ или добавьте его вручную.</p>
    <ul>{warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
  </details>
}
