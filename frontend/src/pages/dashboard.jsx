import Table from "../components/Table";
import Pagination from "../components/Pagination";
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

const PAGE_SIZE = 10;
const SEARCH_DEBOUNCE_MS = 350;

// Debounces a fast-changing input value; returns the settled value after
// `delay` ms of no further changes (used to avoid firing a request per keystroke).
function useDebouncedValue(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
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
  const [applicationsPage, setApplicationsPage] = useState(1);
  const [applicationsTotalPages, setApplicationsTotalPages] = useState(1);
  const [applicationsTotal, setApplicationsTotal] = useState(0);
  const [applicationsLoading, setApplicationsLoading] = useState(false);
  const [applicationsSearchInput, setApplicationsSearchInput] = useState("");
  const applicationsSearch = useDebouncedValue(
    applicationsSearchInput,
    SEARCH_DEBOUNCE_MS,
  );

  const [jobs, setJobs] = useState([]);
  const [jobsPage, setJobsPage] = useState(1);
  const [jobsTotalPages, setJobsTotalPages] = useState(1);
  const [jobsTotal, setJobsTotal] = useState(0);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsSearchInput, setJobsSearchInput] = useState("");
  const jobsSearch = useDebouncedValue(jobsSearchInput, SEARCH_DEBOUNCE_MS);

  const [selectedApplication, setSelectedApplication] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [view, setView] = useState("table"); // "table" | "cards"

  // A new search term invalidates the current page, so reset to page 1
  // up front (in the input handler, not the debounced value) rather than
  // reacting to it later — avoids a second render pass from an effect.
  const handleApplicationsSearchChange = (value) => {
    setApplicationsSearchInput(value);
    setApplicationsPage(1);
  };

  const handleJobsSearchChange = (value) => {
    setJobsSearchInput(value);
    setJobsPage(1);
  };

  useEffect(() => {
    let cancelled = false;
    async function fetchApplications() {
      setApplicationsLoading(true);
      try {
        const data = await api.getApplications({
          page: applicationsPage,
          pageSize: PAGE_SIZE,
          search: applicationsSearch,
        });
        if (cancelled) return;
        setApplications(data.applications ?? []);
        setApplicationsTotalPages(data.total_pages ?? 1);
        setApplicationsTotal(data.total ?? 0);
      } catch (error) {
        console.error("Error fetching applications:", error);
      } finally {
        if (!cancelled) setApplicationsLoading(false);
      }
    }
    fetchApplications();
    return () => {
      cancelled = true;
    };
  }, [applicationsPage, applicationsSearch]);

  useEffect(() => {
    let cancelled = false;
    async function fetchJobs() {
      setJobsLoading(true);
      try {
        const data = await api.getJobs({
          page: jobsPage,
          pageSize: PAGE_SIZE,
          search: jobsSearch,
        });
        if (cancelled) return;
        setJobs(data.jobs ?? []);
        setJobsTotalPages(data.total_pages ?? 1);
        setJobsTotal(data.total ?? 0);
      } catch (error) {
        console.error("Error fetching jobs:", error);
      } finally {
        if (!cancelled) setJobsLoading(false);
      }
    }
    fetchJobs();
    return () => {
      cancelled = true;
    };
  }, [jobsPage, jobsSearch]);

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
          <span className="dashboard-section-count">{applicationsTotal}</span>
        </div>
        <div className="panel-body">
          {view === "table" ? (
            <Table
              columns={applicationColumns}
              nodes={applicationRows}
              searchable
              searchValue={applicationsSearchInput}
              onSearchChange={handleApplicationsSearchChange}
              onRowClick={(row) => setSelectedApplication(row)}
            />
          ) : (
            <>
              <input
                type="text"
                className="search-input"
                placeholder="Search…"
                value={applicationsSearchInput}
                onChange={(e) => handleApplicationsSearchChange(e.target.value)}
              />
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
            </>
          )}
          <Pagination
            page={applicationsPage}
            totalPages={applicationsTotalPages}
            total={applicationsTotal}
            onPageChange={setApplicationsPage}
            disabled={applicationsLoading}
          />
        </div>
      </div>
      <br />
      <div className="panel dashboard-section">
        <div className="panel-header">
          Jobs
          <span className="dashboard-section-count">{jobsTotal}</span>
        </div>
        <div className="panel-body">
          {view === "table" ? (
            <Table
              columns={jobColumns}
              nodes={jobRows}
              searchable
              searchValue={jobsSearchInput}
              onSearchChange={handleJobsSearchChange}
              onRowClick={(row) => setSelectedJob(row)}
            />
          ) : (
            <>
              <input
                type="text"
                className="search-input"
                placeholder="Search…"
                value={jobsSearchInput}
                onChange={(e) => handleJobsSearchChange(e.target.value)}
              />
              <JobCardGrid jobs={jobRows} onCardClick={setSelectedJob} />
            </>
          )}
          <Pagination
            page={jobsPage}
            totalPages={jobsTotalPages}
            total={jobsTotal}
            onPageChange={setJobsPage}
            disabled={jobsLoading}
          />
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
