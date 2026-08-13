import Login from "./pages/Login";
import Register from "./pages/register";
import Dashboard from "./pages/dashboard";
import Navbar from "./components/nav";
import { Routes, Route, Navigate } from "react-router";
import { useUser } from "./hooks/UserContext";

function ProtectedApp({ user, onLogout }) {
  return (
    <>
      <Navbar user={user} onLogout={onLogout} />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

function App() {
  const { user, loading, login, logout } = useUser();

  return (
    <Routes>
      <Route path="/register" element={<Register />} />
      <Route
        path="/*"
        element={
          loading ? (
            <div>Loading...</div>
          ) : !user ? (
            <Login onLogin={login} />
          ) : (
            <ProtectedApp user={user} onLogout={logout} />
          )
        }
      />
    </Routes>
  );
}

export default App;