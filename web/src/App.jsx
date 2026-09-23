import { useEffect } from 'react'
import { useApp } from './state.js'
import { navigate, useRoute } from './router.js'
import RoleSwitch from './components/RoleSwitch.jsx'
import Loader from './components/Loader.jsx'
import ErrorBox from './components/ErrorBox.jsx'
import PagePlaceholder from './components/PagePlaceholder.jsx'
import NewTask from './screens/NewTask.jsx'
import Clarify from './screens/Clarify.jsx'
import MyTasks from './screens/MyTasks.jsx'
import TaskProposals from './screens/TaskProposals.jsx'
import Catalog from './screens/Catalog.jsx'
import ProposalForm from './screens/ProposalForm.jsx'
import MyProposals from './screens/MyProposals.jsx'
import AiSpec from './screens/AiSpec.jsx'
import ProgramStats from './screens/ProgramStats.jsx'

function screen(route, role) {
  switch (route.name) {
    case 'new': return <NewTask />
    case 'my-tasks': return <MyTasks />
    case 'catalog': return <Catalog />
    case 'my-proposals': return <MyProposals />
    case 'ai': return <AiSpec />
    case 'stats': return <ProgramStats />
    case 'task': return role === 'team' ? <ProposalForm id={route.id} /> : <Clarify id={route.id} />
    case 'task-proposals': return <TaskProposals id={route.id} />
    default: return <PagePlaceholder eyebrow="НАВИГАЦИЯ" title="Раздел не найден" description="Выберите раздел в меню, чтобы продолжить." />
  }
}

export default function App() {
  const { identity, selected, loading, backendDown, error, useMocks } = useApp()
  const route = useRoute()

  useEffect(() => {
    if (!window.location.hash) navigate(identity.role === 'team' ? '/catalog' : '/new')
  }, [identity.role])

  const links = identity.role === 'business'
    ? [{ to: '#/new', label: 'Новая задача', name: 'new' }, { to: '#/my-tasks', label: 'Мои задачи', name: 'my-tasks' }]
    : [{ to: '#/catalog', label: 'Каталог', name: 'catalog' }, { to: '#/my-proposals', label: 'Мои отклики', name: 'my-proposals' }]
  links.push({ to: '#/stats', label: 'Панель программы', name: 'stats' })
  links.push({ to: '#/ai', label: 'Как работает ИИ', name: 'ai' })

  return <div className="app-shell">
    <header className="site-header">
      <div className="header-main container">
        <a className="brand" href={identity.role === 'team' ? '#/catalog' : '#/new'} aria-label="Challenge Hub — главная"><span className="brand-icon">CH<span>.</span></span><span className="brand-name">Challenge Hub<small>AI SANA</small></span></a>
        <div className="header-context"><span className="context-dot" /> Практические задачи для команд</div>
        <RoleSwitch />
      </div>
    </header>
    <nav className="main-nav" aria-label="Разделы"><div className="container nav-content">{links.map((item) => <a key={item.name} href={item.to} className={route.name === item.name ? 'active' : ''} aria-current={route.name === item.name ? 'page' : undefined}>{item.label}</a>)}</div></nav>
    <main className="container main-content">
      <div className="context-line"><span>{identity.role === 'business' ? 'Кабинет бизнеса' : 'Кабинет команды'}</span><span className="context-divider">/</span><strong>{selected?.name || 'Выберите участника'}</strong></div>
      {useMocks && <div className="demo-banner"><strong>Демо-режим</strong><span>Данные и действия сохраняются в этом браузере для сквозного сценария.</span></div>}
      {backendDown && !useMocks && <div className="offline-banner" role="alert"><strong>Бэкенд не отвечает</strong><span>Проверьте запуск сервера на порту 8000 и обновите страницу.</span></div>}
      <ErrorBox message={error} />
      {loading ? <Loader /> : screen(route, identity.role)}
    </main>
    <footer className="site-footer"><div className="container footer-content"><div><strong>Challenge Hub</strong><span>От ясной задачи к выбранной команде.</span></div><span>AI Sana · HackAlem 2026</span></div></footer>
  </div>
}
