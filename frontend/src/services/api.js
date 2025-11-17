import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach Authorization header if token present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers = config.headers || {};
    // Backend expects 'Token <token>' format
    config.headers["Authorization"] = `Token ${token}`;
  }
  return config;
});

// Interceptors for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.error || error.message || "An error occurred";
    return Promise.reject(new Error(message));
  }
);

// Applicants
export const applicantsAPI = {
  getAll: (params) => api.get("/applicants/", { params }),
  getById: (id) => api.get(`/applicants/${id}/`),
  create: (data) => api.post("/applicants/", data),
  bulkCreate: (data) => api.post("/applicants/bulk_create/", data),
  update: (id, data) => api.put(`/applicants/${id}/`, data),
  delete: (id) => api.delete(`/applicants/${id}/`),
};

// Interviewers
export const interviewersAPI = {
  getAll: (params) => api.get("/interviewers/", { params }),
  getById: (id) => api.get(`/interviewers/${id}/`),
  create: (data) => api.post("/interviewers/", data),
  bulkCreate: (data) => api.post("/interviewers/bulk_create/", data),
  update: (id, data) => api.put(`/interviewers/${id}/`, data),
  delete: (id) => api.delete(`/interviewers/${id}/`),
};

// Rooms
export const roomsAPI = {
  getAll: (params) => api.get("/rooms/", { params }),
  getById: (id) => api.get(`/rooms/${id}/`),
  create: (data) => api.post("/rooms/", data),
  bulkCreate: (data) => api.post("/rooms/bulk_create/", data),
  update: (id, data) => api.put(`/rooms/${id}/`, data),
  delete: (id) => api.delete(`/rooms/${id}/`),
};

// Schedules
export const schedulesAPI = {
  getAll: (params) => api.get("/schedules/", { params }),
  getById: (id) => api.get(`/schedules/${id}/`),
  getTimeline: (params) => api.get("/schedules/timeline/", { params }),
  getConflicts: () => api.get("/schedules/conflicts/"),
  create: (data) => api.post("/schedules/", data),
  update: (id, data) => api.put(`/schedules/${id}/`, data),
  delete: (id) => api.delete(`/schedules/${id}/`),
};

// Data Management
export const dataAPI = {
  importExcel: (file, sheetType, sessionId) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("type", sheetType);
    if (sessionId) formData.append("session_id", sessionId);
    return api.post("/data/import/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  exportExcel: (sessionId) =>
    api.get("/data/export/", {
      responseType: "blob",
      params: sessionId ? { session_id: sessionId } : {},
    }),
  getStatistics: (params) => api.get("/data/statistics/", { params }),
  getLogs: ({ actionType, companyId, limit } = {}) =>
    api.get("/data/logs/", {
      params: {
        ...(actionType ? { action_type: actionType } : {}),
        ...(companyId ? { company_id: companyId } : {}),
        ...(limit ? { limit } : {}),
      },
    }),
};

// Positions
export const positionsAPI = {
  getAll: () => api.get("/positions/"),
  getById: (id) => api.get(`/positions/${id}/`),
  create: (data) => api.post("/positions/", data),
  update: (id, data) => api.put(`/positions/${id}/`, data),
  delete: (id) => api.delete(`/positions/${id}/`),
};

// Interview Sessions
export const sessionsAPI = {
  getAll: (params) => api.get("/sessions/", { params }),
  getActive: () => api.get("/sessions/active/"),
  getById: (id) => api.get(`/sessions/${id}/`),
  create: (data) => api.post("/sessions/", data),
  update: (id, data) => api.put(`/sessions/${id}/`, data),
  delete: (id) => api.delete(`/sessions/${id}/`),
  activate: (id) => api.post(`/sessions/${id}/activate/`),
  updateMembership: (id, data) => api.post(`/sessions/${id}/membership/`, data),
};

// (Removed duplicate companiesAPI block; single canonical definition is below)

// Algorithms
export const algorithmsAPI = {
  runGenetic: ({ config = {}, company_id, session_id, dry_run } = {}) =>
    api.post("/algorithm/genetic/", {
      config,
      company_id,
      session_id,
      dry_run,
    }),
  runGeneticVariant: ({ config = {}, company_id, session_id, dry_run } = {}) =>
    api.post("/algorithm/genetic-variant/", {
      config,
      company_id,
      session_id,
      dry_run,
    }), // GA2
  runGeneticVariant2: ({ config = {}, company_id, session_id, dry_run } = {}) =>
    api.post("/algorithm/genetic-variant2/", {
      config,
      company_id,
      session_id,
      dry_run,
    }), // GA3
  runGeneticVariant3: ({ config = {}, company_id, session_id, dry_run } = {}) =>
    api.post("/algorithm/genetic-variant3/", {
      config,
      company_id,
      session_id,
      dry_run,
    }), // GA4
  compare: ({ config = {}, company_id, session_id } = {}) =>
    api.post("/algorithm/compare/", { config, company_id, session_id }),
  getResults: ({ company_id, session_id, top, selected } = {}) =>
    api.get("/algorithm/results/", {
      params: {
        ...(company_id ? { company_id } : {}),
        ...(session_id ? { session_id } : {}),
        ...(top ? { top } : {}),
        ...(selected !== undefined ? { selected } : {}),
      },
    }),
  chooseResult: ({ result_id, session_id, company_id }) =>
    api.post("/algorithm/select/", { result_id, session_id, company_id }),
  run: (algorithm, { config = {}, company_id, session_id, dry_run } = {}) => {
    const payload = { config, company_id, session_id, dry_run };
    const algorithmMap = {
      GA: () => api.post("/algorithm/genetic/", payload),
      GA2: () => api.post("/algorithm/genetic-variant/", payload),
      GA3: () => api.post("/algorithm/genetic-variant2/", payload),
      GA4: () => api.post("/algorithm/genetic-variant3/", payload),
    };
    return algorithmMap[algorithm]
      ? algorithmMap[algorithm]()
      : Promise.reject(new Error("Invalid algorithm type"));
  },
};

// Companies
export const companiesAPI = {
  getAll: () => api.get("/companies/"),
  getCurrent: () => api.get("/companies/current/"),
  getById: (id) => api.get(`/companies/${id}/`),
  create: (data) => api.post("/companies/", data),
  update: (id, data) => api.put(`/companies/${id}/`, data),
  delete: (id) => api.delete(`/companies/${id}/`),
};

// Algorithm Configs
export const configsAPI = {
  getAll: () => api.get("/configs/"),
  getById: (id) => api.get(`/configs/${id}/`),
  create: (data) => api.post("/configs/", data),
  update: (id, data) => api.put(`/configs/${id}/`, data),
  delete: (id) => api.delete(`/configs/${id}/`),
  activate: (id) => api.post(`/configs/${id}/activate/`),
};

// Auth
export const authAPI = {
  register: ({ username, password, company_code, company_id }) =>
    api.post("/auth/register/", {
      username,
      password,
      company_code,
      company_id,
    }),
  login: ({ username, password }) =>
    api.post("/auth/login/", { username, password }),
};

export default api;
