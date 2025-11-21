import React from "react";
import { useQuery } from "@tanstack/react-query";
import { algorithmsDevAPI } from "../../services/api";
import TimetableMini from "./TimetableMini";

const CrossoverView = ({ runId, generation, individual }) => {
  const { data, isLoading, isError } = useQuery({
    queryKey: [
      "ga-dev-crossover",
      runId,
      generation.index,
      individual.individual_id,
    ],
    queryFn: () =>
      algorithmsDevAPI
        .getCrossoverDetail({
          run_id: runId,
          generation: generation.index,
          child_id: individual.individual_id,
        })
        .then((res) => res.data),
  });

  if (isLoading) {
    return (
      <div className="text-xs text-gray-500">Loading crossover detail...</div>
    );
  }
  if (isError || !data) {
    return (
      <div className="text-xs text-red-600">
        Crossover detail not available for this individual.
      </div>
    );
  }

  const { parent_a, parent_b, child_before, child_after } = data;

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-700">
        Crossover for child #{individual.rank} in Gen {generation.index}. Green
        segments inherited from Parent A, orange from Parent B.
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div>
          <h4 className="text-xs font-semibold mb-1 text-gray-700">Parent A</h4>
          <TimetableMini
            individual={parent_a}
            isSelected={false}
            onClick={() => {}}
          />
        </div>
        <div>
          <h4 className="text-xs font-semibold mb-1 text-gray-700">Parent B</h4>
          <TimetableMini
            individual={parent_b}
            isSelected={false}
            onClick={() => {}}
          />
        </div>
        <div>
          <h4 className="text-xs font-semibold mb-1 text-gray-700">
            Child after crossover
          </h4>
          <TimetableMini
            individual={child_before}
            isSelected={true}
            onClick={() => {}}
          />
        </div>
      </div>
    </div>
  );
};

export default CrossoverView;
