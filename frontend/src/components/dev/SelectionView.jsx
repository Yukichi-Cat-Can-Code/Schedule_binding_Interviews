import React from "react";

const SelectionView = ({ generation, individual }) => {
  const reps = generation.representatives || [];

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-700">
        Selection in Gen {generation.index}. Highlighted schedules are selected
        as parents.
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {reps.map((ind) => {
          const isParent = ind.selection_meta?.is_selected_parent;
          const prob = ind.selection_meta?.selection_prob ?? null;
          return (
            <div
              key={ind.individual_id}
              className={`border rounded p-2 text-xs ${
                isParent ? "border-yellow-500 bg-yellow-50" : "border-gray-200"
              }`}
            >
              <div className="flex justify-between mb-1">
                <span className="font-semibold">
                  #{ind.rank} d fitness {ind.fitness?.toFixed(3) ?? "-"}
                </span>
                {isParent && (
                  <span className="px-1 rounded bg-yellow-500 text-white">
                    Parent
                  </span>
                )}
              </div>
              <div className="text-gray-600">
                Selection prob:{" "}
                {prob !== null ? `${(prob * 100).toFixed(1)}%` : "-"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SelectionView;
