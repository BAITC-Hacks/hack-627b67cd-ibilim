import { useApp } from '../state.js'
import { navigate } from '../router.js'

export default function RoleSwitch() {
  const { identity, setIdentity, businesses, teams } = useApp()
  const accounts = identity.role === 'business' ? businesses : teams

  function changeRole(role) {
    if (role === identity.role) return
    setIdentity(role)
    navigate(role === 'business' ? '/new' : '/catalog')
  }

  return <div className="identity-control">
    <div className="role-tabs" role="group" aria-label="Выберите роль">
      <button type="button" className={identity.role === 'business' ? 'active' : ''} aria-pressed={identity.role === 'business'} onClick={() => changeRole('business')}>Бизнес</button>
      <button type="button" className={identity.role === 'team' ? 'active' : ''} aria-pressed={identity.role === 'team'} onClick={() => changeRole('team')}>Команда</button>
    </div>
    <label className="account-select"><span className="sr-only">Выберите участника</span>
      <select value={identity.id ?? ''} disabled={!accounts.length} onChange={(event) => setIdentity(identity.role, Number(event.target.value))}>
        {!accounts.length && <option value="">Загружаем…</option>}
        {accounts.map((account) => <option value={account.id} key={account.id}>{account.name}</option>)}
      </select>
    </label>
  </div>
}
