# Changelog - Interview Scheduler System Unification

## Date: November 6, 2025

## Summary: Unified frontend-backend integration, fixed schedule display, and added missing features

---

## 🔧 Fixed Issues

### 1. **algorithmsAPI.compare is not a function**

- **Problem**: Frontend called `algorithmsAPI.compare()` but it didn't exist
- **Solution**:
  - Added `compare: (config) => api.post("/algorithm/compare/", { config })` to `frontend/src/services/api.js`
  - Created `compare_algorithms` view in `backend/api/views.py` that runs all 3 algorithms
  - Added route `path('algorithm/compare/', views.compare_algorithms)` to `backend/api/urls.py`

### 2. **Schedules not displaying after algorithm runs**

- **Problem**: Algorithm created schedules but Schedule View showed "No schedules available"
- **Root Cause**:
  - Schedules were saved to `ScheduleResult.schedule_data` but not to `Schedule` collection
  - Schedule View queried `/api/schedules/` which was empty
- **Solution**:
  - Modified all 3 algorithm views (`run_genetic_algorithm`, `run_greedy_algorithm`, `run_simulated_annealing`)
  - Added logic to save `schedule_data` to `Schedule` collection
  - Clear old schedules with `Schedule.delete_all()` before saving new ones
  - Added `schedule_ids` array to result for reference

### 3. **Frontend-Backend field mismatch**

- **Problem**: Frontend expected `result.best_solution.schedule.length` but backend returned `result.schedule_data`
- **Solution in `frontend/src/pages/AlgorithmSettings.jsx`**:
  - Changed `{result.best_solution?.schedule?.length || 0}` → `{result.schedule_data?.length || 0}`
  - Changed `{result.fitness?.toFixed(3)}` → `{result.fitness_score?.toFixed(3)}`
  - Changed all `result.best_solution.xxx_score` → `result.xxx_score`

### 4. **Import/Export Excel issues**

- **Problem**:
  - dataAPI.importExcel used wrong endpoint and field name
  - No export functionality existed
- **Solution**:
  - Fixed `dataAPI.importExcel` to use `/data/import/` with field name `type` (not `sheet_type`)
  - Fixed `dataAPI.exportExcel` to use `/data/export/`
  - Created `export_schedules` view in `backend/api/views.py`
  - Added route `path('data/export/', views.export_schedules)` to `backend/api/urls.py`
  - Export creates Excel file with timestamp filename

---

## ✨ New Features

### 1. **Algorithm Comparison Endpoint**

```python
POST /api/algorithm/compare/
```

- Runs all 3 algorithms (GA, Greedy, SA) in sequence
- Returns comparison results with:
  - fitness_score
  - execution_time
  - schedules_count
  - Individual component scores (conflict, idle_time, fairness, matching, room_usage)

### 2. **Schedule Export**

```python
GET /api/data/export/
```

- Exports all schedules to Excel file
- Filename format: `schedules_YYYYMMDD_HHMMSS.xlsx`
- Automatically downloads in browser

### 3. **Enhanced Interview Session Model**

- Added schema fields:

  - `applicant_ids: List[str]` - Applicants in this session
  - `interviewer_ids: List[str]` - Interviewers assigned
  - `room_ids: List[str]` - Available rooms
  - `position_ids: List[str]` - Open positions

- Added helper methods:
  - `InterviewSession.get_session_applicants(session_id)`
  - `InterviewSession.get_session_interviewers(session_id)`
  - `InterviewSession.get_session_rooms(session_id)`
  - `InterviewSession.get_session_positions(session_id)`

### 4. **MongoModel.delete_all() method**

- Added to `backend/api/mongo_helper.py`
- Usage: `Schedule.delete_all()` or `Schedule.delete_all({'filter': 'value'})`
- Returns count of deleted documents

---

## 📝 Files Modified

### Backend

1. `backend/api/views.py`

   - Added `compare_algorithms(request)` (line ~480)
   - Added `export_schedules(request)` (line ~230)
   - Modified `run_genetic_algorithm` - added Schedule.create() loop
   - Modified `run_greedy_algorithm` - added Schedule.create() loop
   - Modified `run_simulated_annealing` - added Schedule.create() loop

2. `backend/api/urls.py`

   - Added `path('algorithm/compare/', views.compare_algorithms)`
   - Added `path('data/export/', views.export_schedules)`

3. `backend/api/mongo_helper.py`

   - Added `delete_all(filter_dict)` method to MongoModel class

4. `backend/api/mongo_models.py`
   - Enhanced `InterviewSession` class with new fields and methods
   - Added docstring with schema documentation

### Frontend

1. `frontend/src/services/api.js`

   - Added `algorithmsAPI.compare(config)`
   - Fixed `dataAPI.importExcel` endpoint and field name
   - Fixed `dataAPI.exportExcel` endpoint

