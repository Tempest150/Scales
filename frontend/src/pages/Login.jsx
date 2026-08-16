import { useState } from "react";
import { Google } from "react-bootstrap-icons";
// api import no longer needed here — the context owns the login call now
import { useTheme } from "../hooks/ThemeContext";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onLogin(email.trim().toLowerCase(), password);
      // no need to do anything else here — UserContext updates `user` state,
      // App.jsx re-renders into ProtectedApp automatically
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`auth-page ${theme === "light" ? "auth-page--light" : ""}`}>
      <button type="button" className="auth-theme-toggle" onClick={toggleTheme}>
        {theme === "dark" ? "Light background" : "Dark background"}
      </button>
      <div className="auth-card">
        <div className="auth-image-col">
          <img
            src="https://mdbcdn.b-cdn.net/img/Photos/new-templates/bootstrap-login-form/draw2.svg"
            alt="Login illustration"
            className="auth-image"
          />
        </div>

        <div className="auth-form-col">
          <div className="auth-eyebrow">Job Application System</div>
          <h1 className="auth-title">Scales</h1>
          <p className="auth-sub">Sign in to your account</p>

          <form onSubmit={handleSubmit} className="auth-form">
            <div>
              <label className="auth-label">Email</label>
              <input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="auth-label">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
                placeholder="••••••••"
              />
            </div>

            <div className="auth-remember-row">
              <label className="auth-checkbox-label">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="auth-checkbox"
                />
                Remember me
              </label>
              <a href="#" className="auth-link">
                Forgot password?
              </a>
            </div>

            {error && <p className="auth-error">{error}</p>}

            <button type="submit" disabled={loading} className="auth-btn">
              {loading ? "Signing in…" : "Sign in"}
            </button>

            <div className="auth-divider">
              <span className="auth-divider-line" />
              <span className="auth-divider-text">OR</span>
              <span className="auth-divider-line" />
            </div>

            <button type="button" disabled className="auth-social-btn">
              <Google /> Continue with Google
            </button>

            <p className="auth-sub">
              Don't have an account?{" "}
              <a href="/register" className="auth-link">
                Register
              </a>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
