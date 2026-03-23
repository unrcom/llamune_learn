import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { HomePage } from '@/pages/HomePage'
import { JobsPage } from '@/pages/JobsPage'
import { JobCreatePage } from '@/pages/JobCreatePage'
import { JobDetailPage } from '@/pages/JobDetailPage'
import { LoginPage } from '@/pages/LoginPage'
import { getToken } from '@/api/client'
import { MonkeyProvider } from '@/contexts/MonkeyContext'

export default function App() {
  const [loggedIn, setLoggedIn] = useState(() => !!getToken())

  function handleLogin() {
    setLoggedIn(true)
  }

  function handleLogout() {
    setLoggedIn(false)
  }

  if (!loggedIn) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    )
  }

  return (
    <BrowserRouter>
      <MonkeyProvider>
        <Layout onLogout={handleLogout}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/poc/:pocId/jobs" element={<JobsPage />} />
            <Route path="/poc/:pocId/jobs/new" element={<JobCreatePage />} />
            <Route path="/poc/:pocId/jobs/:jobId" element={<JobDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </MonkeyProvider>
    </BrowserRouter>
  )
}
