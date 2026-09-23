import React from 'react'
import { createRoot } from 'react-dom/client'
import { AppProvider } from './state.js'
import App from './App.jsx'
import './styles.css'
import './flow.css'

createRoot(document.getElementById('root')).render(
  <AppProvider><App /></AppProvider>,
)
