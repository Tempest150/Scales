import { useState } from "react";
import { api } from "../api/client";
import { useUser } from "../hooks/UserContext";
import { useNavigate } from "react-router-dom";
import { Google } from "react-bootstrap-icons";
import { useTheme } from "../hooks/ThemeContext";
export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
    const { theme, toggleTheme } = useTheme();

  const { login } = useUser();
  const navigate = useNavigate();


  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.register(name.trim(), email.trim().toLowerCase(), password);
      // registration succeeded — now log them in so the session cookie gets set
      await login(email.trim().toLowerCase(), password);
      navigate("/");
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
            alt="Register illustration"
            className="auth-image"
          />
        </div>

        <div className="auth-form-col">
          <div className="auth-eyebrow">Job Application System</div>
          <h1 className="auth-title">Scales</h1>
          <p className="auth-sub">Create your account</p>

          <form onSubmit={handleSubmit} className="auth-form">
            <div>
              <label className="auth-label">Name</label>
              <input
                type="text"
                required
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="auth-input"
                placeholder="Your name"
              />
            </div>

            <div>
              <label className="auth-label">Email</label>
              <input
                type="email"
                required
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
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
                placeholder="••••••••"
              />
            </div>

            {error && <p className="auth-error">{error}</p>}

            <button type="submit" disabled={loading} className="auth-btn">
              {loading ? "Creating account…" : "Create account"}
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
              Already have an account?{" "}
              <a href="/" className="auth-link">
                Sign in
              </a>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
