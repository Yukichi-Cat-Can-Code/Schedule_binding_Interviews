import { Outlet, NavLink } from "react-router-dom";
import {
  FiHome,
  FiDatabase,
  FiSettings,
  FiCalendar,
  FiBarChart2,
} from "react-icons/fi";

const Layout = () => {
  const navItems = [
    { to: "/", icon: FiHome, label: "Dashboard" },
    { to: "/data", icon: FiDatabase, label: "Data Management" },
    { to: "/config", icon: FiSettings, label: "Algorithm Settings" },
    { to: "/schedule", icon: FiCalendar, label: "Schedule View" },
    { to: "/compare", icon: FiBarChart2, label: "Comparison" },
  ];

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
              <span className="text-sm text-gray-600">v1.0.0</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center space-x-2 py-4 px-3 border-b-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            © 2025 Interview Scheduler. AI Fundamental Project - CTU
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
