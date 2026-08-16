// UserContext.jsx
import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../api/client';

const UserContext = createContext(null);

const IDLE_SYNC = { status: 'idle', total: 0, completed: 0, error: null };

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true until we know login state
  const [syncStatus, setSyncStatus] = useState(IDLE_SYNC);
  const pollRef = useRef(null);

  // On mount, ask the backend "is there already a valid session cookie?"
  useEffect(() => {
    api.me()
      .then((data) => setUser(data))
      .catch(() => setUser(null)) // no valid session — that's fine, just not logged in
      .finally(() => setLoading(false));
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]); // clear interval on unmount

  const pollSyncStatus = useCallback(() => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const data = await api.syncStatus();
        setSyncStatus(data);
        if (data.status === 'done' || data.status === 'error') {
          stopPolling();
        }
      } catch {
        stopPolling(); // treat a failed poll as "stop trying, let the user in"
      }
    }, 1000);
  }, [stopPolling]);

  const login = async (email, password) => {
    const data = await api.login(email, password); // sets the cookie server-side
    setUser(data);
    setSyncStatus({ status: 'syncing', total: 0, completed: 0, error: null });
    pollSyncStatus(); // backend kicked off email classification in the background — watch it
  };

  const logout = async () => {
    stopPolling();
    await api.logout(); // clears the cookie server-side
    setUser(null);
    setSyncStatus(IDLE_SYNC);
  };

  return (
    <UserContext.Provider value={{ user, loading, login, logout, syncStatus }}>
      {children}
    </UserContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useUser = () => useContext(UserContext);