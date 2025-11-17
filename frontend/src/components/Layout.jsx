import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { authAPI } from "../services/api";
import { useCurrentCompany } from "../hooks/useCurrentCompany";
import {
  FiHome,
  FiDatabase,
  FiSettings,
  FiCalendar,
  FiBarChart2,
} from "react-icons/fi";

const Layout = () => {
  const [token, setToken] = useState(() => localStorage.getItem("auth_token"));
  const [username, setUsername] = useState(() =>
    localStorage.getItem("auth_username")
  );
  const [companyId, setCompanyId] = useState(() =>
    localStorage.getItem("auth_company_id")
  );
  const [role, setRole] = useState(() => localStorage.getItem("auth_role"));
  const [companyName, setCompanyName] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const [showAuth, setShowAuth] = useState(false);
  const [mode, setMode] = useState("login"); // 'login' | 'register'
  const [form, setForm] = useState({
    username: "",
    password: "",
    company_code: "",
  });

  const logout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_username");
    localStorage.removeItem("auth_company_id");
    localStorage.removeItem("auth_role");
    localStorage.removeItem("selectedCompany");
    localStorage.removeItem("selected_session");
    setToken(null);
    setUsername(null);
    setCompanyId(null);
    navigate("/");
  };

  const submitAuth = async (e) => {
    e.preventDefault();
    try {
      if (mode === "login") {
        const res = await authAPI.login({
          username: form.username,
          password: form.password,
        });
        const { token, username, company_id, role } = res.data;
        localStorage.setItem("auth_token", token);
        localStorage.setItem("auth_username", username);
        if (role) {
          localStorage.setItem("auth_role", role);
          setRole(role);
        }
        if (company_id) {
          localStorage.setItem("auth_company_id", company_id);
          localStorage.setItem("selectedCompany", company_id);
          setCompanyId(company_id);
        }
        setToken(token);
        setUsername(username);
      } else {
        const res = await authAPI.register({
          username: form.username,
          password: form.password,
          company_code: form.company_code,
        });
        const { token, username, company_id, role } = res.data;
        localStorage.setItem("auth_token", token);
        localStorage.setItem("auth_username", username);
        if (role) {
          localStorage.setItem("auth_role", role);
          setRole(role);
        }
        if (company_id) {
          localStorage.setItem("auth_company_id", company_id);
          localStorage.setItem("selectedCompany", company_id);
          setCompanyId(company_id);
        }
        setToken(token);
        setUsername(username);
      }
      setShowAuth(false);
      setForm({ username: "", password: "", company_code: "" });
    } catch (err) {
      alert(err.message || "Auth failed");
    }
  };

  // Resolve current company via shared hook so all pages are consistent.
  const { company: companyDoc, companyId: resolvedCompanyId } =
    useCurrentCompany();

  useEffect(() => {
    if (resolvedCompanyId && companyDoc) {
      setCompanyId(resolvedCompanyId);
      setCompanyName(
        companyDoc?.name || companyDoc?.code || String(resolvedCompanyId)
      );
    } else if (!resolvedCompanyId) {
      setCompanyName("");
    }
  }, [resolvedCompanyId, companyDoc]);

  const navItems = [
    { to: "/", icon: FiHome, label: "Dashboard" },
    { to: "/data", icon: FiDatabase, label: "Data Management" },
    { to: "/config", icon: FiSettings, label: "Algorithm Settings" },
    { to: "/schedule", icon: FiCalendar, label: "Schedule View" },
    { to: "/compare", icon: FiBarChart2, label: "Comparison" },
    { to: "/company", icon: FiSettings, label: "Company" },
    // Admin-only: Action Logs
    ...(role === "admin"
      ? [{ to: "/logs", icon: FiBarChart2, label: "Action Logs" }]
      : []),
  ];

  // Gate protected routes: if not authenticated and route is not root, show auth modal
  useEffect(() => {
    if (!token && location.pathname !== "/") {
      setShowAuth(true);
      navigate("/");
    }
  }, [token, location.pathname]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Interview Scheduler
              </h1>
              <p className="text-sm text-gray-600">
                Genetic Algorithm Optimization
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {token ? (
                <>
                  {companyId && (
                    <span className="px-2 py-1 text-xs rounded bg-indigo-100 text-indigo-700 font-medium">
                      {companyName || "Company"}
                    </span>
                  )}
                  <span className="text-sm text-gray-700">{username}</span>
                  <button className="text-sm text-red-600" onClick={logout}>
                    Logout
                  </button>
                </>
              ) : (
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowAuth(true)}
                >
                  Login / Register
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navItems.map((item) => {
              const disabled = !token && item.to !== "/";
              return (
                <NavLink
                  key={item.to}
                  to={disabled ? "/" : item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `flex items-center space-x-2 py-4 px-3 border-b-2 text-sm font-medium transition-colors ${
                      isActive && !disabled
                        ? "border-blue-500 text-blue-600"
                        : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                    } ${disabled ? "opacity-40 cursor-not-allowed" : ""}`
                  }
                  onClick={(e) => {
                    if (disabled) {
                      e.preventDefault();
                      setShowAuth(true);
                    }
                  }}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {token ? (
          <Outlet />
        ) : (
          <div className="max-w-md mx-auto mt-12 text-center">
            <h2 className="text-2xl font-semibold mb-4">
              Welcome to Interview Scheduler
            </h2>
            <p className="text-gray-600 mb-6">
              Please login or register to access scheduling features.
            </p>
            <button
              className="btn btn-primary"
              onClick={() => setShowAuth(true)}
            >
              Login / Register
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            © 2025 Interview Scheduler. AI Fundamental Project - CTU
          </p>
        </div>
      </footer>
      {showAuth && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                {mode === "login" ? "Login" : "Register"}
              </h3>
              <button
                onClick={() => setShowAuth(false)}
                className="text-gray-500"
              >
                ×
              </button>
            </div>
            <form onSubmit={submitAuth} className="space-y-4">
              <div>
                <label className="block text-sm mb-1">Username</label>
                <input
                  type="text"
                  required
                  value={form.username}
                  onChange={(e) =>
                    setForm({ ...form, username: e.target.value })
                  }
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              <div>
                <label className="block text-sm mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={form.password}
                  onChange={(e) =>
                    setForm({ ...form, password: e.target.value })
                  }
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              {mode === "register" && (
                <div>
                  <label className="block text-sm mb-1">Company Code</label>
                  <input
                    type="text"
                    required
                    value={form.company_code}
                    onChange={(e) =>
                      setForm({ ...form, company_code: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded"
                  />
                </div>
              )}
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  className="text-sm text-blue-600"
                  onClick={() =>
                    setMode(mode === "login" ? "register" : "login")
                  }
                >
                  {mode === "login"
                    ? "Need an account? Register"
                    : "Have an account? Login"}
                </button>
                <div className="space-x-2">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowAuth(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    {mode === "login" ? "Login" : "Register"}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
