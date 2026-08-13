import { useState } from 'react';
import { api } from '../api/client';
import { useUser } from '../hooks/UserContext';
import { useNavigate } from 'react-router-dom';

export default function Register() {
  const [name, setName]         = useState('');
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const { login } = useUser();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.register(name.trim(), email.trim().toLowerCase(), password);
      // registration succeeded — now log them in so the session cookie gets set
      await login(email.trim().toLowerCase(), password);
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.eyebrow}>Personal finance</div>
        <h1 style={s.title}>Leo</h1>
        <p style={s.sub}>Create your account</p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={s.label}>Name</label>
            <input
              type="text"
              required
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={s.input}
              placeholder="Your name"
            />
          </div>

          <div>
            <label style={s.label}>Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={s.input}
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label style={s.label}>Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={s.input}
              placeholder="••••••••"
            />
          </div>

          {error && <p style={s.error}>{error}</p>}

          <button type="submit" disabled={loading} style={s.btn}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
          <p style={s.sub}>
            Already have an account? <a href="/" style={s.link}>Sign in</a>
          </p>
        </form>
      </div>
    </div>
  );
}

const s = {
  page: {
    fontFamily: "'DM Sans', 'Inter', sans-serif",
    background: '#0f0f0f',
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1.5rem',
  },
  card: {
    background: '#161616',
    border: '0.5px solid rgba(255,255,255,0.08)',
    borderRadius: 16,
    padding: '2.5rem 2rem',
    width: '100%',
    maxWidth: 380,
  },
  eyebrow: {
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: '0.14em',
    color: '#555',
    marginBottom: 6,
  },
  title: {
    fontSize: 32,
    fontWeight: 600,
    color: '#e8e6e1',
    margin: '0 0 4px',
  },
  sub: {
    fontSize: 14,
    color: '#555',
    marginBottom: '1.75rem',
  },
  label: {
    display: 'block',
    fontSize: 13,
    color: '#888',
    marginBottom: 6,
  },
  input: {
    width: '100%',
    background: '#1a1a1a',
    border: '0.5px solid rgba(255,255,255,0.1)',
    borderRadius: 8,
    color: '#e8e6e1',
    fontSize: 15,
    padding: '10px 12px',
    outline: 'none',
    fontFamily: 'inherit',
    boxSizing: 'border-box',
    transition: 'border-color 0.15s',
  },
  error: {
    fontSize: 13,
    color: '#f87171',
    background: 'rgba(248,113,113,0.08)',
    border: '0.5px solid rgba(248,113,113,0.2)',
    borderRadius: 6,
    padding: '8px 12px',
    margin: 0,
  },
  btn: {
    width: '100%',
    padding: '11px',
    borderRadius: 8,
    border: '0.5px solid rgba(74,222,128,0.4)',
    background: 'rgba(74,222,128,0.1)',
    color: '#4ade80',
    fontSize: 15,
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: 'inherit',
    marginTop: 4,
    transition: 'background 0.15s',
  },
  link: {
    color: '#4ade80',
    textDecoration: 'none',
  },
};