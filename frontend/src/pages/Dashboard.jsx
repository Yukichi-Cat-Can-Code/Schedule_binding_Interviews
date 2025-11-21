import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { dataAPI, schedulesAPI, sessionsAPI } from "../services/api";
import { useCurrentCompany } from "../hooks/useCurrentCompany";
import { FiUsers, FiUserCheck, FiHome, FiCalendar } from "react-icons/fi";

const Dashboard = () => {
  const navigate = useNavigate();
  const { companyId } = useCurrentCompany();
  const { data: sessions } = useQuery({
    queryKey: ["sessions", companyId || "all"],
    enabled: !!companyId,
    queryFn: () => sessionsAPI.getAll().then((res) => res.data),
  });

  // Persist selected session across refreshes but ensure it's valid for current company
  const [selectedSessionId, setSelectedSessionId] = React.useState(() =>
    typeof window !== "undefined"
      ? localStorage.getItem("selected_session") || ""
      : ""
  );

  // When there is exactly one session for the company, auto-select it
  // so the dashboard immediately reflects that active context.
  React.useEffect(() => {
    if (sessions && sessions.length === 1 && !selectedSessionId) {
      setSelectedSessionId(sessions[0]._id);
    }
  }, [sessions, selectedSessionId]);

  // If the selected session is not part of the currently-loaded sessions (e.g. was
  // left over from a different company), clear it so statistics are not filtered
  // by an unrelated session id.
  React.useEffect(() => {
    if (!sessions) return;
    if (selectedSessionId) {
      const found = sessions.find((s) => s._id === selectedSessionId);
      if (!found) {
        setSelectedSessionId("");
        try {
          localStorage.removeItem("selected_session");
        } catch (e) {}
      }
    }
  }, [sessions, selectedSessionId]);

  const { data: stats, isLoading } = useQuery({
    queryKey: ["statistics", companyId, selectedSessionId],
    enabled: !!companyId,
    queryFn: () =>
      dataAPI
        .getStatistics({
          ...(selectedSessionId ? { session_id: selectedSessionId } : {}),
        })
        .then((res) => res.data),
  });

  const { data: conflicts } = useQuery({
    queryKey: ["conflicts", companyId],
    enabled: !!companyId,
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
          Overview of your interview scheduling system (per session)
        </p>
      </div>
      <div className="mt-2">
        <label className="text-sm font-medium text-gray-700 mr-2">
          Session:
        </label>
        <select
          className="px-2 py-1 border rounded-md text-sm"
          value={selectedSessionId}
          onChange={(e) => {
            const v = e.target.value || "";
            setSelectedSessionId(v);
            try {
              if (v) localStorage.setItem("selected_session", v);
              else localStorage.removeItem("selected_session");
            } catch (e) {}
          }}
        >
          <option value="">All sessions</option>
          {(sessions || []).map((s) => (
            <option key={s._id} value={s._id}>
              {s.name || s.code || s._id}
            </option>
          ))}
        </select>
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

      {/* Position Distribution (Applicants & Interviewers) */}
      {stats?.applicants?.by_position && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Applicants by Position
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(stats.applicants.by_position).map(
                ([name, count]) => (
                  <div
                    key={`app-${name}`}
                    className="text-center p-4 bg-gray-50 rounded"
                  >
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                    <p className="text-sm text-gray-600">{name}</p>
                  </div>
                )
              )}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Interviewers by Position
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(stats.interviewers.by_position).map(
                ([name, count]) => (
                  <div
                    key={`int-${name}`}
                    className="text-center p-4 bg-gray-50 rounded"
                  >
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                    <p className="text-sm text-gray-600">{name}</p>
                  </div>
                )
              )}
            </div>
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
            onClick={() => navigate("/data")}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors cursor-pointer"
          >
            <p className="font-medium text-gray-900">Import Data</p>
            <p className="text-sm text-gray-600 mt-1">Upload Excel file</p>
          </button>
          <button
            onClick={() => navigate("/config")}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors cursor-pointer"
          >
            <p className="font-medium text-gray-900">Run Algorithm</p>
            <p className="text-sm text-gray-600 mt-1">Generate schedule</p>
          </button>
          <button
            onClick={() => navigate("/compare")}
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
