import { useState, useMemo, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  dataAPI,
  applicantsAPI,
  interviewersAPI,
  roomsAPI,
  positionsAPI,
  sessionsAPI,
  companiesAPI,
} from "../services/api";
import toast from "react-hot-toast";
import { FiUpload, FiDownload, FiPlus, FiX } from "react-icons/fi";
import { useCurrentCompany } from "../hooks/useCurrentCompany";

const DataManagement = () => {
  const [activeTab, setActiveTab] = useState("applicants");
  const [isUploading, setIsUploading] = useState(false);
  const { companyId: authCompanyId, company } = useCurrentCompany();
  // Selected session (user choice) separate from active session flag
  const [selectedSessionId, setSelectedSessionId] = useState(
    () => localStorage.getItem("selected_session") || null
  );
  // Company selection is always driven from authCompanyId (current company)
  const [selectedCompanyId, setSelectedCompanyId] = useState("");

  // Companies list for selector
  const { data: companies } = useQuery({
    queryKey: ["companies"],
    queryFn: () => companiesAPI.getAll().then((r) => r.data),
  });

  // Keep selectedCompanyId in sync with current auth company
  useEffect(() => {
    if (!authCompanyId) return;
    // Clean up old localStorage keys that may conflict
    localStorage.removeItem("selectedCompany");
    localStorage.removeItem("company_id");
    setSelectedCompanyId(authCompanyId);
  }, [authCompanyId]);
  const queryClient = useQueryClient();
  // Active session (backend-defined current session)
  const { data: activeSession } = useQuery({
    queryKey: ["sessions", "active"],
    queryFn: () =>
      sessionsAPI
        .getActive()
        .then((res) => res.data)
        .catch(() => null),
  });

  // All sessions for user selection, filtered by selected company
  const { data: allSessions } = useQuery({
    queryKey: ["sessions", selectedCompanyId],
    enabled: !!selectedCompanyId,
    queryFn: () =>
      sessionsAPI
        .getAll({ company_id: selectedCompanyId })
        .then((res) => res.data),
  });

  // No auto-select session here; user chooses explicitly.

  // Resolve selected session (require explicit selection; no fallback)
  const selectedSession = useMemo(() => {
    if (!allSessions?.length || !selectedSessionId) return null;
    return allSessions.find((s) => s._id === selectedSessionId) || null;
  }, [allSessions, selectedSessionId]);

  const tabs = [
    { id: "sessions", label: "Interview Sessions" },
    { id: "applicants", label: "Applicants" },
    { id: "interviewers", label: "Interviewers" },
    { id: "rooms", label: "Rooms" },
    { id: "positions", label: "Positions" },
  ];

  // Import Excel
  const handleImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!selectedSession?._id) {
      toast.error("Please select a session first");
      return;
    }

    setIsUploading(true);
    try {
      await dataAPI.importExcel(file, "all", selectedSession._id);
      toast.success("Data imported successfully!");
      queryClient.invalidateQueries();
    } catch (error) {
      toast.error(error.message || "Failed to import data");
    } finally {
      setIsUploading(false);
    }
  };

  // Export Excel
  const handleExport = async () => {
    if (!selectedSession?._id) {
      toast.error("Please select a session first");
      return;
    }
    try {
      const response = await dataAPI.exportExcel(selectedSession._id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      const cd =
        response.headers?.["content-disposition"] ||
        response.headers?.["Content-Disposition"] ||
        "";
      let filename = null;
      // RFC5987 filename*
      const star = cd.match(/filename\*=UTF-8''([^;]+)/i);
      if (star && star[1]) {
        try {
          filename = decodeURIComponent(star[1]);
        } catch {
          /* ignore */
        }
      }
      if (!filename) {
        const m = cd.match(/filename="?([^";]+)"?/i);
        if (m && m[1]) filename = m[1];
      }
      if (!filename) {
        const companyName =
          (companies || []).find((c) => c._id === selectedCompanyId)?.name ||
          "Company";
        const period = `${selectedSession.start_date}_${selectedSession.end_date}`;
        // Use double underscore as separators to match backend
        filename = `${
          selectedSession.name || selectedSession.code || "Session"
        }__${period}__${companyName}.xlsx`;
      }
      filename = filename.replace(/[\\/:*?"<>|]/g, "-");
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Data exported successfully!");
    } catch (error) {
      toast.error("Failed to export data");
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-3xl font-bold text-gray-900">
              Data Management
            </h2>
          </div>
          <p className="text-gray-600">
            Manage data scoped to an interview session
          </p>
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-700">Company:</span>
            <span className="px-2 py-1 text-xs rounded bg-indigo-100 text-indigo-700 font-medium">
              {company?.name || company?.code || "Your Company"}
            </span>
            <label className="text-sm font-medium text-gray-700">
              Session:
            </label>
            <select
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              value={selectedSessionId || ""}
              disabled={!selectedCompanyId}
              onChange={(e) => {
                const val = e.target.value || null;
                setSelectedSessionId(val);
                if (val) localStorage.setItem("selected_session", val);
                else localStorage.removeItem("selected_session");
              }}
            >
              <option value="">
                {selectedCompanyId ? "Select session" : "Select company first"}
              </option>
              {allSessions?.map((s) => (
                <option key={s._id} value={s._id}>
                  {s.code || s.name} {s.is_active ? "(active)" : ""}
                </option>
              ))}
            </select>
            {selectedSession && (
              <>
                <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700">
                  {selectedSession.name}
                </span>
                <SessionMembershipButton session={selectedSession} />
              </>
            )}
          </div>
        </div>
        <div className="flex space-x-3">
          <label
            className={`btn btn-secondary cursor-pointer ${
              !selectedSession ? "opacity-50 pointer-events-none" : ""
            }`}
          >
            <FiUpload className="w-5 h-5" />
            <span>Import Excel</span>
            <input
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              disabled={!selectedSession}
              onChange={handleImport}
            />
          </label>
          <button
            onClick={handleExport}
            className={`btn btn-primary flex items-center space-x-2 ${
              !selectedSession ? "opacity-50 pointer-events-none" : ""
            }`}
            disabled={!selectedSession}
          >
            <FiDownload className="w-5 h-5" />
            <span>Export Excel</span>
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-4 mb-6 border-b pb-2">
          {tabs.map((tab) => {
            const disabled =
              tab.id !== "sessions" &&
              !selectedSession &&
              tab.id !== "sessions";
            return (
              <button
                key={tab.id}
                onClick={() => !disabled && setActiveTab(tab.id)}
                className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === tab.id
                    ? "bg-blue-600 text-white shadow"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                } ${disabled ? "opacity-40 cursor-not-allowed" : ""}`}
                type="button"
              >
                {tab.label}
              </button>
            );
          })}
        </div>
        {!selectedSession && activeTab !== "sessions" ? (
          <div className="p-4 mb-4 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-700">
            Please select a company and then a session to view and manage data.
          </div>
        ) : null}
        {activeTab === "applicants" && selectedSession && (
          <ApplicantsTable selectedSession={selectedSession} />
        )}
        {activeTab === "interviewers" && selectedSession && (
          <InterviewersTable selectedSession={selectedSession} />
        )}
        {activeTab === "rooms" && selectedSession && (
          <RoomsTable selectedSession={selectedSession} />
        )}
        {activeTab === "positions" && selectedSession && (
          <PositionsTable selectedSession={selectedSession} />
        )}
        {activeTab === "sessions" && (
          <SessionsTable companyId={selectedCompanyId} />
        )}
      </div>

      {/* Import Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          Excel Import Format
        </h3>
        <p className="text-sm text-blue-800 mb-3">
          Your Excel file should contain 3 sheets: Applicants, Interviewers, and
          Rooms
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-white p-3 rounded">
            <p className="font-medium mb-2">Applicants Sheet:</p>
            <ul className="text-gray-600 space-y-1">
              <li>• Email</li>
              <li>• Full Name</li>
              <li>• Student ID</li>
              <li>• Available Time</li>
              <li>• Position</li>
            </ul>
          </div>
          <div className="bg-white p-3 rounded">
            <p className="font-medium mb-2">Interviewers Sheet:</p>
            <ul className="text-gray-600 space-y-1">
              <li>• Full Name</li>
              <li>• Email</li>
              <li>• Position</li>
              <li>• Available Time</li>
              <li>• Preferred Room</li>
            </ul>
          </div>
          <div className="bg-white p-3 rounded">
            <p className="font-medium mb-2">Rooms Sheet:</p>
            <ul className="text-gray-600 space-y-1">
              <li>• Room Code</li>
              <li>• Room Name</li>
              <li>• Start Time</li>
              <li>• End Time</li>
              <li>• Preferred Position</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

// Sub-components for tables
const ApplicantsTable = ({ selectedSession }) => {
  const [showModal, setShowModal] = useState(false);
  const [editingApplicant, setEditingApplicant] = useState(null);
  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    student_id: "",
    available_time: "",
    position: "Media",
  });
  const queryClient = useQueryClient();

  const sessionId = selectedSession?._id || null;
  // Reset modal/editing when session changes
  useEffect(() => {
    setShowModal(false);
    setEditingApplicant(null);
  }, [sessionId]);
  const { data: filteredApplicants, isLoading } = useQuery({
    queryKey: ["applicants", sessionId],
    enabled: !!sessionId,
    queryFn: () =>
      applicantsAPI.getAll({ session_id: sessionId }).then((res) => res.data),
  });

  // Dynamic positions
  const { data: positions } = useQuery({
    queryKey: ["positions", "active"],
    queryFn: () => positionsAPI.getAll().then((res) => res.data),
  });

  // Add applicant (with session attach if selected)
  const addMutation = useMutation({
    mutationFn: async (data) => {
      const res = await applicantsAPI.create(data);
      if (selectedSession?._id) {
        const newId = res.data._id;
        const currentIds = selectedSession.applicant_ids || [];
        if (!currentIds.includes(newId)) {
          await sessionsAPI.update(selectedSession._id, {
            applicant_ids: [...currentIds, newId],
          });
        }
      }
      return res;
    },
    onSuccess: () => {
      toast.success("Applicant added successfully!");
      queryClient.invalidateQueries(["applicants"]);
      queryClient.invalidateQueries(["sessions"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to add applicant");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => applicantsAPI.update(id, data),
    onSuccess: () => {
      toast.success("Applicant updated successfully!");
      queryClient.invalidateQueries(["applicants"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update applicant");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      // Confirm if part of session
      const inSession = selectedSession?.applicant_ids?.includes(id);
      if (inSession) {
        if (
          !window.confirm("Applicant belongs to this session. Delete anyway?")
        ) {
          throw new Error("Deletion cancelled");
        }
      }
      await applicantsAPI.delete(id);
      if (inSession) {
        const newIds = selectedSession.applicant_ids.filter(
          (aid) => aid !== id
        );
        await sessionsAPI.update(selectedSession._id, {
          applicant_ids: newIds,
        });
      }
      return id;
    },
    onSuccess: () => {
      toast.success("Applicant deleted successfully!");
      queryClient.invalidateQueries(["applicants"]);
      queryClient.invalidateQueries(["sessions"]);
    },
    onError: (error) => {
      if (error.message !== "Deletion cancelled") {
        toast.error(error.message || "Failed to delete applicant");
      }
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingApplicant(null);
    setFormData({
      email: "",
      full_name: "",
      student_id: "",
      available_time: "",
      position: "Media",
    });
  };

  const handleEdit = (applicant) => {
    setEditingApplicant(applicant);
    setFormData({
      email: applicant.email,
      full_name: applicant.full_name,
      student_id: applicant.student_id,
      available_time: applicant.available_time,
      position: applicant.position,
    });
    setShowModal(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingApplicant) {
      updateMutation.mutate({ id: editingApplicant._id, data: formData });
    } else {
      addMutation.mutate(formData);
    }
  };

  if (!sessionId) return <div>Please select a session to view applicants.</div>;
  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Applicants ({filteredApplicants.length || 0})
        </h3>
        <button onClick={() => setShowModal(true)} className="btn btn-primary">
          <FiPlus className="w-5 h-5" />
          <span>Add Applicant</span>
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Student ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Position
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredApplicants.map((applicant) => (
              <tr key={applicant._id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  {applicant.full_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {applicant.email}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {applicant.student_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                    {applicant.position}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => handleEdit(applicant)}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(applicant._id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                {editingApplicant ? "Edit Applicant" : "Add Applicant"}
              </h3>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Student ID
                </label>
                <input
                  type="text"
                  required
                  value={formData.student_id}
                  onChange={(e) =>
                    setFormData({ ...formData, student_id: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Available Time
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., 09:00-12:00"
                  value={formData.available_time}
                  onChange={(e) =>
                    setFormData({ ...formData, available_time: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Position
                </label>
                <select
                  value={formData.position}
                  onChange={(e) =>
                    setFormData({ ...formData, position: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {(positions?.length
                    ? positions
                    : [
                        { _id: "Media", code: "Media", name: "Media" },
                        { _id: "HR", code: "HR", name: "HR" },
                        { _id: "Event", code: "Event", name: "Event" },
                      ]
                  ).map((p) => (
                    <option key={p._id || p.code} value={p.code}>
                      {p.name || p.code}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {editingApplicant
                    ? updateMutation.isPending
                      ? "Updating..."
                      : "Update Applicant"
                    : addMutation.isPending
                    ? "Adding..."
                    : "Add Applicant"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const InterviewersTable = ({ selectedSession }) => {
  const [showModal, setShowModal] = useState(false);
  const [editingInterviewer, setEditingInterviewer] = useState(null);
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    position: "Media",
    available_time: "",
    preferred_room: "",
    max_slots: 5,
  });
  const queryClient = useQueryClient();

  const sessionId = selectedSession?._id || null;
  useEffect(() => {
    setShowModal(false);
    setEditingInterviewer(null);
  }, [sessionId]);
  const { data: filteredInterviewers, isLoading } = useQuery({
    queryKey: ["interviewers", sessionId],
    enabled: !!sessionId,
    queryFn: () =>
      interviewersAPI.getAll({ session_id: sessionId }).then((res) => res.data),
  });

  // Dynamic positions
  const { data: positions } = useQuery({
    queryKey: ["positions", "active"],
    queryFn: () => positionsAPI.getAll().then((res) => res.data),
  });

  // Add interviewer (and attach to session if selected)
  const addMutation = useMutation({
    mutationFn: async (data) => {
      const res = await interviewersAPI.create(data);
      if (selectedSession?._id) {
        const newId = res.data._id;
        const currentIds = selectedSession.interviewer_ids || [];
        if (!currentIds.includes(newId)) {
          await sessionsAPI.update(selectedSession._id, {
            interviewer_ids: [...currentIds, newId],
          });
        }
      }
      return res;
    },
    onSuccess: () => {
      toast.success("Interviewer added successfully!");
      queryClient.invalidateQueries(["interviewers"]);
      queryClient.invalidateQueries(["sessions"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to add interviewer");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => interviewersAPI.update(id, data),
    onSuccess: () => {
      toast.success("Interviewer updated successfully!");
      queryClient.invalidateQueries(["interviewers"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update interviewer");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const inSession = selectedSession?.interviewer_ids?.includes(id);
      if (inSession) {
        if (
          !window.confirm("Interviewer belongs to this session. Delete anyway?")
        ) {
          throw new Error("Deletion cancelled");
        }
      }
      await interviewersAPI.delete(id);
      if (inSession) {
        const newIds = selectedSession.interviewer_ids.filter(
          (iid) => iid !== id
        );
        await sessionsAPI.update(selectedSession._id, {
          interviewer_ids: newIds,
        });
      }
      return id;
    },
    onSuccess: () => {
      toast.success("Interviewer deleted successfully!");
      queryClient.invalidateQueries(["interviewers"]);
      queryClient.invalidateQueries(["sessions"]);
    },
    onError: (error) => {
      if (error.message !== "Deletion cancelled") {
        toast.error(error.message || "Failed to delete interviewer");
      }
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingInterviewer(null);
    setFormData({
      full_name: "",
      email: "",
      position: "Media",
      available_time: "",
      preferred_room: "",
      max_slots: 5,
    });
  };

  const handleEdit = (interviewer) => {
    setEditingInterviewer(interviewer);
    setFormData({
      full_name: interviewer.full_name,
      email: interviewer.email,
      position: interviewer.position,
      available_time: interviewer.available_time,
      preferred_room: interviewer.preferred_room || "",
      max_slots: interviewer.max_slots,
    });
    setShowModal(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingInterviewer) {
      updateMutation.mutate({ id: editingInterviewer._id, data: formData });
    } else {
      addMutation.mutate(formData);
    }
  };

  if (!sessionId)
    return <div>Please select a session to view interviewers.</div>;
  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Interviewers ({filteredInterviewers.length})
        </h3>
        <button onClick={() => setShowModal(true)} className="btn btn-primary">
          <FiPlus className="w-5 h-5" />
          <span>Add Interviewer</span>
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Position
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Max Slots
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredInterviewers.map((interviewer) => (
              <tr key={interviewer._id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  {interviewer.full_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {interviewer.email}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                    {interviewer.position}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {interviewer.max_slots}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => handleEdit(interviewer)}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(interviewer._id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                {editingInterviewer ? "Edit Interviewer" : "Add Interviewer"}
              </h3>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Position
                </label>
                <select
                  value={formData.position}
                  onChange={(e) =>
                    setFormData({ ...formData, position: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {(positions?.length
                    ? positions
                    : [
                        { _id: "Media", code: "Media", name: "Media" },
                        { _id: "HR", code: "HR", name: "HR" },
                        { _id: "Event", code: "Event", name: "Event" },
                      ]
                  ).map((p) => (
                    <option key={p._id || p.code} value={p.code}>
                      {p.name || p.code}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Available Time
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., 09:00-17:00"
                  value={formData.available_time}
                  onChange={(e) =>
                    setFormData({ ...formData, available_time: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preferred Room
                </label>
                <input
                  type="text"
                  value={formData.preferred_room}
                  onChange={(e) =>
                    setFormData({ ...formData, preferred_room: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Slots
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  value={formData.max_slots}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      max_slots: parseInt(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {editingInterviewer
                    ? updateMutation.isPending
                      ? "Updating..."
                      : "Update Interviewer"
                    : addMutation.isPending
                    ? "Adding..."
                    : "Add Interviewer"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const RoomsTable = ({ selectedSession }) => {
  const [showModal, setShowModal] = useState(false);
  const [editingRoom, setEditingRoom] = useState(null);
  const [formData, setFormData] = useState({
    room_code: "",
    room_name: "",
    start_time: "",
    end_time: "",
    preferred_position: "",
  });
  const queryClient = useQueryClient();

  const sessionId = selectedSession?._id || null;
  useEffect(() => {
    setShowModal(false);
    setEditingRoom(null);
  }, [sessionId]);
  const { data: filteredRooms, isLoading } = useQuery({
    queryKey: ["rooms", sessionId],
    enabled: !!sessionId,
    queryFn: () =>
      roomsAPI.getAll({ session_id: sessionId }).then((res) => res.data),
  });

  // Dynamic positions for preferred_position
  const { data: positions } = useQuery({
    queryKey: ["positions", "active"],
    queryFn: () => positionsAPI.getAll().then((res) => res.data),
  });

  const addMutation = useMutation({
    mutationFn: async (data) => {
      const res = await roomsAPI.create(data);
      if (selectedSession?._id) {
        const newId = res.data._id;
        const currentIds = selectedSession.room_ids || [];
        if (!currentIds.includes(newId)) {
          await sessionsAPI.update(selectedSession._id, {
            room_ids: [...currentIds, newId],
          });
        }
      }
      return res;
    },
    onSuccess: () => {
      toast.success("Room added successfully!");
      queryClient.invalidateQueries(["rooms"]);
      queryClient.invalidateQueries(["sessions"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to add room");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => roomsAPI.update(id, data),
    onSuccess: () => {
      toast.success("Room updated successfully!");
      queryClient.invalidateQueries(["rooms"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update room");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const inSession = selectedSession?.room_ids?.includes(id);
      if (inSession) {
        if (!window.confirm("Room belongs to this session. Delete anyway?")) {
          throw new Error("Deletion cancelled");
        }
      }
      await roomsAPI.delete(id);
      if (inSession) {
        const newIds = selectedSession.room_ids.filter((rid) => rid !== id);
        await sessionsAPI.update(selectedSession._id, { room_ids: newIds });
      }
      return id;
    },
    onSuccess: () => {
      toast.success("Room deleted successfully!");
      queryClient.invalidateQueries(["rooms"]);
      queryClient.invalidateQueries(["sessions"]);
    },
    onError: (error) => {
      if (error.message !== "Deletion cancelled") {
        toast.error(error.message || "Failed to delete room");
      }
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingRoom(null);
    setFormData({
      room_code: "",
      room_name: "",
      start_time: "",
      end_time: "",
      preferred_position: "",
    });
  };

  const handleEdit = (room) => {
    setEditingRoom(room);
    setFormData({
      room_code: room.room_code,
      room_name: room.room_name,
      start_time: room.start_time,
      end_time: room.end_time,
      preferred_position: room.preferred_position || "",
    });
    setShowModal(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingRoom) {
      updateMutation.mutate({ id: editingRoom._id, data: formData });
    } else {
      addMutation.mutate(formData);
    }
  };

  if (!sessionId) return <div>Please select a session to view rooms.</div>;
  if (isLoading) return <div>Loading...</div>;

  // existing code continues

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Rooms ({filteredRooms.length})
        </h3>
        <button onClick={() => setShowModal(true)} className="btn btn-primary">
          <FiPlus className="w-5 h-5" />
          <span>Add Room</span>
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Code
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Preferred Position
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredRooms.map((room) => (
              <tr key={room._id}>
                <td className="px-6 py-4 whitespace-nowrap font-medium">
                  {room.room_code}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {room.room_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {room.start_time} - {room.end_time}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {room.preferred_position && (
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800">
                      {room.preferred_position}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => handleEdit(room)}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(room._id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                {editingRoom ? "Edit Room" : "Add Room"}
              </h3>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Room Code
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., A101"
                  value={formData.room_code}
                  onChange={(e) =>
                    setFormData({ ...formData, room_code: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Room Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Conference Room A"
                  value={formData.room_name}
                  onChange={(e) =>
                    setFormData({ ...formData, room_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Time
                </label>
                <input
                  type="time"
                  required
                  value={formData.start_time}
                  onChange={(e) =>
                    setFormData({ ...formData, start_time: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Time
                </label>
                <input
                  type="time"
                  required
                  value={formData.end_time}
                  onChange={(e) =>
                    setFormData({ ...formData, end_time: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preferred Position (Optional)
                </label>
                <select
                  value={formData.preferred_position}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      preferred_position: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">None</option>
                  {(positions?.length
                    ? positions
                    : [
                        { _id: "Media", code: "Media", name: "Media" },
                        { _id: "HR", code: "HR", name: "HR" },
                        { _id: "Event", code: "Event", name: "Event" },
                      ]
                  ).map((p) => (
                    <option key={p._id || p.code} value={p.code}>
                      {p.name || p.code}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {editingRoom
                    ? updateMutation.isPending
                      ? "Updating..."
                      : "Update Room"
                    : addMutation.isPending
                    ? "Adding..."
                    : "Add Room"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const PositionsTable = ({ selectedSession }) => {
  const [showModal, setShowModal] = useState(false);
  const [editingPosition, setEditingPosition] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    description: "",
    is_active: true,
  });
  const queryClient = useQueryClient();

  const { data: positions, isLoading } = useQuery({
    queryKey: ["positions"],
    queryFn: () => positionsAPI.getAll().then((res) => res.data),
  });

  useEffect(() => {
    setShowModal(false);
    setEditingPosition(null);
  }, [selectedSession?._id]);

  const filteredPositions = useMemo(() => {
    if (!selectedSession?.position_ids?.length) return positions || [];
    const setIds = new Set(selectedSession.position_ids.map(String));
    return (positions || []).filter((p) => setIds.has(String(p._id)));
  }, [positions, selectedSession]);

  const addMutation = useMutation({
    mutationFn: async (data) => {
      const res = await positionsAPI.create(data);
      if (selectedSession?._id) {
        const newId = res.data._id;
        const currentIds = selectedSession.position_ids || [];
        if (!currentIds.includes(newId)) {
          await sessionsAPI.update(selectedSession._id, {
            position_ids: [...currentIds, newId],
          });
        }
      }
      return res;
    },
    onSuccess: () => {
      toast.success("Position added successfully!");
      queryClient.invalidateQueries(["positions"]);
      queryClient.invalidateQueries(["sessions"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to add position");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => positionsAPI.update(id, data),
    onSuccess: () => {
      toast.success("Position updated successfully!");
      queryClient.invalidateQueries(["positions"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update position");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const inSession = selectedSession?.position_ids?.includes(id);
      if (inSession) {
        if (
          !window.confirm("Position belongs to this session. Delete anyway?")
        ) {
          throw new Error("Deletion cancelled");
        }
      }
      await positionsAPI.delete(id);
      if (inSession) {
        const newIds = selectedSession.position_ids.filter((pid) => pid !== id);
        await sessionsAPI.update(selectedSession._id, { position_ids: newIds });
      }
      return id;
    },
    onSuccess: () => {
      toast.success("Position deleted successfully!");
      queryClient.invalidateQueries(["positions"]);
      queryClient.invalidateQueries(["sessions"]);
    },
    onError: (error) => {
      if (error.message !== "Deletion cancelled") {
        toast.error(error.message || "Failed to delete position");
      }
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingPosition(null);
    setFormData({
      name: "",
      code: "",
      description: "",
      is_active: true,
    });
  };

  const handleEdit = (position) => {
    setEditingPosition(position);
    setFormData({
      name: position.name,
      code: position.code,
      description: position.description || "",
      is_active: position.is_active,
    });
    setShowModal(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingPosition) {
      updateMutation.mutate({ id: editingPosition._id, data: formData });
    } else {
      addMutation.mutate(formData);
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Positions ({filteredPositions.length})
        </h3>
        <button onClick={() => setShowModal(true)} className="btn btn-primary">
          <FiPlus className="w-5 h-5" />
          <span>Add Position</span>
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Code
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredPositions.map((position) => (
              <tr key={position._id}>
                <td className="px-6 py-4 whitespace-nowrap font-medium">
                  {position.code}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">{position.name}</td>
                <td className="px-6 py-4">{position.description || "-"}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      position.is_active
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {position.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => handleEdit(position)}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(position._id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                {editingPosition ? "Edit Position" : "Add Position"}
              </h3>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Code
                </label>
                <input
                  type="text"
                  required
                  value={formData.code}
                  onChange={(e) =>
                    setFormData({ ...formData, code: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) =>
                    setFormData({ ...formData, is_active: e.target.checked })
                  }
                  className="mr-2"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">
                  Active
                </label>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {addMutation.isPending || updateMutation.isPending
                    ? "Saving..."
                    : editingPosition
                    ? "Update"
                    : "Add"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const SessionsTable = () => {
  const [showModal, setShowModal] = useState(false);
  const [editingSession, setEditingSession] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    year: new Date().getFullYear(),
    start_date: "",
    end_date: "",
    description: "",
    is_active: false,
  });
  const queryClient = useQueryClient();

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => sessionsAPI.getAll().then((res) => res.data),
  });

  const addMutation = useMutation({
    mutationFn: (data) => sessionsAPI.create(data),
    onSuccess: () => {
      toast.success("Session added successfully!");
      queryClient.invalidateQueries(["sessions"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to add session");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => sessionsAPI.update(id, data),
    onSuccess: () => {
      toast.success("Session updated successfully!");
      queryClient.invalidateQueries(["sessions"]);
      closeModal();
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update session");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => sessionsAPI.delete(id),
    onSuccess: () => {
      toast.success("Session deleted successfully!");
      queryClient.invalidateQueries(["sessions"]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete session");
    },
  });

  const activateMutation = useMutation({
    mutationFn: (id) => sessionsAPI.activate(id),
    onSuccess: () => {
      toast.success("Session activated successfully!");
      queryClient.invalidateQueries(["sessions"]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to activate session");
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingSession(null);
    setFormData({
      name: "",
      code: "",
      year: new Date().getFullYear(),
      start_date: "",
      end_date: "",
      description: "",
      is_active: false,
    });
  };

  const handleEdit = (session) => {
    setEditingSession(session);
    setFormData({
      name: session.name,
      code: session.code,
      year: session.year,
      start_date: session.start_date,
      end_date: session.end_date,
      description: session.description || "",
      is_active: session.is_active,
    });
    setShowModal(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingSession) {
      updateMutation.mutate({ id: editingSession._id, data: formData });
    } else {
      addMutation.mutate(formData);
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Interview Sessions ({sessions?.length || 0})
        </h3>
        <button onClick={() => setShowModal(true)} className="btn btn-primary">
          <FiPlus className="w-5 h-5" />
          <span>Add Session</span>
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Code
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Year
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Period
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sessions?.map((session) => (
              <tr key={session._id}>
                <td className="px-6 py-4 whitespace-nowrap font-medium">
                  {session.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">{session.code}</td>
                <td className="px-6 py-4 whitespace-nowrap">{session.year}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {session.start_date} ~ {session.end_date}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      session.is_active
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {session.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {!session.is_active && (
                    <button
                      onClick={() => activateMutation.mutate(session._id)}
                      className="text-green-600 hover:text-green-800 mr-3"
                    >
                      Activate
                    </button>
                  )}
                  <button
                    onClick={() => handleEdit(session)}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(session._id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                {editingSession ? "Edit Session" : "Add Session"}
              </h3>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Code
                </label>
                <input
                  type="text"
                  required
                  value={formData.code}
                  onChange={(e) =>
                    setFormData({ ...formData, code: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Year
                </label>
                <input
                  type="number"
                  required
                  value={formData.year}
                  onChange={(e) =>
                    setFormData({ ...formData, year: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  required
                  value={formData.start_date}
                  onChange={(e) =>
                    setFormData({ ...formData, start_date: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  required
                  value={formData.end_date}
                  onChange={(e) =>
                    setFormData({ ...formData, end_date: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="session_is_active"
                  checked={formData.is_active}
                  onChange={(e) =>
                    setFormData({ ...formData, is_active: e.target.checked })
                  }
                  className="mr-2"
                />
                <label
                  htmlFor="session_is_active"
                  className="text-sm text-gray-700"
                >
                  Active
                </label>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {addMutation.isPending || updateMutation.isPending
                    ? "Saving..."
                    : editingSession
                    ? "Update"
                    : "Add"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Membership management button and modal
const SessionMembershipButton = ({ session }) => {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button className="btn btn-secondary" onClick={() => setOpen(true)}>
        Manage Membership
      </button>
      {open && (
        <SessionMembershipModal
          session={session}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
};

const SessionMembershipModal = ({ session, onClose }) => {
  const queryClient = useQueryClient();
  const sessionId = session?._id;
  const [activeTab, setActiveTab] = useState("applicants");
  const [search, setSearch] = useState("");
  const [showAll, setShowAll] = useState(true);
  const [positionFilter, setPositionFilter] = useState("");

  // Live selection sets (used for preview and filtering when Scope = "In Session")
  const [selApplicants, setSelApplicants] = useState(
    new Set((session.applicant_ids || []).map(String))
  );
  const [selInterviewers, setSelInterviewers] = useState(
    new Set((session.interviewer_ids || []).map(String))
  );
  const [selRooms, setSelRooms] = useState(
    new Set((session.room_ids || []).map(String))
  );
  const [selPositions, setSelPositions] = useState(
    new Set((session.position_ids || []).map(String))
  );

  const { data: allApplicants } = useQuery({
    queryKey: ["applicants_pool"],
    queryFn: () => applicantsAPI.getAll().then((r) => r.data),
  });
  const { data: allInterviewers } = useQuery({
    queryKey: ["interviewers_pool"],
    queryFn: () => interviewersAPI.getAll().then((r) => r.data),
  });
  const { data: allRooms } = useQuery({
    queryKey: ["rooms_pool"],
    queryFn: () => roomsAPI.getAll().then((r) => r.data),
  });
  const { data: allPositions } = useQuery({
    queryKey: ["positions_pool"],
    queryFn: () => positionsAPI.getAll().then((r) => r.data),
  });

  // Derived sets for filtering (session membership vs all)
  const sessionApplicantIds = new Set(
    (session.applicant_ids || []).map(String)
  );
  const sessionInterviewerIds = new Set(
    (session.interviewer_ids || []).map(String)
  );
  const sessionRoomIds = new Set((session.room_ids || []).map(String));
  const sessionPositionIds = new Set((session.position_ids || []).map(String));

  const normalizeSearch = (v) => v.trim().toLowerCase();
  const s = normalizeSearch(search);

  // Filtering logic; when showAll=false use current selection sets (live preview), not persisted session membership.
  const applyFilters = (items, liveSet, keyName, extraKeys = []) => {
    if (!items) return [];
    return items.filter((it) => {
      const idStr = String(it._id);
      if (!showAll && !liveSet.has(idStr)) return false;
      if (s) {
        const composite = [
          it[keyName] || "",
          ...extraKeys.map((k) => it[k] || ""),
        ]
          .join(" ")
          .toLowerCase();
        if (!composite.includes(s)) return false;
      }
      if (positionFilter) {
        const posVal = (
          it.position ||
          it.preferred_position ||
          it.code ||
          ""
        ).toLowerCase();
        if (posVal !== positionFilter.toLowerCase()) return false;
      }
      return true;
    });
  };

  const filteredApplicants = applyFilters(
    allApplicants || [],
    selApplicants,
    "full_name",
    ["email", "student_id", "position"]
  );
  const filteredInterviewers = applyFilters(
    allInterviewers || [],
    selInterviewers,
    "full_name",
    ["email", "position"]
  );
  const filteredRooms = applyFilters(allRooms || [], selRooms, "room_name", [
    "room_code",
    "preferred_position",
  ]);
  const filteredPositions = applyFilters(
    allPositions || [],
    selPositions,
    "name",
    ["code", "description"]
  );

  // Position options aggregated from applicants + interviewers + positions
  const positionOptions = Array.from(
    new Set([
      ...(allApplicants || []).map((a) => a.position).filter(Boolean),
      ...(allInterviewers || []).map((i) => i.position).filter(Boolean),
      ...(allPositions || []).map((p) => p.code).filter(Boolean),
    ])
  ).sort();

  const toggle = (setFn, current, id) => {
    const copy = new Set(current);
    if (copy.has(id)) copy.delete(id);
    else copy.add(id);
    setFn(copy);
  };

  const onSave = async () => {
    try {
      const currA = new Set((session.applicant_ids || []).map(String));
      const currI = new Set((session.interviewer_ids || []).map(String));
      const currR = new Set((session.room_ids || []).map(String));
      const currP = new Set((session.position_ids || []).map(String));

      const nextA = Array.from(selApplicants);
      const nextI = Array.from(selInterviewers);
      const nextR = Array.from(selRooms);
      const nextP = Array.from(selPositions);

      const add = {
        applicants: nextA.filter((x) => !currA.has(x)),
        interviewers: nextI.filter((x) => !currI.has(x)),
        rooms: nextR.filter((x) => !currR.has(x)),
        positions: nextP.filter((x) => !currP.has(x)),
      };
      const remove = {
        applicants: Array.from(currA).filter((x) => !selApplicants.has(x)),
        interviewers: Array.from(currI).filter((x) => !selInterviewers.has(x)),
        rooms: Array.from(currR).filter((x) => !selRooms.has(x)),
        positions: Array.from(currP).filter((x) => !selPositions.has(x)),
      };

      await sessionsAPI.updateMembership(sessionId, { add, remove });
      toast.success("Membership updated");
      // Refresh session and scoped lists immediately
      queryClient.invalidateQueries(["sessions"]);
      if (sessionId) {
        queryClient.invalidateQueries(["applicants", sessionId]);
        queryClient.invalidateQueries(["interviewers", sessionId]);
        queryClient.invalidateQueries(["rooms", sessionId]);
        queryClient.invalidateQueries(["positions"]);
      }
      onClose();
    } catch (e) {
      toast.error(e.message || "Failed to update membership");
    }
  };

  const Tab = ({ id, label }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`px-3 py-2 text-sm border-b-2 ${
        activeTab === id
          ? "border-blue-500 text-blue-600"
          : "border-transparent text-gray-600"
      }`}
    >
      {label}
    </button>
  );

  const List = ({ items, selSet, setSel, titleKey, subKey }) => (
    <div className="max-h-80 overflow-y-auto border rounded p-2">
      {items.map((it) => (
        <label key={it._id} className="flex items-center space-x-2 py-1">
          <input
            type="checkbox"
            checked={selSet.has(String(it._id))}
            onChange={() => toggle(setSel, selSet, String(it._id))}
          />
          <span className="text-sm">
            {it[titleKey] || it.full_name || it.room_name || it.name}
            {subKey && it[subKey] ? (
              <span className="text-gray-500"> — {it[subKey]}</span>
            ) : null}
          </span>
        </label>
      ))}
    </div>
  );

  // Select All checkbox component acts on currently filtered list
  const SelectAllCheckbox = ({ items, selSet, setSel }) => {
    const ids = items.map((it) => String(it._id));
    const total = ids.length;
    const selected = ids.filter((id) => selSet.has(id)).length;
    const allSelected = total > 0 && selected === total;
    const partial = selected > 0 && selected < total;

    const toggleAll = () => {
      const next = new Set(selSet);
      if (allSelected) {
        ids.forEach((id) => next.delete(id));
      } else {
        ids.forEach((id) => next.add(id));
      }
      setSel(next);
    };

    return (
      <label className="flex items-center gap-1 text-xs font-medium cursor-pointer">
        <input
          type="checkbox"
          checked={allSelected}
          ref={(el) => {
            if (el) el.indeterminate = partial;
          }}
          onChange={toggleAll}
        />
        <span>
          {allSelected ? "Unselect All" : "Select All"} ({selected}/{total})
        </span>
      </label>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">
            Manage Membership for {session?.name}
          </h3>
          <button className="text-gray-500" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="border-b mb-4 flex space-x-4">
          <Tab id="applicants" label="Applicants" />
          <Tab id="interviewers" label="Interviewers" />
          <Tab id="rooms" label="Rooms" />
          <Tab id="positions" label="Positions" />
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-end gap-4 mb-4">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium">Scope:</label>
            <select
              className="border px-2 py-1 rounded text-xs"
              value={showAll ? "all" : "session"}
              onChange={(e) => setShowAll(e.target.value === "all")}
            >
              <option value="all">All</option>
              <option value="session">In Session</option>
            </select>
          </div>
          <div className="flex-grow min-w-[180px]">
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full border px-3 py-1 rounded text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium">Position:</label>
            <select
              className="border px-2 py-1 rounded text-xs"
              value={positionFilter}
              onChange={(e) => setPositionFilter(e.target.value)}
            >
              <option value="">(Any)</option>
              {positionOptions.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          {(search || positionFilter || !showAll) && (
            <button
              onClick={() => {
                setSearch("");
                setPositionFilter("");
                setShowAll(true);
              }}
              className="text-xs text-gray-600 hover:text-gray-800"
            >
              Reset Filters
            </button>
          )}
          <div className="flex items-center gap-3 ml-auto">
            {activeTab === "applicants" && (
              <SelectAllCheckbox
                items={filteredApplicants}
                selSet={selApplicants}
                setSel={setSelApplicants}
              />
            )}
            {activeTab === "interviewers" && (
              <SelectAllCheckbox
                items={filteredInterviewers}
                selSet={selInterviewers}
                setSel={setSelInterviewers}
              />
            )}
            {activeTab === "rooms" && (
              <SelectAllCheckbox
                items={filteredRooms}
                selSet={selRooms}
                setSel={setSelRooms}
              />
            )}
            {activeTab === "positions" && (
              <SelectAllCheckbox
                items={filteredPositions}
                selSet={selPositions}
                setSel={setSelPositions}
              />
            )}
          </div>
        </div>

        {activeTab === "applicants" && (
          <List
            items={filteredApplicants}
            selSet={selApplicants}
            setSel={setSelApplicants}
            titleKey="full_name"
            subKey="email"
          />
        )}
        {activeTab === "interviewers" && (
          <List
            items={filteredInterviewers}
            selSet={selInterviewers}
            setSel={setSelInterviewers}
            titleKey="full_name"
            subKey="email"
          />
        )}
        {activeTab === "rooms" && (
          <List
            items={filteredRooms}
            selSet={selRooms}
            setSel={setSelRooms}
            titleKey="room_name"
            subKey="room_code"
          />
        )}
        {activeTab === "positions" && (
          <List
            items={filteredPositions}
            selSet={selPositions}
            setSel={setSelPositions}
            titleKey="name"
            subKey="code"
          />
        )}

        <div className="mt-4 flex justify-end space-x-3">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={onSave}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataManagement;
