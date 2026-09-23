export default function ErrorBox({ message }) {
  return message ? <div className="error-box" role="alert">{message}</div> : null
}
