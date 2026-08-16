import { useTheme } from "../hooks/ThemeContext";

export default function SyncLoader({ total, completed }) {
  const { theme } = useTheme();
  const hasTotal = total > 0;
  const pct = hasTotal ? Math.round((completed / total) * 100) : 0;

  return (
    <div className={`auth-page ${theme === "light" ? "auth-page--light" : ""}`}>
      <div className="sync-loader-card">
        <div className="sync-spinner" />
        <h2 className="sync-loader-title">Syncing your inbox</h2>
        <p className="sync-loader-sub">
          {hasTotal
            ? `Classifying ${completed} of ${total} emails…`
            : "Checking for new emails…"}
        </p>
        {hasTotal && (
          <div className="sync-progress-track">
            <div className="sync-progress-fill" style={{ width: `${pct}%` }} />
          </div>
        )}
      </div>
    </div>
  );
}
