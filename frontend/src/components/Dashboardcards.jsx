import { BoxArrowUpRight, Envelope } from "react-bootstrap-icons";
import "./Dashboardcards.css";
import { openUrl } from "@tauri-apps/plugin-opener";
import { parseTags } from "../hooks/util";
/* ==========================================================================
   Status → color mapping (application status)
   Uses the amber-slate palette's chart colors for visual distinction
   without introducing new hues outside the established system.
   ========================================================================== */
const STATUS_STYLES = {
  Applied: { label: "Applied", color: "var(--chart-1, #7399bf)" },
  OA: { label: "OA", color: "var(--chart-4, #e2b146)" },
  Interview: { label: "Interview", color: "var(--auth-accent, #df6035)" },
  Offer: { label: "Offer", color: "var(--chart-2, #e16f41)" },
  Rejected: { label: "Rejected", color: "var(--auth-error, #ef4444)" },
  Ghosted: { label: "Ghosted", color: "var(--auth-text-dim, #808080)" },
};
const LABELS = {
  requirements: "Requirements",
  preferred: "Preferred",
  skills: "Skills",
  technologies: "Technologies",
  certifications: "Certifications",
};
function StatusPill({ status }) {
  const meta = STATUS_STYLES[status] || {
    label: status || "Unknown",
    color: "var(--auth-text-dim)",
  };
  return (
    <span
      className="status-pill"
      style={{
        color: meta.color,
        borderColor: meta.color,
        background: `color-mix(in srgb, ${meta.color} 14%, transparent)`,
      }}
    >
      {meta.label}
    </span>
  );
}

/* ==========================================================================
   Application card
   ========================================================================== */
export function ApplicationCard({ application, onViewEmail, onCardClick }) {
  const { company, role_title, status, status_changed_at, gmail_message_id } =
    application;

  const updated =
    status_changed_at && status_changed_at !== "N/A"
      ? new Date(status_changed_at).toLocaleDateString(undefined, {
          month: "short",
          day: "numeric",
          year: "numeric",
        })
      : "N/A";

  return (
    <div
      className="panel dash-card"
      onClick={() => onCardClick?.(application)}
      style={{ cursor: onCardClick ? "pointer" : undefined }}
    >
      <div className="dash-card-top">
        <div className="dash-card-heading">
          <div className="dash-card-company">
            {company || "Unknown company"}
          </div>
          <div className="dash-card-role">
            {role_title || "Role not extracted"}
          </div>
        </div>
        <StatusPill status={status} />
        {console.log("Status changed at:", status)}
      </div>

      <div className="dash-card-footer">
        <span className="dash-card-meta">Updated / Applied {updated}</span>
        <button
          type="button"
          className="dash-card-action"
          disabled={!gmail_message_id}
          onClick={(e) => {
            e.stopPropagation();
            gmail_message_id && onViewEmail?.(gmail_message_id);
          }}
          title={gmail_message_id ? "View source email" : "No linked email"}
        >
          {gmail_message_id ? (
            <>
              <Envelope size={13} />
              View email
            </>
          ) : (
            <span className="text-muted">No email</span>
          )}
        </button>
      </div>
    </div>
  );
}

/* ==========================================================================
   Job card
   ========================================================================== */
