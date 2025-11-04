import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { schedulesAPI } from "../services/api";
import { format, parseISO } from "date-fns";
import { FiAlertCircle } from "react-icons/fi";

const ScheduleView = () => {
  const [viewMode, setViewMode] = useState("timeline"); // timeline | table

  const { data: schedules, isLoading } = useQuery({
    queryKey: ["schedules"],
    queryFn: () => schedulesAPI.getAll().then((res) => res.data),
  });

  const { data: timeline } = useQuery({
    queryKey: ["timeline"],
    queryFn: () => schedulesAPI.getTimeline().then((res) => res.data),
  });

  const { data: conflicts } = useQuery({
    queryKey: ["conflicts"],
    queryFn: () => schedulesAPI.getConflicts().then((res) => res.data),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Schedule View</h2>
          <p className="text-gray-600 mt-1">
            View and manage interview schedules
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setViewMode("timeline")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              viewMode === "timeline"
                ? "bg-blue-500 text-white"
                : "bg-white text-gray-700 border"
            }`}
          >
            Timeline View
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              viewMode === "table"
                ? "bg-blue-500 text-white"
                : "bg-white text-gray-700 border"
            }`}
          >
            Table View
          </button>
        </div>
      </div>

      {/* Conflicts Alert */}
      {conflicts && conflicts.count > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <FiAlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                {conflicts.count} Conflicts Detected
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <ul className="list-disc list-inside space-y-1">
                  {conflicts.conflicts.slice(0, 3).map((conflict, idx) => (
                    <li key={idx}>
                      {conflict.type === "interviewer"
                        ? `Interviewer ${conflict.interviewer} has overlapping schedules`
                        : `Room ${conflict.room} is double-booked`}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {viewMode === "timeline" ? (
          <TimelineView timeline={timeline} />
        ) : (
          <TableView schedules={schedules} />
        )}
      </div>
    </div>
  );
};

const TimelineView = ({ timeline }) => {
  if (!timeline || Object.keys(timeline).length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No schedules available. Run an algorithm to generate schedules.
      </div>
    );
  }

  const positionColors = {
    Media: "bg-blue-500",
    HR: "bg-green-500",
    Event: "bg-purple-500",
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Timeline by Room</h3>
      {Object.entries(timeline).map(([roomId, slots]) => (
        <div key={roomId} className="border rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">{roomId}</h4>
          <div className="space-y-2">
            {slots.map((slot) => (
              <div
                key={slot.id}
                className="timeline-slot p-3 rounded-lg border-l-4 bg-gray-50 hover:bg-gray-100 cursor-pointer"
                style={{
                  borderLeftColor: positionColors[slot.position] || "#9ca3af",
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">
                      {slot.applicant}
                    </p>
                    <p className="text-sm text-gray-600">
                      Interviewer: {slot.interviewer}
                    </p>
                    <p className="text-sm text-gray-600">
                      Position:{" "}
                      <span className="font-medium">{slot.position}</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {format(parseISO(slot.start), "HH:mm")} -{" "}
                      {format(parseISO(slot.end), "HH:mm")}
                    </p>
                    <span
                      className={`inline-block px-2 py-1 text-xs rounded-full mt-1 ${
                        slot.status === "scheduled"
                          ? "bg-green-100 text-green-800"
                          : slot.status === "completed"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {slot.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const TableView = ({ schedules }) => {
  if (!schedules || schedules.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No schedules available. Run an algorithm to generate schedules.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Applicant
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Interviewer
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Room
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Time
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {schedules.map((schedule) => (
            <tr key={schedule._id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="font-medium text-gray-900">
                    {schedule.applicant_detail?.full_name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {schedule.applicant_detail?.position}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {schedule.interviewer_detail?.full_name}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {schedule.room_detail?.room_code}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm">
                  {format(parseISO(schedule.start_time), "MMM dd, HH:mm")} -
                  {format(parseISO(schedule.end_time), "HH:mm")}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    schedule.status === "scheduled"
                      ? "bg-green-100 text-green-800"
                      : schedule.status === "completed"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {schedule.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ScheduleView;
