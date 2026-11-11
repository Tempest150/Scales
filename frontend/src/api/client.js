const API_BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

// [{ property, order }] (primary first) -> "status:asc,company:desc"
const serializeSort = (sort) =>
  sort.map(({ property, order }) => `${property}:${order}`).join(",");

export const api = {
  // Auth
  login(email, password) {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  logout() {
    return request("/auth/logout", { method: "POST" });
  },

  register(name, email, password) {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    });
  },
  
  me() {
    return request("/auth/me");
  },

  // Emails
  syncStatus() {
    return request("/emails/sync-status");
  },

  dashboardFill() {
    return request("/application/dashboard");
  },

  getApplications({
    page = 1,
    pageSize = 10,
    search = "",
    status = "",
    sort = [],
  } = {}) {
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    if (sort.length) params.set("sort", serializeSort(sort));
    return request(`/application/applications?${params.toString()}`);
  },

  getJobs({ page = 1, pageSize = 10, search = "", sort = [] } = {}) {
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (search) params.set("search", search);
    if (sort.length) params.set("sort", serializeSort(sort));
    return request(`/application/jobs?${params.toString()}`);
  },
};
