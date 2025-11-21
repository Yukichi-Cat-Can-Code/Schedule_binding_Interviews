import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

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

api.interceptors.request.use((config) => {
  try {
    const cid =
      typeof window !== "undefined"
        ? localStorage.getItem("auth_company_id")
        : null;
    if (!cid) return config;

    const method = (config.method || "get").toLowerCase();
    // Ensure params object exists
    config.params = config.params || {};

    if (method === "get" || method === "delete") {
      // Put company_id in query string to avoid CORS preflight / custom headers
      config.params = { ...config.params, company_id: cid };
    } else {
      // For POST/PUT/PATCH, if JSON body and company_id not present, add it
      const contentType =
        (config.headers &&
          (config.headers["Content-Type"] || config.headers["content-type"])) ||
        "";
      // Only auto-inject into JSON bodies. If `config.data` is FormData,
      // don't overwrite it — append the company_id field to the FormData
      // (if not already present) so file uploads are preserved.
      if (config.data instanceof FormData) {
        if (!config.data.has("company_id")) {
          config.data.append("company_id", cid);
        }
      } else if (contentType.includes("application/json")) {
        // Ensure data object for JSON payloads
        config.data = config.data || {};
        if (typeof config.data === "object" && !Array.isArray(config.data)) {
          if (!("company_id" in config.data)) {
            config.data = { ...config.data, company_id: cid };
          }
        }
      } else {
        // For other content types (e.g. form-encoded), place company_id in params if not already
        config.params = config.params || {};
        if (!config.params.company_id) config.params.company_id = cid;
      }
    }
  } catch (e) {}
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
    // Let the browser set the multipart Content-Type (with boundary).
    // Attach company_id as a query param so backend can resolve tenant without requiring
    // multipart parsing to contain it. This avoids CORS preflights and parser surprises.
    const cid =
      typeof window !== "undefined"
        ? localStorage.getItem("auth_company_id")
        : null;
    // Ensure axios does not force a JSON Content-Type for this FormData request;
    // the browser will set the correct multipart boundary header automatically.
    return api.post("/data/import/", formData, {
      params: cid ? { company_id: cid } : {},
      headers: { "Content-Type": undefined },
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

// GA Dev / Debug APIs
export const algorithmsDevAPI = {
  getLatestRun: () => api.get("/algorithm/debug/run/latest/"),
  getScheduleDetail: ({ run_id, generation, individual_id }) =>
    api.get("/algorithm/debug/schedule/", {
      params: { run_id, generation, individual_id },
    }),
  getCrossoverDetail: ({ run_id, generation, child_id }) =>
    api.get("/algorithm/debug/crossover/", {
      params: { run_id, generation, child_id },
    }),
  getLineageDetail: ({ run_id, generation, individual_id }) =>
    api.get("/algorithm/debug/lineage/", {
      params: { run_id, generation, individual_id },
    }),
};

// Companies
export const companiesAPI = {
  getAll: () => api.get("/companies/"),

  getCurrent: async () => {
    const cid =
      typeof window !== "undefined"
        ? localStorage.getItem("auth_company_id")
        : null;
    if (cid) {
      return api.get(`/companies/${encodeURIComponent(cid)}/`);
    }

    // If no local company id available, fall back to the server-resolved endpoint
    return api.get("/companies/current/");
  },
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
