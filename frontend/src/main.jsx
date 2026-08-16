// main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './responsive.css'
import {UserProvider} from './hooks/UserContext.jsx'
import { ToastProvider } from './hooks/ToastContext.jsx'
import { ThemeProvider } from './hooks/ThemeContext.jsx'
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <UserProvider>
      <ToastProvider>
        <BrowserRouter>
        <ThemeProvider>
          <App />
        </ThemeProvider>
        </BrowserRouter>
      </ToastProvider>
    </UserProvider>
  </React.StrictMode>,
)