import { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { dataAPI, companiesAPI } from "../services/api";

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

  const [companyMap, setCompanyMap] = useState({});

  useEffect(() => {
    if (!logs || !Array.isArray(logs)) return;
    const ids = Array.from(
      new Set(logs.map((l) => l.company_id).filter(Boolean))
    );
    if (ids.length === 0) return;

    let mounted = true;
    (async () => {
      const pairs = await Promise.all(
        ids.map(async (id) => {
          try {
            const res = await companiesAPI.getById(id);
            const name = res?.data?.name || res?.data?.company_name || null;
            return [id, name];
          } catch (e) {
            return [id, null];
          }
        })
      );
      if (!mounted) return;
      const map = {};
      for (const [id, name] of pairs) {
        if (name) map[id] = name;
      }
      setCompanyMap((s) => ({ ...s, ...map }));
    })();

    return () => {
      mounted = false;
    };
  }, [logs]);

  const sanitizeDetails = (obj) => {
    if (obj === null || obj === undefined) return obj;
    if (typeof obj !== "object") return obj;

    if (Array.isArray(obj)) {
      // For arrays, sanitize each element; for arrays of ids show counts
      const isIdArray = obj.every(
        (v) => typeof v === "string" && /^[0-9a-fA-F]{8,}$/.test(v)
      );
      if (isIdArray) return `(${obj.length} items)`;
      return obj.map((v) => sanitizeDetails(v));
    }

    const out = {};
    for (const [k, v] of Object.entries(obj)) {
      // Skip keys that are likely identifiers
      if (/(_id|company_id|user_id|session_id|resource_id)$/.test(k)) continue;

      // collapse long id-like string values
      if (typeof v === "string" && /^[0-9a-fA-F]{8,}$/.test(v)) continue;

      // make some keys more friendly
      if (k === "data_keys" && Array.isArray(v)) {
        out["Data keys"] = v.join(", ");
        continue;
      }
      if (k === "execution_time" && typeof v === "number") {
        out["Execution time (s)"] = v.toFixed ? v.toFixed(2) : v;
        continue;
      }
      if (k === "generations") {
        out["Generations"] = v;
        continue;
      }

      out[k] = sanitizeDetails(v);
    }
    return out;
  };

  const getUserDisplay = (log) => {
    if (!log) return "-";
    if (log.user_email) return log.user_email;
    if (log.user_name) return log.user_name;
    // try details common fields
    const d = log.details || {};
    if (d.user_email) return d.user_email;
    if (d.user && typeof d.user === "object") {
      return d.user.email || d.user.username || d.user.name || null;
    }
    if (d.user_email) return d.user_email;
    if (log.user_id) return String(log.user_id).slice(0, 8) + "...";
    return "-";
  };

  const getRoleDisplay = (log) => {
    if (!log) return "-";
    if (log.role) return log.role;
    const d = log.details || {};
    if (d.role) return d.role;
    if (d.user_role) return d.user_role;
    if (d.role_name) return d.role_name;
    // if user object includes role
    if (d.user && typeof d.user === "object" && d.user.role) return d.user.role;
    return "-";
  };

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
                      {getUserDisplay(log)}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      {log.company_id ? companyMap[log.company_id] || "-" : "-"}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      {getRoleDisplay(log)}
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
                      {log.details ? (
                        <>
                          <pre className="text-xs text-gray-600 whitespace-pre-wrap break-words">
                            {JSON.stringify(
                              sanitizeDetails(log.details),
                              null,
                              2
                            )}
                          </pre>
                        </>
                      ) : (
                        "-"
                      )}
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
