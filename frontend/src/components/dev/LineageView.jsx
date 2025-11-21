import React from "react";
import { useQuery } from "@tanstack/react-query";
import { algorithmsDevAPI } from "../../services/api";
import TimetableMini from "./TimetableMini";

const LineageView = ({ runId, generation, individual }) => {
  const { data, isLoading, isError } = useQuery({
    queryKey: [
      "ga-dev-lineage",
      runId,
      generation.index,
      individual.individual_id,
    ],
    queryFn: () =>
      algorithmsDevAPI
        .getLineageDetail({
          run_id: runId,
          generation: generation.index,
          individual_id: individual.individual_id,
        })
        .then((res) => res.data),
  });

  if (isLoading) {
    return (
      <div className="text-xs text-gray-500">Loading lineage detail...</div>
    );
  }
  if (isError || !data) {
    return (
      <div className="text-xs text-red-600">
        Lineage detail not available for this individual.
      </div>
    );
  }

  const { parents, child } = data;

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-700">
        Lineage between Gen {generation.index} and Gen {generation.index + 1}.
        Hover or inspect to see which parents spawned this child and what
        changed.
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div>
          <h4 className="text-xs font-semibold mb-1 text-gray-700">
            Parents (Gen {generation.index})
          </h4>
          <div className="space-y-2">
            {(parents || []).map((p) => (
              <div key={p.individual_id}>
                <TimetableMini
                  individual={p}
                  isSelected={false}
                  onClick={() => {}}
                />
              </div>
            ))}
          </div>
        </div>
        <div className="lg:col-span-2">
          <h4 className="text-xs font-semibold mb-1 text-gray-700">
            Child (Gen {generation.index + 1})
          </h4>
          <TimetableMini
            individual={child}
            isSelected={true}
            onClick={() => {}}
          />
        </div>
      </div>
    </div>
  );
};

export default LineageView;
