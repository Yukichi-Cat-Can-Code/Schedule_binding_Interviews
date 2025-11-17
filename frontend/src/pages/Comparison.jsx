import { useState, useMemo } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { algorithmsAPI, sessionsAPI } from "../services/api";
import { useCurrentCompany } from "../hooks/useCurrentCompany";
import toast from "react-hot-toast";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { FiPlay, FiCheckCircle } from "react-icons/fi";

const Comparison = () => {
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonResults, setComparisonResults] = useState(null);
  const [sessionId, setSessionId] = useState("");

  const { company, companyId } = useCurrentCompany();

  const { data: sessions } = useQuery({
    queryKey: ["sessions", companyId],
    enabled: !!companyId,
    queryFn: () =>
      sessionsAPI.getAll({ company_id: companyId }).then((res) => res.data),
  });

  const { data: previousResults } = useQuery({
    queryKey: ["algorithmResults", companyId, sessionId],
    enabled: !!companyId,
    queryFn: () =>
      algorithmsAPI
        .getResults({
          company_id: companyId,
          session_id: sessionId || undefined,
        })
        .then((res) => res.data),
  });

  const compareAlgorithms = useMutation({
    mutationFn: () =>
      algorithmsAPI.compare({
        config: {
          GA: {},
          GA2: {},
          GA3: {},
          GA4: {},
        },
        company_id: companyId,
        session_id: sessionId || undefined,
      }),
    onSuccess: (response) => {
      setComparisonResults(response.data);
      toast.success("Comparison completed!");
      setIsComparing(false);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to compare algorithms");
      setIsComparing(false);
    },
  });

  const handleCompare = () => {
    setIsComparing(true);
    compareAlgorithms.mutate();
  };

  // Derived interviewer load chart data
  const interviewerLoadData = useMemo(() => {
    if (!comparisonResults?.results) return [];
    const merged = {};
    comparisonResults.results.forEach((r) => {
      Object.entries(r.interviewer_load || {}).forEach(([id, count]) => {
        merged[id] = merged[id] || { interviewer: id };
        merged[id][r.algorithm] = count;
      });
    });
    return Object.values(merged);
  }, [comparisonResults]);

  const roomUtilizationData = useMemo(() => {
    if (!comparisonResults?.results) return [];
    const merged = {};
    comparisonResults.results.forEach((r) => {
      Object.entries(r.room_utilization || {}).forEach(([id, count]) => {
        merged[id] = merged[id] || { room: id };
        merged[id][r.algorithm] = count;
      });
    });
    return Object.values(merged);
  }, [comparisonResults]);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="space-y-1">
          <h2 className="text-3xl font-bold text-gray-900">
            Algorithm Comparison
          </h2>
          <p className="text-gray-600">Compare performance & resource usage</p>
          <div className="flex items-center space-x-2 text-sm text-gray-700">
            <span className="font-medium">Company:</span>
            <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100">
              {company?.name || company?.code || "Loading..."}
            </span>
          </div>
          <div className="flex items-center space-x-2 mt-2">
            <label className="text-sm font-medium text-gray-700">
              Session:
            </label>
            <select
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All sessions</option>
              {(sessions || []).map((s) => (
                <option key={s._id} value={s._id}>
                  {s.name || s.code || s._id}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={handleCompare}
          disabled={isComparing}
          className="btn btn-primary"
        >
          {isComparing ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
              <span>Running Comparison...</span>
            </>
          ) : (
            <>
              <FiPlay className="w-5 h-5" />
              <span>Run Comparison</span>
            </>
          )}
        </button>
      </div>
      {/* Interviewer Load Chart */}
      {interviewerLoadData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">
            Interviewer Load (Number of Assigned Slots)
          </h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={interviewerLoadData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="interviewer" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="GA" stackId="a" fill="#3b82f6" />
              <Bar dataKey="GA2" stackId="a" fill="#10b981" />
              <Bar dataKey="GA3" stackId="a" fill="#8b5cf6" />
              <Bar dataKey="GA4" stackId="a" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Room Utilization Chart */}
      {roomUtilizationData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">
            Room Utilization (Number of Used Slots)
          </h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={roomUtilizationData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="room" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="GA" stackId="a" fill="#3b82f6" />
              <Bar dataKey="GA2" stackId="a" fill="#10b981" />
              <Bar dataKey="GA3" stackId="a" fill="#8b5cf6" />
              <Bar dataKey="GA4" stackId="a" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Comparison Results (current run) */}
      {comparisonResults && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {comparisonResults.results?.map((result) => (
              <div
                key={result.algorithm}
                className="bg-white rounded-lg shadow p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">{result.algorithm}</h3>
                  {result.fitness ===
                    Math.max(
                      ...comparisonResults.results.map((r) => r.fitness || 0)
                    ) && <FiCheckCircle className="w-6 h-6 text-green-500" />}
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-600">Fitness Score</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {result.fitness_score?.toFixed(3) ||
                        result.fitness?.toFixed(3) ||
                        "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Execution Time</p>
                    <p className="text-lg font-semibold text-gray-700">
                      {result.execution_time?.toFixed(2) ||
                        result.generations ||
                        "N/A"}
                      s
                    </p>
                  </div>
                  {result.generations && (
                    <div>
                      <p className="text-sm text-gray-600">
                        Generations/Iterations
                      </p>
                      <p className="text-lg font-semibold text-gray-700">
                        {result.generations || result.iterations}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Fitness Comparison Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">
              Fitness Score Comparison
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={comparisonResults.results?.map((r) => ({
                  algorithm: r.algorithm,
                  fitness: r.fitness_score || r.fitness || 0,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="algorithm" />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Legend />
                <Bar dataKey="fitness" fill="#3b82f6" name="Fitness Score" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Execution Time Comparison */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">
              Execution Time Comparison
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={comparisonResults.results?.map((r) => ({
                  algorithm: r.algorithm,
                  time: r.execution_time || 0,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="algorithm" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="time" fill="#10b981" name="Execution Time (s)" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Detailed Metrics Radar Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">
              Detailed Metrics Comparison
            </h3>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart
                data={(() => {
                  const algos = ["GA", "GA2", "GA3", "GA4"];
                  const findScore = (algo, key) => {
                    const r = comparisonResults.results?.find(
                      (x) => x.algorithm === algo
                    );
                    if (!r) return 0;
                    if (key === "conflict" || key === "idle") {
                      return (
                        (1 - (r[key + "_score"] ?? r[key + "_score"] ?? 0)) *
                        100
                      );
                    }
                    return (r[key + "_score"] ?? 0) * 100;
                  };
                  return [
                    "conflict",
                    "idle",
                    "fairness",
                    "matching",
                    "room_usage",
                  ].map((metric) => {
                    const labelMap = {
                      conflict: "Conflict",
                      idle: "Idle Time",
                      fairness: "Fairness",
                      matching: "Matching",
                      room_usage: "Room Usage",
                    };
                    const row = { metric: labelMap[metric] };
                    algos.forEach((a) => {
                      // keys stored as conflict_score, idle_time_score, fairness_score, matching_score, room_usage_score
                      const keyName = metric === "idle" ? "idle_time" : metric;
                      row[a] = findScore(a, keyName);
                    });
                    return row;
                  });
                })()}
              >
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis domain={[0, 100]} />
                <Radar
                  name="GA"
                  dataKey="GA"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
                <Radar
                  name="GA2"
                  dataKey="GA2"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                />
                <Radar
                  name="GA3"
                  dataKey="GA3"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
                  fillOpacity={0.6}
                />
                <Radar
                  name="GA4"
                  dataKey="GA4"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.6}
                />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Convergence Chart (for GA and SA) */}
          {comparisonResults.results?.some((r) => r.fitness_history) && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">
                Convergence Over Time
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="generation"
                    label={{
                      value: "Generation/Iteration",
                      position: "insideBottom",
                      offset: -5,
                    }}
                  />
                  <YAxis
                    domain={[0, 1]}
                    label={{
                      value: "Fitness",
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />
                  <Tooltip />
                  <Legend />
                  {comparisonResults.results?.map((result, idx) => {
                    if (result.fitness_history) {
                      const data = result.fitness_history.map(
                        (fitness, gen) => ({
                          generation: gen,
                          [result.algorithm]: fitness,
                        })
                      );
                      const colors = [
                        "#3b82f6",
                        "#10b981",
                        "#8b5cf6",
                        "#f59e0b",
                      ];
                      return (
                        <Line
                          key={result.algorithm}
                          data={data}
                          type="monotone"
                          dataKey={result.algorithm}
                          stroke={colors[idx]}
                          strokeWidth={2}
                          dot={false}
                        />
                      );
                    }
                    return null;
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Comparison Table */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">
              Side-by-Side Comparison
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Metric
                    </th>
                    {comparisonResults.results?.map((result) => (
                      <th
                        key={result.algorithm}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                      >
                        {result.algorithm}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      Fitness Score
                    </td>
                    {comparisonResults.results?.map((result) => (
                      <td
                        key={result.algorithm}
                        className="px-6 py-4 whitespace-nowrap"
                      >
                        {result.fitness_score?.toFixed(3) ||
                          result.fitness?.toFixed(3) ||
                          "N/A"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      Execution Time
                    </td>
                    {comparisonResults.results?.map((result) => (
                      <td
                        key={result.algorithm}
                        className="px-6 py-4 whitespace-nowrap"
                      >
                        {result.execution_time?.toFixed(2) || "N/A"}s
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      Conflict Score
                    </td>
                    {comparisonResults.results?.map((result) => (
                      <td
                        key={result.algorithm}
                        className="px-6 py-4 whitespace-nowrap"
                      >
                        {(result.conflict_score * 100).toFixed(1) || "N/A"}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      Idle Time
                    </td>
                    {comparisonResults.results?.map((result) => (
                      <td
                        key={result.algorithm}
                        className="px-6 py-4 whitespace-nowrap"
                      >
                        {(result.idle_time_score * 100).toFixed(1) || "N/A"}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      Fairness
                    </td>
                    {comparisonResults.results?.map((result) => (
                      <td
                        key={result.algorithm}
                        className="px-6 py-4 whitespace-nowrap"
                      >
                        {(result.fairness_score * 100).toFixed(1) || "N/A"}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      Matching
                    </td>
                    {comparisonResults.results?.map((result) => (
                      <td
                        key={result.algorithm}
                        className="px-6 py-4 whitespace-nowrap"
                      >
                        {(result.matching_score * 100).toFixed(1) || "N/A"}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      Room Usage
                    </td>
                    {comparisonResults.results?.map((result) => (
                      <td
                        key={result.algorithm}
                        className="px-6 py-4 whitespace-nowrap"
                      >
                        {(result.room_usage_score * 100).toFixed(1) || "N/A"}%
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Previous Results */}
      {previousResults && previousResults.length > 0 && !comparisonResults && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Previous Results</h3>
          <div className="space-y-3">
            {previousResults.slice(0, 5).map((result) => (
              <div
                key={result._id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium">{result.algorithm}</p>
                  <p className="text-sm text-gray-600">
                    {new Date(result.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">
                    {result.fitness_score.toFixed(3)}
                  </p>
                  <p className="text-sm text-gray-600">
                    {result.execution_time.toFixed(2)}s
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historical best runs table (per session) */}
      {previousResults && previousResults.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Algorithm Runs</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">
                    Algorithm
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">
                    Fitness
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">
                    Conflicts
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">
                    Fairness
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">
                    Idle Time
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">
                    Room Usage
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">
                    Exec Time (s)
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {previousResults.map((r) => (
                  <tr key={r._id || r.id}>
                    <td className="px-3 py-2 whitespace-nowrap font-medium text-gray-900">
                      {r.algorithm}
                    </td>
                    <td className="px-3 py-2">
                      {(r.fitness_score ?? r.final_fitness ?? 0).toFixed(3)}
                    </td>
                    <td className="px-3 py-2">{r.conflict_score ?? 0}</td>
                    <td className="px-3 py-2">{r.fairness_score ?? 0}</td>
                    <td className="px-3 py-2">{r.idle_time_score ?? 0}</td>
                    <td className="px-3 py-2">{r.room_usage_score ?? 0}</td>
                    <td className="px-3 py-2">
                      {(r.execution_time ?? 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Comparison;
