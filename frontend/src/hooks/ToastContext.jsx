// ToastContext.jsx
import { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);

  const showError = useCallback((message) => {
    setToast({ type: 'error', message });
    setTimeout(() => setToast(null), 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ showError }}>
      {children}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 20, right: 20,
          background: toast.type === 'error' ? 'var(--nb-red, #ff5c5c)' : 'var(--nb-lime, #b8f35b)',
          color: '#111', padding: '12px 16px', borderRadius: 0,
          border: '3px solid var(--nb-ink, #111)',
          fontFamily: 'inherit', fontSize: 14, fontWeight: 700, zIndex: 9999,
          boxShadow: '4px 4px 0 var(--nb-ink, #111)',
        }}>
          {toast.message}
        </div>
      )}
    </ToastContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => useContext(ToastContext); 