import React from "react";
import TimetableMini from "./TimetableMini";

const TimetableMiniGrid = ({
  generation,
  selectedIndividualId,
  onSelectIndividual,
}) => {
  if (!generation) return null;
  const reps = generation.representatives || [];

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Generation {generation.index} d Representative Schedules
          </h3>
          <p className="text-xs text-gray-500">
            Mini timetable for top individuals in this generation.
          </p>
        </div>
        <div className="text-xs text-gray-500">
          Best fitness: {generation.stats?.best_fitness?.toFixed(3) ?? "-"}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {reps.map((ind) => (
          <TimetableMini
            key={ind.individual_id}
            individual={ind}
            isSelected={selectedIndividualId === ind.individual_id}
            onClick={() => onSelectIndividual(ind)}
          />
        ))}
      </div>
    </div>
  );
};

export default TimetableMiniGrid;
