import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import DataManagement from "./pages/DataManagement";
import AlgorithmSettings from "./pages/AlgorithmSettings";
import ScheduleView from "./pages/ScheduleView";
import Comparison from "./pages/Comparison";
import Company from "./pages/Company";
import ActionLogs from "./pages/ActionLogs";
import DevMode from "./pages/DevMode";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="data" element={<DataManagement />} />
        <Route path="config" element={<AlgorithmSettings />} />
        <Route path="schedule" element={<ScheduleView />} />
        <Route path="compare" element={<Comparison />} />
        <Route path="company" element={<Company />} />
        <Route path="logs" element={<ActionLogs />} />
        <Route path="dev" element={<DevMode />} />
      </Route>
    </Routes>
  );
}

export default App;
