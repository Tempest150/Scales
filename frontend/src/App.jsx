import { useEffect } from "react";
import Login from "./pages/Login";
import Register from "./pages/register";
import Dashboard from "./pages/dashboard";
import Navbar from "./components/nav";
import SyncLoader from "./components/SyncLoader";
import { Routes, Route, Navigate } from "react-router";
import { useUser } from "./hooks/UserContext";
import { useToast } from "./hooks/ToastContext";

function ProtectedApp({ user, onLogout }) {
  return (
    <>
      <Navbar user={user} onLogout={onLogout} />
      <Routes>
        <Route path="/" element={<Dashboard user={user} />} />
        <Route path="/dashboard" element={<Dashboard user={user} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

function App() {
  const { user, loading, login, logout, syncStatus } = useUser();
  const toast = useToast();

  useEffect(() => {
    if (syncStatus.status === "error") {
      toast?.showError(syncStatus.error || "Email sync failed");
    }
  }, [syncStatus.status, syncStatus.error, toast]);

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
          ) : syncStatus.status === "syncing" ? (
            <SyncLoader total={syncStatus.total} completed={syncStatus.completed} />
          ) : (
            <ProtectedApp user={user} onLogout={logout} />
          )
        }
      />
    </Routes>
  );
}

export default App;
