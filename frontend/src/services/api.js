import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
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
  getAll: () => api.get("/applicants/"),
  getById: (id) => api.get(`/applicants/${id}/`),
  create: (data) => api.post("/applicants/", data),
  bulkCreate: (data) => api.post("/applicants/bulk_create/", data),
  update: (id, data) => api.put(`/applicants/${id}/`, data),
  delete: (id) => api.delete(`/applicants/${id}/`),
};

// Interviewers
export const interviewersAPI = {
  getAll: () => api.get("/interviewers/"),
  getById: (id) => api.get(`/interviewers/${id}/`),
  create: (data) => api.post("/interviewers/", data),
  bulkCreate: (data) => api.post("/interviewers/bulk_create/", data),
  update: (id, data) => api.put(`/interviewers/${id}/`, data),
  delete: (id) => api.delete(`/interviewers/${id}/`),
};

// Rooms
export const roomsAPI = {
  getAll: () => api.get("/rooms/"),
  getById: (id) => api.get(`/rooms/${id}/`),
  create: (data) => api.post("/rooms/", data),
  bulkCreate: (data) => api.post("/rooms/bulk_create/", data),
  update: (id, data) => api.put(`/rooms/${id}/`, data),
  delete: (id) => api.delete(`/rooms/${id}/`),
};

// Schedules
export const schedulesAPI = {
  getAll: () => api.get("/schedules/"),
  getById: (id) => api.get(`/schedules/${id}/`),
  getTimeline: () => api.get("/schedules/timeline/"),
  getConflicts: () => api.get("/schedules/conflicts/"),
  create: (data) => api.post("/schedules/", data),
  update: (id, data) => api.put(`/schedules/${id}/`, data),
  delete: (id) => api.delete(`/schedules/${id}/`),
};

// Data Management
export const dataAPI = {
  importExcel: (file, sheetType) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("sheet_type", sheetType);
    return api.post("/data/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  exportExcel: () => api.get("/data/", { responseType: "blob" }),
  getStatistics: () => api.get("/data/statistics/"),
};

// Algorithms
export const algorithmsAPI = {
  run: (algorithm, config) =>
    api.post("/algorithm/run/", { algorithm, config }),
  getResults: () => api.get("/algorithm/results/"),
  compare: (algorithms, config) =>
    api.post("/algorithm/compare/", { algorithms, config }),
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

export default api;
