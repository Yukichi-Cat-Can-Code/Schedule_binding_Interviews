import React from "react";
import SelectionView from "./SelectionView";
import CrossoverView from "./CrossoverView";
import MutationView from "./MutationView";
import LineageView from "./LineageView";

const GeneticStepPanel = ({
  runId,
  generation,
  individual,
  selectedStep,
  onChangeStep,
}) => {
  if (!generation) return null;

  const tabs = [
    { id: "selection", label: "Selection" },
    { id: "crossover", label: "Crossover" },
    { id: "mutation", label: "Mutation" },
    { id: "lineage", label: "Gen G d G+1" },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            GA Steps d Generation {generation.index}
          </h3>
          <p className="text-xs text-gray-500">
            Select an individual above to inspect detailed genetic operations.
          </p>
        </div>
        <div className="flex space-x-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => onChangeStep(t.id)}
              className={`px-2 py-1 text-xs rounded border ${
                selectedStep === t.id
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-gray-100 text-gray-700 border-gray-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {!individual && (
        <div className="text-xs text-gray-500">
          Select a schedule above to see details for selection, crossover and
          mutation.
        </div>
      )}

      {individual && selectedStep === "selection" && (
        <SelectionView generation={generation} individual={individual} />
      )}
      {individual && selectedStep === "crossover" && (
        <CrossoverView
          runId={runId}
          generation={generation}
          individual={individual}
        />
      )}
      {individual && selectedStep === "mutation" && (
        <MutationView
          runId={runId}
          generation={generation}
          individual={individual}
        />
      )}
      {individual && selectedStep === "lineage" && (
        <LineageView
          runId={runId}
          generation={generation}
          individual={individual}
        />
      )}
    </div>
  );
};

export default GeneticStepPanel;
