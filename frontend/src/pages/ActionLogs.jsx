import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { dataAPI } from "../services/api";

const ACTION_OPTIONS = [
  { value: "", label: "All actions" },
  { value: "IMPORT_EXCEL", label: "Import Excel" },
  { value: "EXPORT_SCHEDULE", label: "Export schedule" },
  { value: "RUN_ALGORITHM", label: "Run algorithm" },
];

function ActionLogs() {
  const [actionType, setActionType] = useState("");

  const {
    data: logs,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["action-logs", actionType],
    queryFn: () =>
      dataAPI.getLogs({ actionType, limit: 200 }).then((res) => res.data),
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Action Logs</h2>
        <p className="text-gray-600 mt-1">
          Audit trail of important operations (imports, exports, algorithms)
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-4 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Action type
          </label>
          <select
            value={actionType}
            onChange={(e) => setActionType(e.target.value)}
            className="mt-1 block w-56 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
          >
            {ACTION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="min-w-full overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Company
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resource
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200 text-sm">
              {isLoading && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-6 text-center text-gray-500"
                  >
                    Loading logs...
                  </td>
                </tr>
              )}
              {isError && !isLoading && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-6 text-center text-red-500"
                  >
                    Failed to load logs
                  </td>
                </tr>
              )}
              {!isLoading && !isError && (!logs || logs.length === 0) && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-6 text-center text-gray-500"
                  >
                    No logs found
                  </td>
                </tr>
              )}
              {!isLoading &&
                !isError &&
                logs &&
                logs.map((log) => (
                  <tr key={log.id || log._id}>
                    <td className="px-4 py-2 whitespace-nowrap text-gray-900">
                      {log.created_at
                        ? new Date(log.created_at).toLocaleString()
                        : "-"}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      {log.user_email || log.user_id || "-"}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      {log.company_id || "-"}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      {log.role || "-"}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap font-medium">
                      {log.action_type}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      {log.resource_type && log.resource_id
                        ? `${log.resource_type} / ${log.resource_id}`
                        : "-"}
                    </td>
                    <td className="px-4 py-2 align-top max-w-xs">
                      <pre className="text-xs text-gray-600 whitespace-pre-wrap break-words">
                        {log.details
                          ? JSON.stringify(log.details, null, 2)
                          : "-"}
                      </pre>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default ActionLogs;
