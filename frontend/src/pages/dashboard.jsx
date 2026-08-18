import Table from "../components/Table";

const applications = [
  {
    id: 1,
    company: "Google",
    role_title: "Software Engineer",
    status: "applied",
    status_changed_at: "2026-07-01T00:00:00Z",
  },
  {
    id: 2,
    company: "Netflix",
    role_title: "Backend Engineer",
    status: "oa",
    status_changed_at: "2026-07-15T00:00:00Z",
  },
  {
    id: 3,
    company: "Stripe",
    role_title: "Frontend Engineer",
    status: "interview",
    status_changed_at: "2026-07-28T00:00:00Z",
  },
  {
    id: 4,
    company: "Amazon",
    role_title: "SDE II",
    status: "rejected",
    status_changed_at: "2026-07-20T00:00:00Z",
  },
  {
    id: 5,
    company: "Datadog",
    role_title: "Platform Engineer",
    status: "offer",
    status_changed_at: "2026-08-05T00:00:00Z",
  },
  {
    id: 6,
    company: "Snowflake",
    role_title: "Data Engineer",
    status: "ghosted",
    status_changed_at: "2026-06-10T00:00:00Z",
  },
];

const jobs = [
  {
    id: 1,
    company: "Figma",
    role_title: "Frontend Engineer",
    location: "Remote",
    status: "new",
    posted_at: "2026-08-14T00:00:00Z",
  },
  {
    id: 2,
    company: "Anthropic",
    role_title: "Full Stack Engineer",
    location: "San Francisco, CA",
    status: "saved",
    posted_at: "2026-08-12T00:00:00Z",
  },
  {
    id: 3,
    company: "Vercel",
    role_title: "Software Engineer",
    location: "Remote",
    status: "new",
    posted_at: "2026-08-10T00:00:00Z",
  },
  {
    id: 4,
    company: "Shopify",
    role_title: "Platform Engineer",
    location: "Toronto, ON",
    status: "dismissed",
    posted_at: "2026-08-02T00:00:00Z",
  },
];

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
  { label: "Company", property: "company" },
  { label: "Role", property: "role_title" },
  { label: "Location", property: "location" },
  {
    label: "Status",
    property: "status",
    type: "select",
    options: ["new", "saved", "applied", "dismissed"],
  },
  {
    label: "Posted",
    property: "posted_at",
    type: "date",
    format: (d) => new Date(d).toLocaleDateString(),
  },
];

function Dashboard( { user }) {
  const applicationRows = applications.map((a) => ({ id: a.id, ...a }));
  const jobRows = jobs.map((j) => ({ id: j.id, ...j }));

  return (
    <div className="dashboard-page">
      <h1 className="dashboard-title">Dashboard | {user?.name || user?.email}</h1>

      <div className="dashboard-sections">
        <div className="panel dashboard-section">
          <div className="panel-header">
            Applications
            <span className="dashboard-section-count">{applicationRows.length}</span>
          </div>
          <div className="panel-body">
            <Table columns={applicationColumns} nodes={applicationRows} searchable />
          </div>
        </div>

        <div className="panel dashboard-section">
          <div className="panel-header">
            Jobs
            <span className="dashboard-section-count">{jobRows.length}</span>
          </div>
          <div className="panel-body">
            <Table columns={jobColumns} nodes={jobRows} searchable />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
