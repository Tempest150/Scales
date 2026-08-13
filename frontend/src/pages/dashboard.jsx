import Table from '../components/Table';

const applications = [
  { id: 1, company: 'Google', role_title: 'Software Engineer', status: 'applied', status_changed_at: '2026-07-01T00:00:00Z' },
  { id: 2, company: 'Netflix', role_title: 'Backend Engineer', status: 'oa', status_changed_at: '2026-07-15T00:00:00Z' },
  { id: 3, company: 'Stripe', role_title: 'Frontend Engineer', status: 'interview', status_changed_at: '2026-07-28T00:00:00Z' },
  { id: 4, company: 'Amazon', role_title: 'SDE II', status: 'rejected', status_changed_at: '2026-07-20T00:00:00Z' },
  { id: 5, company: 'Datadog', role_title: 'Platform Engineer', status: 'offer', status_changed_at: '2026-08-05T00:00:00Z' },
  { id: 6, company: 'Snowflake', role_title: 'Data Engineer', status: 'ghosted', status_changed_at: '2026-06-10T00:00:00Z' },
];

function Dashboard() {
const columns = [
  { label: 'Company', property: 'company' },              // plain text, read-only by default
  { label: 'Role', property: 'role_title' },
  {
    label: 'Status',
    property: 'status',
    type: 'select',                                        // only used when editable=true
    options: ['applied', 'oa', 'interview', 'rejected', 'offer', 'ghosted'],
  },
  {
    label: 'Updated',
    property: 'status_changed_at',
    type: 'date',
    format: (d) => new Date(d).toLocaleDateString(),        // used when editable=false
  },
];
const rows = applications.map((a) => ({ id: a.id, ...a })); // every row needs an `id`

  return (
    <div>
      <h1>Dashboard</h1>
      <Table columns={columns} nodes={rows} searchable={true} />
    </div>
  );}

export default Dashboard;