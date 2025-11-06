import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { dataAPI, schedulesAPI } from "../services/api";
import { FiUsers, FiUserCheck, FiHome, FiCalendar } from "react-icons/fi";

const Dashboard = () => {
  const navigate = useNavigate();
  const { data: stats, isLoading } = useQuery({
    queryKey: ["statistics"],
    queryFn: () => dataAPI.getStatistics().then((res) => res.data),
  });

  const { data: conflicts } = useQuery({
    queryKey: ["conflicts"],
    queryFn: () => schedulesAPI.getConflicts().then((res) => res.data),
  });

  const statCards = [
    {
      title: "Applicants",
      value: stats?.applicants?.total || 0,
      icon: FiUsers,
      color: "bg-blue-500",
    },
    {
      title: "Interviewers",
      value: stats?.interviewers?.total || 0,
      icon: FiUserCheck,
      color: "bg-green-500",
    },
    {
      title: "Rooms",
      value: stats?.rooms?.total || 0,
      icon: FiHome,
      color: "bg-purple-500",
    },
    {
      title: "Schedules",
      value: stats?.schedules?.total || 0,
      icon: FiCalendar,
      color: "bg-orange-500",
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-600 mt-1">
          Overview of your interview scheduling system
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => (
          <div key={card.title} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{card.title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {card.value}
                </p>
              </div>
              <div className={`${card.color} p-3 rounded-lg`}>
                <card.icon className="w-8 h-8 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Position Distribution */}
      {stats?.applicants && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Applicants by Position
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(stats.applicants)
              .filter(([key]) => key !== "total")
              .map(([position, count]) => (
                <div
                  key={position}
                  className="text-center p-4 bg-gray-50 rounded"
                >
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-600">{position}</p>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Conflicts Alert */}
      {conflicts && conflicts.count > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                {conflicts.count} scheduling conflicts detected
              </h3>
              <p className="text-sm text-red-700 mt-1">
                Please review and resolve conflicts in the Schedule View
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate("/data-management")}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors cursor-pointer"
          >
            <p className="font-medium text-gray-900">Import Data</p>
            <p className="text-sm text-gray-600 mt-1">Upload Excel file</p>
          </button>
          <button
            onClick={() => navigate("/algorithm-settings")}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors cursor-pointer"
          >
            <p className="font-medium text-gray-900">Run Algorithm</p>
            <p className="text-sm text-gray-600 mt-1">Generate schedule</p>
          </button>
          <button
            onClick={() => navigate("/comparison")}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors cursor-pointer"
          >
            <p className="font-medium text-gray-900">Compare Results</p>
            <p className="text-sm text-gray-600 mt-1">View analysis</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