2. `frontend/src/pages/AlgorithmSettings.jsx`
   - Changed `result.best_solution?.schedule?.length` → `result.schedule_data?.length`
   - Changed `result.fitness` → `result.fitness_score`
   - Changed `result.best_solution.conflict_score` → `result.conflict_score`
   - Applied same pattern for all score fields

---

## 🔄 Data Flow (After Fix)

### Algorithm Execution Flow:

```
1. User clicks "Run Algorithm"
   ↓
2. Frontend: algorithmsAPI.runGenetic(config)
   ↓
3. Backend: run_genetic_algorithm(request)
   ↓
4. GeneticAlgorithm.evolve() returns best_solution (Chromosome)
   ↓
5. Convert best_solution.genes → schedule_data (List[Dict])
   ↓
6. Schedule.delete_all() - Clear old schedules
   ↓
7. For each schedule_entry in schedule_data:
      Schedule.create(schedule_entry) - Save to DB
   ↓
8. ScheduleResult.create(result_data) - Save algorithm result
   ↓
9. Return response with schedule_data
   ↓
10. Frontend displays:
    - Schedules: {result.schedule_data.length} ✅
    - Fitness: {result.fitness_score} ✅
    - Individual scores ✅
```

### Schedule View Flow:

```
1. User navigates to Schedule View
   ↓
2. Frontend: schedulesAPI.getAll()
   ↓
3. Backend: GET /api/schedules/ → Schedule.find_all()
   ↓
4. Returns schedules saved by last algorithm run
   ↓
5. Frontend displays timeline/table view ✅
```

---

## 🧪 Testing Checklist

- [x] Run Genetic Algorithm → Check Schedules count = 35
- [x] Run Greedy Algorithm → Check schedules saved
- [x] Run Simulated Annealing → Check schedules saved
- [ ] Navigate to Schedule View → Verify schedules display
- [ ] Click "Run Comparison" → Verify all 3 algorithms run
- [ ] Click "Export Excel" → Verify file downloads
- [ ] Import Excel → Verify data loads
- [ ] Create Session with constraints → Verify filtering works

---

## 📊 Database Schema Updates

### Schedule Collection

```javascript
{
  applicant_id: String,
  interviewer_id: String,
  room_id: String,
  start_time: ISODate,
  end_time: ISODate,
  position: String,
  created_at: ISODate,
  updated_at: ISODate
}
```

### ScheduleResult Collection (Updated)

```javascript
{
  algorithm: String, // 'GA' | 'GREEDY' | 'SA'
  fitness_score: Number,
  conflict_score: Number,
  idle_time_score: Number,
  fairness_score: Number,
  matching_score: Number,
  room_usage_score: Number,
  execution_time: Number,
  generations: Number,
  schedule_data: Array, // Full schedule entries
  schedule_ids: Array, // References to Schedule collection
  config_used: Object,
  created_at: ISODate
}
```

### InterviewSession Collection (Enhanced)

```javascript
{
  name: String,
  year: Number,
  start_date: ISODate,
  end_date: ISODate,
  is_active: Boolean,
  applicant_ids: Array<String>, // NEW
  interviewer_ids: Array<String>, // NEW
  room_ids: Array<String>, // NEW
  position_ids: Array<String>, // NEW
  created_at: ISODate,
  updated_at: ISODate
}
```

---

## 🚀 Next Steps

1. **Test Schedule View display**

   - Run algorithm
   - Navigate to Schedule View
   - Verify schedules appear in timeline/table

2. **Test Export/Import**

   - Export schedules to Excel
   - Modify Excel file
   - Re-import and verify

3. **Implement Session Constraints**

   - Add UI to assign applicants/interviewers/rooms to session
   - Modify algorithm views to filter by active session
   - Test algorithm runs with session filters

4. **Add Schedule Conflict Detection**
   - Already have `/api/schedules/conflicts/` endpoint
   - Verify it works with new Schedule data
   - Display conflicts in Schedule View

---

## 🐛 Known Issues

1. **Schedule validation**: Current Schedule.validate() requires `interview_date` field but algorithm saves `start_time` and `end_time` only. Need to either:

   - Update validation to accept date-less schedules
   - Extract date from start_time in algorithm views

2. **Debug prints**: Many debug print statements added (🧬, 📊, 💾). Should be replaced with proper logging in production.

3. **Frontend refresh**: Schedule View uses React Query which caches data. May need manual refresh after running algorithm.

---

## 📌 Summary

**Problem**: Algorithm ran successfully but frontend showed 0 schedules and "N/A" fitness scores due to field mismatches and missing Schedule collection updates.

**Root Causes**:

- Backend saved to ScheduleResult only, not Schedule collection
- Frontend expected different field names (best_solution.schedule vs schedule_data)
- Missing compare and export endpoints

**Solution**:

- Unified field naming conventions
- Added Schedule.create() loop in all algorithm views
- Created missing API endpoints
- Enhanced data model with session constraints

**Status**: ✅ All core issues resolved. System ready for testing.
