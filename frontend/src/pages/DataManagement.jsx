import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  dataAPI,
  applicantsAPI,
  interviewersAPI,
  roomsAPI,
  positionsAPI,
  sessionsAPI,
} from "../services/api";
import toast from "react-hot-toast";
import { FiUpload, FiDownload, FiPlus, FiX } from "react-icons/fi";

const DataManagement = () => {
  const [activeTab, setActiveTab] = useState("applicants");
  const [isUploading, setIsUploading] = useState(false);
  const queryClient = useQueryClient();
  // Active session (for per-session import/export)
  const { data: activeSession } = useQuery({
    queryKey: ["sessions", "active"],
    queryFn: () =>
      sessionsAPI
        .getActive()
        .then((res) => res.data)
        .catch(() => null),
  });

  const tabs = [
    { id: "applicants", label: "Applicants" },
    { id: "interviewers", label: "Interviewers" },
    { id: "rooms", label: "Rooms" },
    { id: "positions", label: "Positions" },
    { id: "sessions", label: "Interview Sessions" },
  ];

  // Import Excel
  const handleImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await dataAPI.importExcel(file, "all", activeSession?._id);
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
    try {
      const response = await dataAPI.exportExcel(activeSession?._id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        activeSession?.code
          ? `schedules_${activeSession.code}.xlsx`
          : "interview_data.xlsx"
      );
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
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Data Management</h2>
          <p className="text-gray-600 mt-1">
            Manage applicants, interviewers, and rooms
          </p>
        </div>
        <div className="flex space-x-3">
          <label className="btn btn-secondary cursor-pointer">
            <FiUpload className="w-5 h-5" />
            <span>Import Excel</span>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleImport}
              className="hidden"
              disabled={isUploading}
            />
          </label>
          <button onClick={handleExport} className="btn btn-secondary">
            <FiDownload className="w-5 h-5" />
            <span>Export Excel</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b">
          <div className="flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-3 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {activeTab === "applicants" && <ApplicantsTable />}
          {activeTab === "interviewers" && <InterviewersTable />}
          {activeTab === "rooms" && <RoomsTable />}
          {activeTab === "positions" && <PositionsTable />}
          {activeTab === "sessions" && <SessionsTable />}
        </div>
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
const ApplicantsTable = () => {
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

  const { data: applicants, isLoading } = useQuery({
    queryKey: ["applicants"],
    queryFn: () => applicantsAPI.getAll().then((res) => res.data),
  });

  // Dynamic positions
  const { data: positions } = useQuery({
    queryKey: ["positions", "active"],
    queryFn: () => positionsAPI.getAll().then((res) => res.data),
  });

  const addMutation = useMutation({
    mutationFn: (data) => applicantsAPI.create(data),
    onSuccess: () => {
      toast.success("Applicant added successfully!");
      queryClient.invalidateQueries(["applicants"]);
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
    mutationFn: (id) => applicantsAPI.delete(id),
    onSuccess: () => {
      toast.success("Applicant deleted successfully!");
      queryClient.invalidateQueries(["applicants"]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete applicant");
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

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Applicants ({applicants?.length || 0})
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
            {applicants?.map((applicant) => (
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

const InterviewersTable = () => {
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

  const { data: interviewers, isLoading } = useQuery({
    queryKey: ["interviewers"],
    queryFn: () => interviewersAPI.getAll().then((res) => res.data),
  });

  // Dynamic positions
  const { data: positions } = useQuery({
    queryKey: ["positions", "active"],
    queryFn: () => positionsAPI.getAll().then((res) => res.data),
  });

  const addMutation = useMutation({
    mutationFn: (data) => interviewersAPI.create(data),
    onSuccess: () => {
      toast.success("Interviewer added successfully!");
      queryClient.invalidateQueries(["interviewers"]);
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
    mutationFn: (id) => interviewersAPI.delete(id),
    onSuccess: () => {
      toast.success("Interviewer deleted successfully!");
      queryClient.invalidateQueries(["interviewers"]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete interviewer");
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

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Interviewers ({interviewers?.length || 0})
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
            {interviewers?.map((interviewer) => (
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

const RoomsTable = () => {
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

  const { data: rooms, isLoading } = useQuery({
    queryKey: ["rooms"],
    queryFn: () => roomsAPI.getAll().then((res) => res.data),
  });

  // Dynamic positions for preferred_position
  const { data: positions } = useQuery({
    queryKey: ["positions", "active"],
    queryFn: () => positionsAPI.getAll().then((res) => res.data),
  });

  const addMutation = useMutation({
    mutationFn: (data) => roomsAPI.create(data),
    onSuccess: () => {
      toast.success("Room added successfully!");
      queryClient.invalidateQueries(["rooms"]);
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
    mutationFn: (id) => roomsAPI.delete(id),
    onSuccess: () => {
      toast.success("Room deleted successfully!");
      queryClient.invalidateQueries(["rooms"]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete room");
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

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Rooms ({rooms?.length || 0})</h3>
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
            {rooms?.map((room) => (
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

const PositionsTable = () => {
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

  const addMutation = useMutation({
    mutationFn: (data) => positionsAPI.create(data),
    onSuccess: () => {
      toast.success("Position added successfully!");
      queryClient.invalidateQueries(["positions"]);
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
    mutationFn: (id) => positionsAPI.delete(id),
    onSuccess: () => {
      toast.success("Position deleted successfully!");
      queryClient.invalidateQueries(["positions"]);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete position");
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
          Positions ({positions?.length || 0})
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
            {positions?.map((position) => (
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

export default DataManagement;
