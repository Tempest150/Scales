import Table from "../components/Table";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import {
  ApplicationDetails,
  JobDetails,
  ApplicationCardGrid,
  JobCardGrid,
} from "../components/DashboardCards";
import { titleCase } from "../hooks/util";
import { GridFill, ListUl } from "react-bootstrap-icons";
import { openUrl } from "@tauri-apps/plugin-opener";
const applicationColumns = [
  { label: "Company", property: "company" },
  { label: "Role", property: "role_title" },
  {
    label: "Status",
    property: "status",
    type: "select",
    options: ["Applied", "OA", "Interview", "Rejected", "Offer", "Ghosted"],
  },
  {
    label: "Updated / Applied",
    property: "status_changed_at",
    type: "date",
    format: (d) => new Date(d).toLocaleDateString(),
  },
  {
    label: "Email",
    property: "gmail_message_id",
    type: "link",
    format: (messageId) =>
      messageId ? (
        <a
          href={`https://mail.google.com/mail/u/0/#all/${messageId}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            openUrl(`https://mail.google.com/mail/u/0/#all/${messageId}`);
          }}
        >
          View Email
        </a>
      ) : (
        <span className="text-muted">—</span>
      ),
  },
];

const jobColumns = [
  { label: "Company", property: "company_name" },
  { label: "Role", property: "job_title" },
  { label: "Summary", property: "summary" },
  {
    label: "Job Link",
    property: "apply_url",
    type: "link",
    format: (url) => (
      <a
        href={url || "#"}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (url) openUrl(url);
        }}
      >
        Apply
      </a>
    ),
  },
];

function Dashboard({ user }) {
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [view, setView] = useState("table"); // "table" | "cards"

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.dashboardFill();
        setApplications(data.applications ?? []);
        setJobs(data.jobs ?? []);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      }
    }
    fetchData();
  }, []);

  const applicationRows = applications.map((app) => ({
    ...app,
    id: app.application_id,

    role_title: app.role_title || "N/A",
    status: titleCase(app.status || "N/A"),
    status_changed_at: app.status_changed_at || "N/A",
    gmail_message_id: app.gmail_message_id || null,
  }));

  const jobRows = jobs.map((job, i) => ({
    ...job,
    id: job.apply_url || `job-${i}`,
    summary: job.summary || "N/A",
    job_title: job.job_title || "N/A",
    company_name: job.company_name || "N/A",
  }));
  return (
    <div className="dashboard-page">
      <h1 className="dashboard-title">
        Dashboard | {user?.name || user?.email}
      </h1>

      <div className="dashboard-view-toggle">
        <button
          type="button"
          className={view === "table" ? "active" : ""}
          onClick={() => setView("table")}
          title="Table view"
          aria-label="Table view"
        >
          <ListUl size={15} />
        </button>
        <button
          type="button"
          className={view === "cards" ? "active" : ""}
          onClick={() => setView("cards")}
          title="Card view"
          aria-label="Card view"
        >
          <GridFill size={15} />
        </button>
      </div>

      <div className="panel dashboard-section">
        <div className="panel-header">
          Applications
          <span className="dashboard-section-count">
            {applicationRows.length}
          </span>
        </div>
        <div className="panel-body">
          {view === "table" ? (
            <Table
              columns={applicationColumns}
              nodes={applicationRows}
              searchable
              onRowClick={(row) => setSelectedApplication(row)}
            />
          ) : (
            <ApplicationCardGrid
              applications={applicationRows}
              onCardClick={setSelectedApplication}
              onViewEmail={(gmail_message_id) => {
                if (gmail_message_id) {
                  openUrl(
                    `https://mail.google.com/mail/u/0/#all/${gmail_message_id}`,
                  );
                }
              }}
            />
          )}
        </div>
      </div>
      <br />
      <div className="panel dashboard-section">
        <div className="panel-header">
          Jobs
          <span className="dashboard-section-count">{jobRows.length}</span>
        </div>
        <div className="panel-body">
          {view === "table" ? (
            <Table
              columns={jobColumns}
              nodes={jobRows}
              searchable
              onRowClick={(row) => setSelectedJob(row)}
            />
          ) : (
            <JobCardGrid jobs={jobRows} onCardClick={setSelectedJob} />
          )}
        </div>
      </div>

      {selectedApplication && (
        <ApplicationDetails
          application={selectedApplication}
          onClose={() => setSelectedApplication(null)}
        />
      )}
      {selectedJob && (
        <JobDetails job={selectedJob} onClose={() => setSelectedJob(null)} />
      )}
    </div>
  );
}

export default Dashboard;
