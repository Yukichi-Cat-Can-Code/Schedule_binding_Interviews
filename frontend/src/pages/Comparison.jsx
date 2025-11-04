import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { algorithmsAPI } from "../services/api";
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

  const { data: previousResults } = useQuery({
    queryKey: ["algorithmResults"],
    queryFn: () => algorithmsAPI.getResults().then((res) => res.data),
  });

  const compareAlgorithms = useMutation({
    mutationFn: () => algorithmsAPI.compare(["GA", "GREEDY", "SA"]),
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

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">
            Algorithm Comparison
          </h2>
          <p className="text-gray-600 mt-1">
            Compare performance of different scheduling algorithms
          </p>
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

      {/* Comparison Results */}
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
                      {result.fitness?.toFixed(3) || "N/A"}
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
                  fitness: r.fitness || 0,
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
                data={[
                  {
                    metric: "Conflict",
                    GA:
                      (1 -
                        (comparisonResults.results?.find(
                          (r) => r.algorithm === "GA"
                        )?.best_solution?.conflict_score || 0)) *
                      100,
                    GREEDY:
                      (1 -
                        (comparisonResults.results?.find(
                          (r) => r.algorithm === "GREEDY"
                        )?.best_solution?.conflict_score || 0)) *
                      100,
                    SA:
                      (1 -
                        (comparisonResults.results?.find(
                          (r) => r.algorithm === "SA"
                        )?.best_solution?.conflict_score || 0)) *
                      100,
                  },
                  {
                    metric: "Idle Time",
                    GA:
                      (1 -
                        (comparisonResults.results?.find(
                          (r) => r.algorithm === "GA"
                        )?.best_solution?.idle_time_score || 0)) *
                      100,
                    GREEDY:
                      (1 -
                        (comparisonResults.results?.find(
                          (r) => r.algorithm === "GREEDY"
                        )?.best_solution?.idle_time_score || 0)) *
                      100,
                    SA:
                      (1 -
                        (comparisonResults.results?.find(
                          (r) => r.algorithm === "SA"
                        )?.best_solution?.idle_time_score || 0)) *
                      100,
                  },
                  {
                    metric: "Fairness",
                    GA:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "GA"
                      )?.best_solution?.fairness_score || 0) * 100,
                    GREEDY:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "GREEDY"
                      )?.best_solution?.fairness_score || 0) * 100,
                    SA:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "SA"
                      )?.best_solution?.fairness_score || 0) * 100,
                  },
                  {
                    metric: "Matching",
                    GA:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "GA"
                      )?.best_solution?.matching_score || 0) * 100,
                    GREEDY:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "GREEDY"
                      )?.best_solution?.matching_score || 0) * 100,
                    SA:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "SA"
                      )?.best_solution?.matching_score || 0) * 100,
                  },
                  {
                    metric: "Room Usage",
                    GA:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "GA"
                      )?.best_solution?.room_usage_score || 0) * 100,
                    GREEDY:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "GREEDY"
                      )?.best_solution?.room_usage_score || 0) * 100,
                    SA:
                      (comparisonResults.results?.find(
                        (r) => r.algorithm === "SA"
                      )?.best_solution?.room_usage_score || 0) * 100,
                  },
                ]}
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
                  name="Greedy"
                  dataKey="GREEDY"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                />
                <Radar
                  name="SA"
                  dataKey="SA"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
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
                      const colors = ["#3b82f6", "#10b981", "#8b5cf6"];
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
                        {result.fitness?.toFixed(3) || "N/A"}
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
                        {(result.best_solution?.conflict_score * 100).toFixed(
                          1
                        ) || "N/A"}
                        %
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
                        {(result.best_solution?.idle_time_score * 100).toFixed(
                          1
                        ) || "N/A"}
                        %
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
                        {(result.best_solution?.fairness_score * 100).toFixed(
                          1
                        ) || "N/A"}
                        %
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
                        {(result.best_solution?.matching_score * 100).toFixed(
                          1
                        ) || "N/A"}
                        %
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
                        {(result.best_solution?.room_usage_score * 100).toFixed(
                          1
                        ) || "N/A"}
                        %
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
    </div>
  );
};

export default Comparison;
