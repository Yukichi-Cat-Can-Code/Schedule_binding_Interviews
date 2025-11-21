import React from "react";
import { useQuery } from "@tanstack/react-query";
import { algorithmsDevAPI } from "../../services/api";
import TimetableMini from "./TimetableMini";

const MutationView = ({ runId, generation, individual }) => {
  const { data, isLoading, isError } = useQuery({
    queryKey: [
      "ga-dev-mutation",
      runId,
      generation.index,
      individual.individual_id,
    ],
    queryFn: () =>
      algorithmsDevAPI
        .getScheduleDetail({
          run_id: runId,
          generation: generation.index,
          individual_id: individual.individual_id,
        })
        .then((res) => res.data),
  });

  if (isLoading) {
    return (
      <div className="text-xs text-gray-500">Loading mutation detail...</div>
    );
  }
  if (isError || !data) {
    return (
      <div className="text-xs text-red-600">
        Mutation detail not available for this individual.
      </div>
    );
  }

  const { before_mutation, after_mutation, mutations } = data;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-700">
          Mutation for individual #{individual.rank} in Gen {generation.index}.
        </div>
        <div className="text-xs text-gray-500">
          Mutated genes: {mutations?.length ?? 0}
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold mb-1 text-gray-700">
            Before mutation
          </h4>
          <TimetableMini
            individual={before_mutation}
            isSelected={false}
            onClick={() => {}}
          />
        </div>
        <div>
          <h4 className="text-xs font-semibold mb-1 text-gray-700">
            After mutation
          </h4>
          <TimetableMini
            individual={after_mutation}
            isSelected={true}
            onClick={() => {}}
          />
        </div>
      </div>
      {mutations && mutations.length > 0 && (
        <div className="mt-2 max-h-40 overflow-auto border-t border-gray-200 pt-2">
          <h5 className="text-xs font-semibold text-gray-700 mb-1">
            Mutated genes
          </h5>
          <ul className="text-[11px] text-gray-600 space-y-1">
            {mutations.map((m, idx) => (
              <li key={idx}>d {m.description || "Mutation"}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MutationView;
