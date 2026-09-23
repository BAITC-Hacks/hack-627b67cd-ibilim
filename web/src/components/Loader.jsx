export default function Loader({ children = 'Загружаем данные…' }) {
  return <div className="loader" role="status"><span className="loader-mark" />{children}</div>
}
