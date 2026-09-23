import { useApp } from '../state.js'

export default function LevelBadge({ level }) {
  const { meta } = useApp()
  const label = meta?.levels.find((item) => item.key === level)?.label || level
  return <span className={`level-badge level-${level}`}>{label}</span>
}
