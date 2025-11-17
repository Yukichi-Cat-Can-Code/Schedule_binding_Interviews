import { useEffect, useMemo, useState, Fragment } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import { FiAlertCircle } from "react-icons/fi";
import {
  schedulesAPI,
  sessionsAPI,
  positionsAPI,
  applicantsAPI,
  interviewersAPI,
  roomsAPI,
  dataAPI,
  algorithmsAPI,
} from "../services/api";
import { useCurrentCompany } from "../hooks/useCurrentCompany";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
} from "recharts";

const ScheduleView = () => {
  const [viewMode, setViewMode] = useState("timeline"); // timeline | table | analytics
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [selectedDate, setSelectedDate] = useState(""); // ISO date filter

  const { companyId } = useCurrentCompany();

  // Sessions
  const { data: sessions } = useQuery({
    queryKey: ["sessions", companyId || "all"],
    enabled: !!companyId,
    queryFn: () =>
      sessionsAPI.getAll({ company_id: companyId }).then((res) => res.data),
  });

  const { data: activeSession } = useQuery({
    queryKey: ["sessions", "active", companyId],
    enabled: !!companyId,
    queryFn: () =>
      sessionsAPI.getActive({ company_id: companyId }).then((res) => res.data),
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

  // Load session-scoped entities to map ids -> readable labels for Table View
  const { data: applicants } = useQuery({
    queryKey: ["applicants", params?.session_id || "all"],
    queryFn: () => applicantsAPI.getAll(params).then((res) => res.data),
  });
  const { data: interviewers } = useQuery({
    queryKey: ["interviewers", params?.session_id || "all"],
    queryFn: () => interviewersAPI.getAll(params).then((res) => res.data),
  });
  const { data: rooms } = useQuery({
    queryKey: ["rooms", params?.session_id || "all"],
    queryFn: () => roomsAPI.getAll(params).then((res) => res.data),
  });

  const maps = useMemo(() => {
    const a = {};
    const i = {};
    const r = {};
    (applicants || []).forEach((x) => (a[x._id] = x));
    (interviewers || []).forEach((x) => (i[x._id] = x));
    (rooms || []).forEach((x) => (r[x._id] = x));
    return { a, i, r };
  }, [applicants, interviewers, rooms]);

  const { data: timeline } = useQuery({
    queryKey: ["timeline", params?.session_id || "all"],
    queryFn: () => schedulesAPI.getTimeline(params).then((res) => res.data),
  });

  const { data: conflicts } = useQuery({
    queryKey: ["conflicts"],
    queryFn: () => schedulesAPI.getConflicts().then((res) => res.data),
  });

  // Top-5 schedule results for analytics view
  const { data: topResults } = useQuery({
    queryKey: ["top-schedule-results", selectedSessionId],
    enabled: !!selectedSessionId,
    queryFn: () =>
      algorithmsAPI
        .getResults({ session_id: selectedSessionId, top: 5 })
        .then((res) => res.data),
  });

  // Currently selected/active result (if any)
  const { data: activeResult } = useQuery({
    queryKey: ["active-schedule-result", selectedSessionId],
    enabled: !!selectedSessionId,
    queryFn: () =>
      algorithmsAPI
        .getResults({ session_id: selectedSessionId, selected: true, top: 1 })
        .then((res) => (Array.isArray(res.data) ? res.data[0] : null)),
  });

  const chooseResultMutation = useMutation({
    mutationFn: ({ resultId }) =>
      algorithmsAPI.chooseResult({
        result_id: resultId,
        session_id: selectedSessionId,
      }),
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
          <p className="text-gray-600 mt-1 flex items-center space-x-2">
            <span>View and manage interview schedules</span>
            {activeResult && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
                Active schedule: {activeResult.algorithm || "Run"}
              </span>
            )}
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
          <button
            onClick={() => setViewMode("analytics")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              viewMode === "analytics"
                ? "bg-blue-500 text-white"
                : "bg-white text-gray-700 border"
            }`}
          >
            Analytics View
          </button>
          {/* Export button */}
          <button
            onClick={async () => {
              try {
                const res = await dataAPI.exportExcel(selectedSessionId);
                const url = window.URL.createObjectURL(new Blob([res.data]));
                const link = document.createElement("a");
                link.href = url;
                // Prefer filename from server's Content-Disposition
                const cd = res.headers?.["content-disposition"] || "";
                let serverName = null;
                // RFC 5987 filename*
                const star = cd.match(/filename\*=UTF-8''([^;]+)/i);
                if (star && star[1]) {
                  try {
                    serverName = decodeURIComponent(star[1]);
                  } catch {}
                }
                if (!serverName) {
                  const m = cd.match(/filename="?([^";]+)"?/i);
                  serverName = m?.[1] || null;
                }
                // Fallback matches new double-underscore naming: <SessionName>__<start_end>__<Company>.xlsx when possible
                let fallback = `schedules_${selectedSessionId || "all"}.xlsx`;
                try {
                  if (selectedSessionId) {
                    // We may have session object in sessions list
                    const sess = (sessions || []).find(
                      (s) => s._id === selectedSessionId
                    );
                    if (sess) {
                      const period = `${sess.start_date || ""}_${
                        sess.end_date || ""
                      }`.replace(/_+/g, "_");
                      const company = (sess.company_name || "Company").replace(
                        /\s+/g,
                        "_"
                      );
                      const base = (
                        sess.name ||
                        sess.code ||
                        "Session"
                      ).replace(/\s+/g, "_");
                      fallback = `${base}__${period}__${company}.xlsx`;
                    }
                  }
                } catch {}
                const safeName = (serverName || fallback).replace(
                  /[\\/:*?"<>|]/g,
                  "-"
                );
                link.download = safeName;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
              } catch (e) {
                console.error(e);
                alert(`Export failed: ${e.message}`);
              }
            }}
            className="px-4 py-2 rounded-lg font-medium border text-gray-700 hover:bg-gray-50"
            title="Export schedules to Excel"
          >
            Export
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

      {/* Analytics View: top-5 schedules as radar chart + selector */}
      {viewMode === "analytics" && selectedSessionId && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-2">
              Top 5 Schedules for This Session
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Compare candidate schedules by fitness, conflicts, fairness, idle
              time and room usage. The best one (rank 1) is highlighted.
            </p>
            {(!topResults || topResults.length === 0) && (
              <p className="text-sm text-gray-500">
                No schedule candidates found. Run algorithms and generate
                candidates first.
              </p>
            )}
            {topResults && topResults.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                <div className="lg:col-span-2 h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart
                      data={topResults.map((r) => ({
                        name: r.algorithm || "Run",
                        fitness:
                          r.fitness_score ?? r.final_fitness ?? r.fitness ?? 0,
                        conflicts: r.conflict_score ?? 0,
                        fairness: r.fairness_score ?? 0,
                        idle: r.idle_time_score ?? 0,
                        roomUsage: r.room_usage_score ?? 0,
                      }))}
                    >
                      <PolarGrid />
                      <PolarAngleAxis dataKey="name" />
                      <PolarRadiusAxis angle={30} />
                      <RechartsTooltip />
                      <Radar
                        name="Fitness"
                        dataKey="fitness"
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.35}
                      />
                      <Radar
                        name="Conflicts (lower better)"
                        dataKey="conflicts"
                        stroke="#ef4444"
                        fill="#ef4444"
                        fillOpacity={0.15}
                      />
                      <Radar
                        name="Fairness"
                        dataKey="fairness"
                        stroke="#10b981"
                        fill="#10b981"
                        fillOpacity={0.25}
                      />
                      <Radar
                        name="Idle Time"
                        dataKey="idle"
                        stroke="#f97316"
                        fill="#f97316"
                        fillOpacity={0.15}
                      />
                      <Radar
                        name="Room Usage"
                        dataKey="roomUsage"
                        stroke="#6366f1"
                        fill="#6366f1"
                        fillOpacity={0.2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-gray-800">
                    Choose Active Schedule
                  </h4>
                  <div className="space-y-2">
                    {topResults.map((r, idx) => (
                      <label
                        key={r._id || r.id}
                        className="flex items-center justify-between rounded border px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer"
                      >
                        <span className="flex items-center space-x-2">
                          <input
                            type="radio"
                            name="selectedScheduleResult"
                            defaultChecked={idx === 0 || r.is_selected}
                            onChange={() =>
                              chooseResultMutation.mutate({
                                resultId: r._id || r.id,
                              })
                            }
                          />
                          <span>
                            <span className="font-medium mr-1">#{idx + 1}</span>
                            <span className="text-gray-700">
                              {r.algorithm} – Fitness{" "}
                              {(
                                r.fitness_score ??
                                r.final_fitness ??
                                r.fitness ??
                                0
                              ).toFixed(3)}
                            </span>
                          </span>
                        </span>
                        {idx === 0 && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                            Best
                          </span>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}
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
            maps={maps}
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

const TableView = ({ schedules, positionMap, selectedDate, maps }) => {
  if (!schedules || schedules.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No schedules available. Run an algorithm to generate schedules.
      </div>
    );
  }

  const [query, setQuery] = useState("");
  const [room, setRoom] = useState("");
  const [status, setStatus] = useState("");
  const [position, setPosition] = useState("");
  const [dense, setDense] = useState(true);

  const rowsBase = selectedDate
    ? schedules.filter(
        (s) => (s.interview_date || s.start_time?.slice(0, 10)) === selectedDate
      )
    : schedules;

  // Build filter options
  const roomOptions = useMemo(() => {
    const set = new Set(
      rowsBase.map((s) => maps?.r?.[s.room_id]?.room_code || "").filter(Boolean)
    );
    return Array.from(set).sort();
  }, [rowsBase, maps]);

  const positionOptions = useMemo(() => {
    const set = new Set(
      rowsBase.map((s) => maps?.a?.[s.applicant_id]?.position).filter(Boolean)
    );
    return Array.from(set).sort();
  }, [rowsBase, maps]);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rowsBase.filter((s) => {
      const a = maps?.a?.[s.applicant_id];
      const i = maps?.i?.[s.interviewer_id];
      const r = maps?.r?.[s.room_id];
      const matchesQuery = q
        ? [a?.full_name, i?.full_name, r?.room_code]
            .filter(Boolean)
            .some((x) => x.toLowerCase().includes(q))
        : true;
      const matchesRoom = room ? r?.room_code === room : true;
      const matchesStatus = status ? s.status === status : true;
      const matchesPos = position ? a?.position === position : true;
      return matchesQuery && matchesRoom && matchesStatus && matchesPos;
    });
  }, [rowsBase, query, room, status, position, maps]);

  return (
    <div className="overflow-x-auto">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 mb-3">
        <input
          className="px-3 py-2 border rounded-md text-sm w-48"
          placeholder="Search name / room"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="px-3 py-2 border rounded-md text-sm"
          value={room}
          onChange={(e) => setRoom(e.target.value)}
        >
          <option value="">All rooms</option>
          {roomOptions.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <select
          className="px-3 py-2 border rounded-md text-sm"
          value={position}
          onChange={(e) => setPosition(e.target.value)}
        >
          <option value="">All positions</option>
          {positionOptions.map((p) => (
            <option key={p} value={p}>
              {positionMap?.[p] || p}
            </option>
          ))}
        </select>
        <select
          className="px-3 py-2 border rounded-md text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All status</option>
          <option value="scheduled">Scheduled</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <label className="inline-flex items-center gap-2 text-sm text-gray-700 ml-auto">
          <input
            type="checkbox"
            checked={dense}
            onChange={(e) => setDense(e.target.checked)}
          />
          Compact rows
        </label>
      </div>

      {/* Group by date */}
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">
              Time
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">
              Applicant
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">
              Interviewer
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">
              Room
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {Object.entries(
            rows.reduce((acc, s) => {
              const d = s.interview_date || s.start_time?.slice(0, 10);
              acc[d] = acc[d] || [];
              acc[d].push(s);
              return acc;
            }, {})
          )
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([d, list]) => (
              <Fragment key={d}>
                <tr key={`h-${d}`} className="bg-gray-50">
                  <td
                    colSpan={5}
                    className="px-4 py-2 text-sm font-medium text-gray-700"
                  >
                    {new Date(d).toLocaleDateString("vi-VN", {
                      weekday: "long",
                      day: "2-digit",
                      month: "2-digit",
                    })}
                  </td>
                </tr>
                {list
                  .slice()
                  .sort(
                    (s1, s2) =>
                      new Date(s1.start_time) - new Date(s2.start_time)
                  )
                  .map((schedule) => {
                    const a = maps?.a?.[schedule.applicant_id];
                    const i = maps?.i?.[schedule.interviewer_id];
                    const r = maps?.r?.[schedule.room_id];
                    const py = dense ? "py-2" : "py-3";
                    return (
                      <tr
                        key={schedule._id}
                        className={`hover:bg-gray-50 ${py}`}
                      >
                        <td className="px-4 whitespace-nowrap align-top">
                          <div className="text-sm font-medium text-gray-900">
                            {format(parseISO(schedule.start_time), "HH:mm")} -{" "}
                            {format(parseISO(schedule.end_time), "HH:mm")}
                          </div>
                          <div className="text-xs text-gray-500">
                            {positionMap?.[a?.position] || a?.position || ""}
                          </div>
                        </td>
                        <td className="px-4 whitespace-nowrap align-top">
                          <div className="text-sm font-medium text-gray-900">
                            {a?.full_name || "—"}
                          </div>
                        </td>
                        <td className="px-4 whitespace-nowrap align-top">
                          {i?.full_name || "—"}
                        </td>
                        <td className="px-4 whitespace-nowrap align-top">
                          <span className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-gray-700 text-xs font-medium">
                            {r?.room_code ||
                              r?.room_name ||
                              schedule.room_id ||
                              "—"}
                          </span>
                        </td>
                        <td className="px-4 whitespace-nowrap align-top">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${
                              schedule.status === "scheduled"
                                ? "bg-green-100 text-green-800"
                                : schedule.status === "completed"
                                ? "bg-blue-100 text-blue-800"
                                : schedule.status === "cancelled"
                                ? "bg-red-100 text-red-700"
                                : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {schedule.status || "scheduled"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
              </Fragment>
            ))}
        </tbody>
      </table>
    </div>
  );
};

export default ScheduleView;
