import { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Gallery from './pages/Gallery'
import { apiFetch } from './lib/api'

function AccessControl({ onLogin, error, submitting }) {
  const [password, setPassword] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    await onLogin(password)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-black/35 border border-white/20 rounded-3xl p-8 shadow-xl"
      >
        <h1 className="text-3xl font-bold text-white m-0 mb-3">Photobooth Access</h1>
        <p className="text-white/70 m-0 mb-6">Enter the API password to continue.</p>

        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full rounded-2xl border border-white/20 bg-white/10 px-4 py-3 text-white placeholder:text-white/50 focus:outline-none focus:border-white/50"
          placeholder="Password"
          autoFocus
          required
        />

        {error && (
          <p className="text-[#ff9ea8] mt-3 mb-0 text-sm">{error}</p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="mt-5 w-full rounded-2xl bg-[#e94560] text-white font-semibold py-3 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {submitting ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}

function App() {
  const [authState, setAuthState] = useState('checking')
  const [authError, setAuthError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const checkAuth = useCallback(async () => {
    try {
      const response = await apiFetch('/api/auth/status')
      if (!response.ok) {
        setAuthState('locked')
        return
      }

      const data = await response.json()
      setAuthState(data.authenticated ? 'ready' : 'locked')
      setAuthError('')
    } catch (error) {
      setAuthState('locked')
      setAuthError('Unable to reach the server.')
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = useCallback(async (password) => {
    setSubmitting(true)
    setAuthError('')

    try {
      const response = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      const data = await response.json()

      if (!response.ok) {
        setAuthError(data.message || 'Authentication failed.')
        return
      }

      setAuthState('ready')
    } catch (error) {
      setAuthError('Unable to reach the server.')
    } finally {
      setSubmitting(false)
    }
  }, [])

  if (authState === 'checking') {
    return (
      <div className="min-h-screen flex items-center justify-center text-white/80 text-xl">
        Checking access...
      </div>
    )
  }

  if (authState !== 'ready') {
    return <AccessControl onLogin={login} error={authError} submitting={submitting} />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/gallery" element={<Gallery />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
