const contactPattern = /https?:\/\/[^\s<>"']+|www\.[^\s<>"']+|(?:t\.me|telegram\.me)\/[^\s<>"']+|mailto:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|@[A-Z0-9_]{5,32}/gi

function linkFor(token) {
  if (token.startsWith('@')) return `https://t.me/${token.slice(1)}`
  if (/^mailto:/i.test(token)) return token
  if (/^[A-Z0-9._%+-]+@/i.test(token)) return `mailto:${token}`
  const address = /^https?:\/\//i.test(token) ? token : `https://${token}`
  try {
    const url = new URL(address)
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : null
  } catch {
    return null
  }
}

export default function ContactLinks({ value = '' }) {
  const parts = []
  let cursor = 0

  for (const match of value.matchAll(contactPattern)) {
    if (match.index > cursor) parts.push(value.slice(cursor, match.index))
    const token = match[0].replace(/[.,;!?:)]+$/, '')
    const href = linkFor(token)
    parts.push(href ? <a key={match.index} href={href} target={href.startsWith('mailto:') ? undefined : '_blank'} rel={href.startsWith('mailto:') ? undefined : 'noopener noreferrer'}>{token}</a> : token)
    cursor = match.index + token.length
  }

  if (cursor < value.length) parts.push(value.slice(cursor))
  return <>{parts}</>
}
