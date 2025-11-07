import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { schedulesAPI, sessionsAPI, positionsAPI } from "../services/api";
import { format, parseISO } from "date-fns";
import { FiAlertCircle } from "react-icons/fi";

const ScheduleView = () => {
  const [viewMode, setViewMode] = useState("timeline"); // timeline | table
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [selectedDate, setSelectedDate] = useState(""); // ISO date filter

  // Sessions
  const { data: sessions } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => sessionsAPI.getAll().then((res) => res.data),
  });

  const { data: activeSession } = useQuery({
    queryKey: ["sessions", "active"],
    queryFn: () => sessionsAPI.getActive().then((res) => res.data),
  });

  useEffect(() => {
    if (activeSession?._id && !selectedSessionId) {
      setSelectedSessionId(activeSession._id);
    }
  }, [activeSession, selectedSessionId]);

  // Positions for code->name mapping
  const { data: positions } = useQuery({
    queryKey: ["positions"],
    queryFn: () => positionsAPI.getAll().then((res) => res.data),
  });
  const positionMap = useMemo(() => {
    const map = {};
    (positions || []).forEach((p) => (map[p.code] = p.name));
    return map;
  }, [positions]);

  const params = selectedSessionId
    ? { session_id: selectedSessionId }
    : undefined;

  const { data: schedules, isLoading } = useQuery({
    queryKey: ["schedules", params?.session_id || "all"],
    queryFn: () => schedulesAPI.getAll(params).then((res) => res.data),
  });

  const { data: timeline } = useQuery({
    queryKey: ["timeline", params?.session_id || "all"],
    queryFn: () => schedulesAPI.getTimeline(params).then((res) => res.data),
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
        <div className="flex items-center space-x-3">
          {/* Session Filter */}
          <select
            className="px-3 py-2 border rounded-md text-sm"
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
          >
            <option value="">All sessions</option>
            {(sessions || []).map((s) => (
              <option key={s._id} value={s._id}>
                {s.name || s.code || s._id}
              </option>
            ))}
          </select>
          {/* Date Filter (client-side) */}
          <select
            className="px-3 py-2 border rounded-md text-sm"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          >
            <option value="">All dates</option>
            {Array.from(
              new Set(
                (schedules || []).map(
                  (s) => s.interview_date || s.start_time?.slice(0, 10)
                )
              )
            )
              .filter(Boolean)
              .sort()
              .map((d) => (
                <option key={d} value={d}>
                  {new Date(d).toLocaleDateString("vi-VN", {
                    weekday: "short",
                    day: "2-digit",
                    month: "2-digit",
                  })}
                </option>
              ))}
          </select>
          {/* View Switch */}
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
          <TimelineView
            timeline={timeline}
            positionMap={positionMap}
            selectedDate={selectedDate}
          />
        ) : (
          <TableView
            schedules={schedules}
            positionMap={positionMap}
            selectedDate={selectedDate}
          />
        )}
      </div>
    </div>
  );
};

const TimelineView = ({ timeline, positionMap, selectedDate }) => {
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

  // Sort rooms and slots by start time ascending
  const sortedRooms = Object.entries(timeline).sort(([a], [b]) =>
    String(a).localeCompare(String(b))
  );

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Timeline by Room</h3>
      {sortedRooms.map(([roomId, slots]) => {
        const filtered = selectedDate
          ? slots.filter(
              (s) =>
                (s.interview_date || s.start?.slice(0, 10)) === selectedDate
            )
          : slots;
        const sortedSlots = [...filtered].sort(
          (s1, s2) => new Date(s1.start) - new Date(s2.start)
        );
        return (
          <div key={roomId} className="border rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3">{roomId}</h4>
            <div className="space-y-2">
              {/* Group by date inside each room */}
              {Object.entries(
                sortedSlots.reduce((acc, slot) => {
                  const d = slot.interview_date || slot.start.slice(0, 10);
                  acc[d] = acc[d] || [];
                  acc[d].push(slot);
                  return acc;
                }, {})
              ).map(([dateKey, daySlots]) => (
                <div key={dateKey} className="space-y-2">
                  <div className="text-sm text-gray-700 font-semibold mt-2">
                    {new Date(dateKey).toLocaleDateString("vi-VN", {
                      weekday: "long",
                      day: "2-digit",
                      month: "2-digit",
                    })}
                  </div>
                  {daySlots.map((slot) => (
                    <div
                      key={slot.id}
                      className="timeline-slot p-3 rounded-lg border-l-4 bg-gray-50 hover:bg-gray-100 cursor-pointer"
                      style={{
                        borderLeftColor:
                          positionColors[slot.position] || "#9ca3af",
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
                            <span className="font-medium">
                              {positionMap?.[slot.position] || slot.position}
                            </span>
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
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const TableView = ({ schedules, positionMap, selectedDate }) => {
  if (!schedules || schedules.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No schedules available. Run an algorithm to generate schedules.
      </div>
    );
  }

  const rows = selectedDate
    ? schedules.filter(
        (s) => (s.interview_date || s.start_time?.slice(0, 10)) === selectedDate
      )
    : schedules;

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
          {rows.map((schedule) => (
            <tr key={schedule._id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="font-medium text-gray-900">
                    {schedule.applicant_detail?.full_name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {positionMap?.[schedule.applicant_detail?.position] ||
                      schedule.applicant_detail?.position}
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
                  <span className="text-gray-600 mr-2">
                    {new Date(
                      schedule.interview_date ||
                        schedule.start_time.slice(0, 10)
                    ).toLocaleDateString("vi-VN", {
                      weekday: "short",
                      day: "2-digit",
                      month: "2-digit",
                    })}
                  </span>
                  {format(parseISO(schedule.start_time), "HH:mm")} -
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
