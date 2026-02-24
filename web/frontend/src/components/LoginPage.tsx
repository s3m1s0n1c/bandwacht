import { FormEvent, useState } from 'react'
import { Radio } from 'lucide-react'
import { auth } from '../api/client'
import { UI } from '../utils/strings'

interface LoginPageProps {
  onLogin: (token: string) => void
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await auth.login(username, password)
      onLogin(result.access_token)
    } catch (err: any) {
      setError(UI.auth_error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen bg-sdr-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-sdr-cyan/10 mb-4">
            <Radio className="w-8 h-8 text-sdr-cyan" />
          </div>
          <h1 className="text-2xl font-bold text-sdr-text">{UI.app_title}</h1>
          <p className="text-sm text-sdr-muted mt-1">{UI.app_subtitle}</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <h2 className="text-lg font-semibold text-center">{UI.auth_login_title}</h2>

          {error && (
            <div className="text-sm text-sdr-red bg-sdr-red/10 border border-sdr-red/20 rounded-lg px-3 py-2 text-center">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm text-sdr-muted mb-1">{UI.auth_username}</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="input w-full"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="block text-sm text-sdr-muted mb-1">{UI.auth_password}</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="input w-full"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary w-full"
          >
            {loading ? UI.loading : UI.auth_login}
          </button>
        </form>
      </div>
    </div>
  )
}
