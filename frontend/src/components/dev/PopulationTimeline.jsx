import React from "react";

const PopulationTimeline = ({
  generations,
  selectedGenerationIndex,
  onSelectGenerationIndex,
}) => {
  if (!generations || generations.length === 0) return null;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900">
          Population Timeline
        </h3>
        <span className="text-xs text-gray-500">
          Rows = generations, columns = representative individuals
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs">
          <thead>
            <tr>
              <th className="px-2 py-1 text-left text-gray-500">Gen</th>
              <th className="px-2 py-1 text-left text-gray-500">
                Individuals (best d worse)
              </th>
            </tr>
          </thead>
          <tbody>
            {generations.map((g) => (
              <tr
                key={g.index}
                className={
                  selectedGenerationIndex === g.index
                    ? "bg-blue-50"
                    : "hover:bg-gray-50"
                }
              >
                <td className="px-2 py-1 whitespace-nowrap">
                  <button
                    type="button"
                    onClick={() => onSelectGenerationIndex(g.index)}
                    className={`px-2 py-1 rounded text-xs ${
                      selectedGenerationIndex === g.index
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    Gen {g.index}
                  </button>
                </td>
                <td className="px-2 py-1">
                  <div className="flex flex-wrap gap-1">
                    {(g.representatives || []).map((ind) => {
                      const fitness = ind.fitness ?? 0;
                      const color =
                        fitness > 0.8
                          ? "bg-green-500"
                          : fitness > 0.5
                          ? "bg-yellow-400"
                          : "bg-red-400";
                      return (
                        <div
                          key={ind.individual_id}
                          className="flex items-center space-x-1 mr-2 mb-1"
                        >
                          <span
                            className={`inline-block w-3 h-3 rounded-full ${color}`}
                          />
                          <span className="text-gray-700">
                            #{ind.rank} ({fitness.toFixed(2)})
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PopulationTimeline;
