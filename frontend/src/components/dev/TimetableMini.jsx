import React from "react";

const TimetableMini = ({ individual, isSelected, onClick }) => {
  const slots = individual.schedule_snapshot || [];
  const rooms = Array.from(
    new Set(slots.map((s) => s.room_name || s.room || "Unknown"))
  );
  const dates = Array.from(new Set(slots.map((s) => s.date))).sort();

  return (
    <div
      className={`border rounded-lg p-2 text-xs cursor-pointer ${
        isSelected ? "border-blue-500 shadow-md" : "border-gray-200"
      }`}
      onClick={onClick}
    >
      <div className="flex justify-between items-center mb-1">
        <div className="font-semibold">
          #{individual.rank} d fitness {individual.fitness?.toFixed(3) ?? "-"}
        </div>
        {individual.selection_meta?.is_selected_parent && (
          <span className="px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-800 text-[10px]">
            Parent
          </span>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr>
              <th className="border border-gray-200 px-1 py-0.5">Room</th>
              {dates.map((d) => (
                <th
                  key={d}
                  className="border border-gray-200 px-1 py-0.5 text-gray-500"
                >
                  {d}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rooms.map((room) => (
              <tr key={room}>
                <td className="border border-gray-200 px-1 py-0.5 text-gray-700">
                  {room}
                </td>
                {dates.map((d) => {
                  const daySlots = slots.filter(
                    (s) =>
                      (s.room_name || s.room || "Unknown") === room &&
                      s.date === d
                  );
                  return (
                    <td
                      key={d}
                      className="border border-gray-200 px-1 py-0.5 align-top"
                    >
                      <div className="space-y-0.5">
                        {daySlots.map((s, idx) => (
                          <div
                            key={idx}
                            className="rounded px-1 py-0.5 text-[10px] text-white"
                            style={{
                              backgroundColor:
                                s.color_hint ||
                                (s.has_conflict ? "#ef4444" : "#3b82f6"),
                            }}
                            title={`${s.applicant_name || "Applicant"} d ${
                              s.interviewer_name || "Interviewer"
                            }\n${s.start_time} d ${s.end_time}`}
                          >
                            {s.applicant_name || "Applicant"} @{" "}
                            {s.start_time?.slice(11, 16) || "?"}
                            {s.has_conflict && " 6a8"}
                          </div>
                        ))}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TimetableMini;
