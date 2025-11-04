import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  dataAPI,
  applicantsAPI,
  interviewersAPI,
  roomsAPI,
} from "../services/api";
import toast from "react-hot-toast";
import { FiUpload, FiDownload, FiPlus } from "react-icons/fi";

const DataManagement = () => {
  const [activeTab, setActiveTab] = useState("applicants");
  const [isUploading, setIsUploading] = useState(false);
  const queryClient = useQueryClient();

  const tabs = [
    { id: "applicants", label: "Applicants" },
    { id: "interviewers", label: "Interviewers" },
    { id: "rooms", label: "Rooms" },
  ];

  // Import Excel
  const handleImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await dataAPI.importExcel(file, "all");
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
      const response = await dataAPI.exportExcel();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "interview_data.xlsx");
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
  const { data: applicants, isLoading } = useQuery({
    queryKey: ["applicants"],
    queryFn: () => applicantsAPI.getAll().then((res) => res.data),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Applicants ({applicants?.length || 0})
        </h3>
        <button className="btn btn-primary">
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
                  <button className="text-blue-600 hover:text-blue-800 mr-3">
                    Edit
                  </button>
                  <button className="text-red-600 hover:text-red-800">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const InterviewersTable = () => {
  const { data: interviewers, isLoading } = useQuery({
    queryKey: ["interviewers"],
    queryFn: () => interviewersAPI.getAll().then((res) => res.data),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          Interviewers ({interviewers?.length || 0})
        </h3>
        <button className="btn btn-primary">
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
                  <button className="text-blue-600 hover:text-blue-800 mr-3">
                    Edit
                  </button>
                  <button className="text-red-600 hover:text-red-800">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const RoomsTable = () => {
  const { data: rooms, isLoading } = useQuery({
    queryKey: ["rooms"],
    queryFn: () => roomsAPI.getAll().then((res) => res.data),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Rooms ({rooms?.length || 0})</h3>
        <button className="btn btn-primary">
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
                  <button className="text-blue-600 hover:text-blue-800 mr-3">
                    Edit
                  </button>
                  <button className="text-red-600 hover:text-red-800">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataManagement;
