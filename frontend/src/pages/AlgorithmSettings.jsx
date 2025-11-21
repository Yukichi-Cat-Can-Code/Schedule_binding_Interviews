import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { algorithmsAPI, sessionsAPI, configsAPI } from "../services/api";
import toast from "react-hot-toast";
import { FiPlay, FiSettings } from "react-icons/fi";
import { useCurrentCompany } from "../hooks/useCurrentCompany";

const AlgorithmSettings = () => {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState("GA");
  const [config, setConfig] = useState({
    GA: {
      POPULATION_SIZE: 100,
      GENERATIONS: 200,
      CROSSOVER_RATE: 0.8,
      MUTATION_RATE: 0.15,
      TOURNAMENT_SIZE: 3,
      ELITISM_RATE: 0.1,
    },
    GA2: {
      POPULATION_SIZE: 100,
      GENERATIONS: 200,
      CROSSOVER_RATE: 0.9,
      MUTATION_RATE: 0.2,
      ELITISM_RATE: 0.05,
    },
    GA3: {
      POPULATION_SIZE: 120,
      GENERATIONS: 250,
      CROSSOVER_RATE: 0.85,
      MUTATION_RATE: 0.12,
    },
    GA4: {
      POPULATION_SIZE: 120,
      GENERATIONS: 250,
      CROSSOVER_RATE: 0.9,
      MUTATION_RATE: 0.18,
      LOCAL_SEARCH_RATE: 0.3,
    },
    WEIGHTS: {
      CONFLICT: 0.4,
      IDLE: 0.2,
      FAIRNESS: 0.2,
      MATCHING: 0.1,
      ROOM: 0.1,
    },
  });

  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [configName, setConfigName] = useState("");
  const [savedConfigId, setSavedConfigId] = useState(null);

  const { companyId } = useCurrentCompany();

  const runAlgorithm = useMutation({
    mutationFn: (data) =>
      // pass algorithm name plus payload with config, session_id and company_id
      algorithmsAPI.run(data.algorithm, {
        config: data.config,
        session_id: data.session_id,
        company_id: data.company_id,
      }),
    onSuccess: (response) => {
      setResult(response.data);
      toast.success("Algorithm completed successfully!");
      setIsRunning(false);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to run algorithm");
      setIsRunning(false);
    },
  });

  const handleRun = () => {
    setIsRunning(true);
    setResult(null);
    // Flattened config: send algorithm params directly plus WEIGHTS
    const sendConfig = {
      ...config[selectedAlgorithm],
      WEIGHTS: config.WEIGHTS,
    };
    const session_id =
      selectedSessionId ||
      localStorage.getItem("selected_session") ||
      localStorage.getItem("active_session_id");
    const company_id = localStorage.getItem("auth_company_id") || companyId;
    if (!session_id) {
      setIsRunning(false);
      toast.error("Please select a Session first");
      return;
    }
    // Pass payload matching `algorithmsAPI.run(algorithm, { config, company_id, session_id })`
    runAlgorithm.mutate({
      algorithm: selectedAlgorithm,
      config: sendConfig,
      session_id,
      company_id,
    });
  };

  // Manual runtime controls are provided in the UI; remove randomize helper.

  const handleConfigChange = (section, key, value) => {
    setConfig((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: parseFloat(value) || 0,
      },
    }));
  };

  // Sessions list for the company
  const { data: sessions } = useQuery({
    queryKey: ["sessions", companyId || "all"],
    enabled: !!companyId,
    queryFn: () => sessionsAPI.getAll().then((res) => res.data),
  });

  // Saved configs
  const { data: savedConfigs } = useQuery({
    queryKey: ["configs", companyId || "all"],
    enabled: !!companyId,
    queryFn: () => configsAPI.getAll().then((res) => res.data),
  });

  const saveConfig = async () => {
    if (!configName) return toast.error("Please enter a name for the config");
    const sendConfig = {
      name: configName,
      algorithm: selectedAlgorithm,
      config: {
        ...config,
      },
      is_active: false,
    };
    try {
      const res = await configsAPI.create(sendConfig);
      toast.success("Configuration saved");
      setConfigName("");
      setSavedConfigId(res.data._id || res.data.id || null);
    } catch (err) {
      toast.error(err.message || "Failed to save config");
    }
  };

  const loadSavedConfig = (cfg) => {
    if (!cfg || !cfg.config) return;
    try {
      // Expect stored config to contain same sections as our local `config` state
      setConfig((prev) => ({ ...prev, ...cfg.config }));
      setSavedConfigId(cfg._id || cfg.id || null);
      setSelectedAlgorithm(cfg.algorithm || selectedAlgorithm);
      toast.success("Configuration loaded");
    } catch (e) {
      toast.error("Failed to load configuration");
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Algorithm Settings</h2>
        <p className="text-gray-600 mt-1">
          Configure and run scheduling algorithms
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Algorithm Selection */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Select Algorithm</h3>
            <div className="space-y-3">
              {[
                { id: "GA", name: "GA (Base)", desc: "Heuristic + adaptive" },
                {
                  id: "GA2",
                  name: "GA2 (Uniform)",
                  desc: "Uniform crossover variant",
                },
                {
                  id: "GA3",
                  name: "GA3 (Order)",
                  desc: "Order crossover + rank selection",
                },
                {
                  id: "GA4",
                  name: "GA4 (Hybrid)",
                  desc: "Two-point + local search",
                },
              ].map((algo) => (
                <button
                  key={algo.id}
                  onClick={() => setSelectedAlgorithm(algo.id)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    selectedAlgorithm === algo.id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-blue-300"
                  }`}
                >
                  <p className="font-medium text-gray-900">{algo.name}</p>
                  <p className="text-sm text-gray-600 mt-1">{algo.desc}</p>
                </button>
              ))}
            </div>

            <button
              onClick={handleRun}
              disabled={isRunning}
              className="w-full mt-6 btn btn-primary"
            >
              {isRunning ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                  <span>Running...</span>
                </>
              ) : (
                <>
                  <FiPlay className="w-5 h-5" />
                  <span>Run Algorithm</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Configuration */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <FiSettings className="w-5 h-5 mr-2" />
              Configuration
            </h3>

            {/* Session selector + saved configs */}
            <div className="flex items-center justify-between mb-4 space-x-3">
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-700">Session:</label>
                <select
                  value={selectedSessionId}
                  onChange={(e) => setSelectedSessionId(e.target.value)}
                  className="px-3 py-2 border rounded text-sm"
                >
                  <option value="">-- select session --</option>
                  {(sessions || []).map((s) => (
                    <option key={s._id} value={s._id}>
                      {s.name || s.code}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-700">Saved Config:</label>
                <select
                  value={savedConfigId || ""}
                  onChange={(e) => {
                    const id = e.target.value || null;
                    setSavedConfigId(id);
                    const cfg = (savedConfigs || []).find(
                      (c) => (c._id || c.id) === id
                    );
                    if (cfg) loadSavedConfig(cfg);
                  }}
                  className="px-3 py-2 border rounded text-sm"
                >
                  <option value="">-- none --</option>
                  {(savedConfigs || []).map((c) => (
                    <option key={c._id || c.id} value={c._id || c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  placeholder="Config name"
                  value={configName}
                  onChange={(e) => setConfigName(e.target.value)}
                  className="px-3 py-2 border rounded text-sm"
                />
                <button onClick={saveConfig} className="btn btn-secondary">
                  Save
                </button>
              </div>
            </div>

            {/* GA Base Parameters */}
            {selectedAlgorithm === "GA" && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">
                  Genetic Algorithm
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Population Size
                    </label>
                    <input
                      type="number"
                      value={config.GA.POPULATION_SIZE}
                      onChange={(e) =>
                        handleConfigChange(
                          "GA",
                          "POPULATION_SIZE",
                          e.target.value
                        )
                      }
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Generations
                    </label>
                    <input
                      type="number"
                      value={config.GA.GENERATIONS}
                      onChange={(e) =>
                        handleConfigChange("GA", "GENERATIONS", e.target.value)
                      }
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Crossover Rate
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      value={config.GA.CROSSOVER_RATE}
                      onChange={(e) =>
                        handleConfigChange(
                          "GA",
                          "CROSSOVER_RATE",
                          e.target.value
                        )
                      }
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Mutation Rate
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      value={config.GA.MUTATION_RATE}
                      onChange={(e) =>
                        handleConfigChange(
                          "GA",
                          "MUTATION_RATE",
                          e.target.value
                        )
                      }
                      className="input"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* GA2 Parameters */}
            {selectedAlgorithm === "GA2" && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">GA2 Variant</h4>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    ["POPULATION_SIZE", "Population Size"],
                    ["GENERATIONS", "Generations"],
                    ["CROSSOVER_RATE", "Crossover Rate"],
                    ["MUTATION_RATE", "Mutation Rate"],
                    ["ELITISM_RATE", "Elitism Rate"],
                  ].map(([key, label]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {label}
                      </label>
                      <input
                        type="number"
                        step={key.includes("RATE") ? "0.01" : "1"}
                        min="0"
                        value={config.GA2[key]}
                        onChange={(e) =>
                          handleConfigChange("GA2", key, e.target.value)
                        }
                        className="input"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* GA3 Parameters */}
            {selectedAlgorithm === "GA3" && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">GA3 Variant</h4>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    ["POPULATION_SIZE", "Population Size"],
                    ["GENERATIONS", "Generations"],
                    ["CROSSOVER_RATE", "Crossover Rate"],
                    ["MUTATION_RATE", "Mutation Rate"],
                  ].map(([key, label]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {label}
                      </label>
                      <input
                        type="number"
                        step={key.includes("RATE") ? "0.01" : "1"}
                        min="0"
                        value={config.GA3[key]}
                        onChange={(e) =>
                          handleConfigChange("GA3", key, e.target.value)
                        }
                        className="input"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* GA4 Parameters */}
            {selectedAlgorithm === "GA4" && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">GA4 Hybrid</h4>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    ["POPULATION_SIZE", "Population Size"],
                    ["GENERATIONS", "Generations"],
                    ["CROSSOVER_RATE", "Crossover Rate"],
                    ["MUTATION_RATE", "Mutation Rate"],
                    ["LOCAL_SEARCH_RATE", "Local Search Rate"],
                  ].map(([key, label]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {label}
                      </label>
                      <input
                        type="number"
                        step={key.includes("RATE") ? "0.01" : "1"}
                        min="0"
                        value={config.GA4[key]}
                        onChange={(e) =>
                          handleConfigChange("GA4", key, e.target.value)
                        }
                        className="input"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Fitness Weights */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">
                Fitness Function Weights
              </h4>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(config.WEIGHTS).map(([key, value]) => (
                  <div key={key}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {key.charAt(0) + key.slice(1).toLowerCase()}
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={value}
                      onChange={(e) =>
                        handleConfigChange("WEIGHTS", key, e.target.value)
                      }
                      className="input"
                    />
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-500 mt-2">
                Total:{" "}
                {Object.values(config.WEIGHTS)
                  .reduce((a, b) => a + b, 0)
                  .toFixed(1)}
              </p>
              {/* Runtime Controls: manual inputs for workers, repair timeout, and time limit */}
              {selectedAlgorithm && (
                <div className="mt-6 p-4 border rounded bg-gray-50">
                  <h4 className="font-medium text-gray-800 mb-2">
                    Runtime Controls
                  </h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">
                        Num Workers
                      </label>
                      <input
                        type="number"
                        min={1}
                        value={
                          (config[selectedAlgorithm] &&
                            config[selectedAlgorithm].NUM_WORKERS) ||
                          1
                        }
                        onChange={(e) =>
                          handleConfigChange(
                            selectedAlgorithm,
                            "NUM_WORKERS",
                            e.target.value
                          )
                        }
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">
                        Max Repair (ms)
                      </label>
                      <input
                        type="number"
                        min={0}
                        value={
                          (config[selectedAlgorithm] &&
                            config[selectedAlgorithm].MAX_REPAIR_MS) ||
                          500
                        }
                        onChange={(e) =>
                          handleConfigChange(
                            selectedAlgorithm,
                            "MAX_REPAIR_MS",
                            e.target.value
                          )
                        }
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">
                        Time Limit (s)
                      </label>
                      <input
                        type="number"
                        min={0}
                        value={
                          (config[selectedAlgorithm] &&
                            config[selectedAlgorithm].TIME_LIMIT_SECONDS) ||
                          ""
                        }
                        onChange={(e) =>
                          handleConfigChange(
                            selectedAlgorithm,
                            "TIME_LIMIT_SECONDS",
                            e.target.value
                          )
                        }
                        className="input"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Results</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600">Fitness Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {result.fitness_score?.toFixed(3) || "N/A"}
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600">Execution Time</p>
              <p className="text-2xl font-bold text-gray-900">
                {result.execution_time?.toFixed(2) ||
                  result.generations ||
                  "N/A"}
                s
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-gray-600">Algorithm</p>
              <p className="text-2xl font-bold text-gray-900">
                {result.algorithm}
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-gray-600">Schedules</p>
              <p className="text-2xl font-bold text-gray-900">
                {result.schedule_data?.length || 0}
              </p>
            </div>
          </div>

          {result.conflict_score !== undefined && (
            <div className="mt-4 grid grid-cols-5 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Conflict</p>
                <p className="text-lg font-bold">
                  {(result.conflict_score * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Idle Time</p>
                <p className="text-lg font-bold">
                  {(result.idle_time_score * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Fairness</p>
                <p className="text-lg font-bold">
                  {(result.fairness_score * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Matching</p>
                <p className="text-lg font-bold">
                  {(result.matching_score * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Room Usage</p>
                <p className="text-lg font-bold">
                  {(result.room_usage_score * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AlgorithmSettings;
