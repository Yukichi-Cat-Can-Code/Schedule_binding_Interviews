import React from "react";
import { useQuery } from "@tanstack/react-query";
import { algorithmsDevAPI } from "../services/api";
import PopulationTimeline from "../components/dev/PopulationTimeline";
import TimetableMiniGrid from "../components/dev/TimetableMiniGrid";
import GeneticStepPanel from "../components/dev/GeneticStepPanel";

const DevMode = () => {
  const [selectedGeneration, setSelectedGeneration] = React.useState(null);
  const [selectedIndividual, setSelectedIndividual] = React.useState(null);
  const [selectedStep, setSelectedStep] = React.useState("selection");

  const {
    data: devRun,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["ga-dev-run"],
    queryFn: () => algorithmsDevAPI.getLatestRun().then((res) => res.data),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (isError || !devRun) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
        <p className="font-semibold mb-1">Dev run not available</p>
        <p className="text-sm">
          {error?.message ||
            "No GA debug run found. Run an algorithm in dev mode on the backend and try again."}
        </p>
      </div>
    );
  }

  const generations = devRun.generations || [];

  const importantGenList = React.useMemo(() => {
    if (!generations.length) return [];
    const indexes = new Set([0, 5, 10, 20]);
    const last = generations[generations.length - 1]?.index;
    if (typeof last === "number") indexes.add(last);
    const byIndex = Object.fromEntries(generations.map((g) => [g.index, g]));
    return Array.from(indexes)
      .sort((a, b) => a - b)
      .map((idx) => byIndex[idx])
      .filter(Boolean);
  }, [generations]);

  const currentGen =
    selectedGeneration || importantGenList[0] || generations[0] || null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">GA Dev Mode</h2>
        <p className="text-gray-600 mt-1">
          Visualize population evolution, selection, crossover and mutation
          across generations.
        </p>
      </div>

      <PopulationTimeline
        generations={importantGenList}
        selectedGenerationIndex={currentGen?.index ?? null}
        onSelectGenerationIndex={(idx) => {
          const found = generations.find((g) => g.index === idx) || null;
          setSelectedGeneration(found);
          setSelectedIndividual(null);
        }}
      />

      <TimetableMiniGrid
        generation={currentGen}
        selectedIndividualId={selectedIndividual?.individual_id ?? null}
        onSelectIndividual={setSelectedIndividual}
      />

      <GeneticStepPanel
        runId={devRun.run_id}
        generation={currentGen}
        individual={selectedIndividual}
        selectedStep={selectedStep}
        onChangeStep={setSelectedStep}
      />
    </div>
  );
};

export default DevMode;