export function JobCard({ job, onCardClick }) {
  const { job_title, apply_url, tags, summary, company_name } = job;
  const tagGroups = parseTags(tags);
  const hasTags = Object.keys(tagGroups).length > 0;

  return (
    <div
      className="panel dash-card"
      onClick={() => onCardClick?.(job)}
      style={{ cursor: onCardClick ? "pointer" : undefined }}
    >
      <div className="dash-card-top">
        <div className="dash-card-heading">
          <div className="dash-card-company">
            {company_name || "Unknown company"}
          </div>
          <div className="dash-card-role">{job_title || "Untitled role"}</div>
        </div>
      </div>

      {summary && <p className="dash-card-summary">{summary}</p>}

      {hasTags ? (
        <div className="dash-card-taglist">
          {Object.entries(tagGroups)
            .slice(0, 2)
            .map(([key, items]) => (
              <div key={key} className="dash-card-tag-group">
                <div className="dash-card-tag-label">{LABELS[key] || key}</div>
                <ul className="dash-card-tag-items">
                  {items.slice(0, 3).map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
        </div>
      ) : (
        <p className="dash-card-tag-empty">Couldn't find any tags</p>
      )}

      <div className="dash-card-footer">
        <span className="dash-card-meta" />
        <a
          className="dash-card-action"
          href={apply_url || "#"}
          aria-disabled={!apply_url}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (apply_url) openUrl(apply_url);
          }}
        >
          <BoxArrowUpRight size={13} />
          Apply
        </a>
      </div>
    </div>
  );
}

/* ==========================================================================
   Grid wrappers — drop-in replacements for a table view
   ========================================================================== */
export function ApplicationCardGrid({
  applications,
  onViewEmail,
  onCardClick,
}) {
  if (!applications?.length) {
    return (
      <div className="dash-empty">
        No applications yet — they'll show up here once emails are classified.
      </div>
    );
  }
  return (
    <div className="dash-card-grid">
      {applications.map((app) => (
        <ApplicationCard
          key={app.application_id}
          application={app}
          onViewEmail={onViewEmail}
          onCardClick={onCardClick}
        />
      ))}
    </div>
  );
}

export function JobCardGrid({ jobs, onCardClick }) {
  if (!jobs?.length) {
    return <div className="dash-empty">No enriched jobs yet.</div>;
  }
  return (
    <div className="dash-card-grid">
      {jobs.map((job) => (
        <JobCard
          key={job.apply_url || job.job_title}
          job={job}
          onCardClick={onCardClick}
        />
      ))}
    </div>
  );
}

/* ==========================================================================
   Application details — overlay modal
   ========================================================================== */
export function ApplicationDetails({ application, onClose }) {
  const { company, role_title, status, status_changed_at, sender_email } =
    application;

  return (
    <div className="details-overlay" onClick={onClose}>
      <div className="panel details-panel" onClick={(e) => e.stopPropagation()}>
        <div className="panel-header">
          <span>{company}</span>
          <button className="details-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="panel-body">
          <p>
            <strong>Role:</strong> {role_title || "N/A"}
          </p>
          <p>
            <strong>Status:</strong> {status}
          </p>
          <p>
            <strong>Last updated:</strong>{" "}
            {status_changed_at
              ? new Date(status_changed_at).toLocaleString()
              : "N/A"}
          </p>
          {sender_email && (
            <p>
              <strong>From:</strong> {sender_email}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   Job details — overlay modal
   ========================================================================== */
export function JobDetails({ job, onClose }) {
  const { job_title, company_name, apply_url, tags, summary } = job;

  const tagGroups = parseTags(tags);
  console.log("Parsed tag groups:", tagGroups);
  const hasTags = Object.keys(tagGroups).length > 0;

  return (
    <div className="details-overlay" onClick={onClose}>
      <div className="panel details-panel" onClick={(e) => e.stopPropagation()}>
        <div className="panel-header">
          <span>{job_title || "N/A"}</span>
          <button className="details-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="panel-body">
          <p>
            <strong>Company:</strong> {company_name || "N/A"}
          </p>

          {summary && <p className="details-summary">{summary}</p>}

          {hasTags ? (
            <div className="dash-card-taglist">
              {Object.entries(tagGroups).map(([key, items]) => (
                <div key={key} className="dash-card-tag-group">
                  <div className="dash-card-tag-label">
                    {LABELS[key] || key}
                  </div>
                  <ul className="dash-card-tag-items">
                    {items.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : (
            <p className="dash-card-tag-empty">Couldn't find any tags</p>
          )}

          <a
            className="dash-card-action details-apply-link"
            href={apply_url || "#"}
            target="_blank"
            rel="noreferrer"
            aria-disabled={!apply_url}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              if (apply_url) openUrl(apply_url);
            }}
          >
            <BoxArrowUpRight size={13} />
            Apply
          </a>
        </div>
      </div>
    </div>
  );
}
