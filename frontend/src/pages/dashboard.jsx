import Table from "../components/Table";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { ApplicationDetails, JobDetails } from "../components/DashboardCards";

const applicationColumns = [
  { label: "Company", property: "company" },
  { label: "Role", property: "role_title" },
  {
    label: "Status",
    property: "status",
    type: "select",
    options: ["applied", "oa", "interview", "rejected", "offer", "ghosted"],
  },
  {
    label: "Updated",
    property: "status_changed_at",
    type: "date",
    format: (d) => new Date(d).toLocaleDateString(),
  },
];

const jobColumns = [
  { label: "Company", property: "company_name" },
  { label: "Role", property: "job_title" },
  { label: "Summary", property: "summary" },
  { label: "Tags", property: "tags" },
];

function Dashboard({ user }) {
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);

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
    id: app.application_id,
    ...app,
    status_changed_at: app.status_changed_at || "N/A",
  }));

  const jobRows = jobs.map((job, i) => ({
    id: job.apply_url || `job-${i}`,
    ...job,
    tags: Array.isArray(job.tags) ? job.tags.join(", ") : job.tags || "N/A",
  }));

  return (
    <div className="dashboard-page">
      <h1 className="dashboard-title">
        Dashboard | {user?.name || user?.email}
      </h1>

      <div className="panel dashboard-section">
        <div className="panel-header">
          Applications
          <span className="dashboard-section-count">
            {applicationRows.length}
          </span>
        </div>
        <div className="panel-body">
          <Table
            columns={applicationColumns}
            nodes={applicationRows}
            searchable
            onRowClick={(row) => setSelectedApplication(row)}
          />
        </div>
      </div>
      <br/>
      <div className="panel dashboard-section">
        <div className="panel-header">
          Jobs
          <span className="dashboard-section-count">{jobRows.length}</span>
        </div>
        <div className="panel-body">
          <Table
            columns={jobColumns}
            nodes={jobRows}
            searchable
            onRowClick={(row) => setSelectedJob(row)}
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
