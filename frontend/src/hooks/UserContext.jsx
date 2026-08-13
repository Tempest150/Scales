// UserContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true until we know login state

  // On mount, ask the backend "is there already a valid session cookie?"
  useEffect(() => {
    api.me()
      .then((data) => setUser(data))
      .catch(() => setUser(null)) // no valid session — that's fine, just not logged in
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const data = await api.login(email, password); // sets the cookie server-side
    setUser(data);
  };

  const logout = async () => {
    await api.logout(); // clears the cookie server-side
    setUser(null);
  };

  return (
    <UserContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </UserContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useUser = () => useContext(UserContext);