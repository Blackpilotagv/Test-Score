import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen, User as UserIcon, LogOut, ShieldCheck, LayoutDashboard, Menu, X, Calendar, FileText } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    setMobileMenuOpen(false);
    logout();
    navigate('/login');
  };

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" onClick={closeMobileMenu} className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-700 to-indigo-600 flex items-center justify-center text-white font-black text-lg shadow-xs">
                TS
              </div>
              <div>
                <span className="text-xl font-extrabold text-gray-900 tracking-tight block leading-tight">Test-Score</span>
                <span className="text-[10px] font-bold text-sky-600 block tracking-wide uppercase">by MZAB Arcane</span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <div className="hidden md:flex ml-10 space-x-8">
              <Link to="/" className="text-gray-600 hover:text-sky-600 font-medium text-sm transition-colors py-5 border-b-2 border-transparent hover:border-sky-600">
                Home
              </Link>
              <Link to="/exams" className="text-gray-600 hover:text-sky-600 font-medium text-sm transition-colors py-5 border-b-2 border-transparent hover:border-sky-600">
                Daily Mocks
              </Link>
              <Link to="/past-year-papers" className="text-indigo-600 hover:text-indigo-800 font-bold text-sm transition-colors py-5 border-b-2 border-transparent hover:border-indigo-600 flex items-center gap-1">
                📚 Past 5 Years Papers
              </Link>
              <Link to="/about" className="text-gray-600 hover:text-sky-600 font-medium text-sm transition-colors py-5 border-b-2 border-transparent hover:border-sky-600">
                About
              </Link>
              {user && (
                <Link to="/dashboard" className="text-gray-600 hover:text-sky-600 font-medium text-sm transition-colors py-5 border-b-2 border-transparent hover:border-sky-600 flex items-center gap-1">
                  <LayoutDashboard className="w-4 h-4" /> Dashboard
                </Link>
              )}
              {isAdmin && (
                <>
                  <Link to="/admin" className="text-amber-700 hover:text-amber-900 font-semibold text-sm transition-colors py-5 border-b-2 border-transparent hover:border-amber-600 flex items-center gap-1">
                    <ShieldCheck className="w-4 h-4" /> Admin Portal
                  </Link>
                  <Link to="/admin/past-year-papers" className="text-amber-700 hover:text-amber-900 font-semibold text-sm transition-colors py-5 border-b-2 border-transparent hover:border-amber-600 flex items-center gap-1">
                    📄 Past Papers
                  </Link>
                  <Link to="/admin/scheduler" className="text-amber-700 hover:text-amber-900 font-semibold text-sm transition-colors py-5 border-b-2 border-transparent hover:border-amber-600 flex items-center gap-1">
                    📅 Daily Scheduler
                  </Link>
                </>
              )}
            </div>
          </div>

          {/* Desktop Right Auth Actions */}
          <div className="hidden md:flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">
                  Hi, <strong className="text-sky-700">{user.name}</strong>
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors border border-red-200 cursor-pointer"
                >
                  <LogOut className="w-4 h-4" /> Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/login"
                  className="text-gray-700 hover:text-sky-600 font-medium text-sm px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-sky-600 hover:bg-sky-700 text-white font-medium text-sm px-4 py-2 rounded-lg shadow-xs transition-all"
                >
                  Register
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Hamburger Toggle Button */}
          <div className="flex md:hidden items-center gap-2">
            {user && (
              <span className="text-xs font-bold text-sky-800 bg-sky-50 px-2.5 py-1 rounded-full border border-sky-100 max-w-[120px] truncate">
                {user.name.split(' ')[0]}
              </span>
            )}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-gray-700 hover:bg-gray-100 border border-gray-200 transition-all focus:outline-hidden"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6 text-sky-700" /> : <Menu className="w-6 h-6 text-gray-800" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Drawer Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-gray-200 shadow-xl px-4 pt-3 pb-6 space-y-3 animate-in slide-in-from-top duration-200">
          <div className="flex flex-col space-y-1">
            <Link
              to="/"
              onClick={closeMobileMenu}
              className="px-3 py-2.5 rounded-xl font-bold text-sm text-gray-800 hover:bg-sky-50 hover:text-sky-600 transition-colors"
            >
              🏠 Home
            </Link>
            <Link
              to="/exams"
              onClick={closeMobileMenu}
              className="px-3 py-2.5 rounded-xl font-bold text-sm text-gray-800 hover:bg-sky-50 hover:text-sky-600 transition-colors"
            >
              📝 Daily Mock Tests
            </Link>
            <Link
              to="/past-year-papers"
              onClick={closeMobileMenu}
              className="px-3 py-2.5 rounded-xl font-extrabold text-sm text-indigo-700 bg-indigo-50 border border-indigo-100 hover:bg-indigo-100 transition-colors flex items-center justify-between"
            >
              <span>📚 Past 5 Years Question Papers</span>
              <span className="text-xxs font-black bg-indigo-600 text-white px-2 py-0.5 rounded-full">NEW</span>
            </Link>
            <Link
              to="/about"
              onClick={closeMobileMenu}
              className="px-3 py-2.5 rounded-xl font-bold text-sm text-gray-800 hover:bg-sky-50 hover:text-sky-600 transition-colors"
            >
              ℹ️ About Platform
            </Link>

            {user && (
              <Link
                to="/dashboard"
                onClick={closeMobileMenu}
                className="px-3 py-2.5 rounded-xl font-bold text-sm text-sky-800 bg-sky-50/70 border border-sky-100 hover:bg-sky-100 transition-colors flex items-center gap-2"
              >
                <LayoutDashboard className="w-4 h-4 text-sky-600" /> Student Dashboard
              </Link>
            )}

            {isAdmin && (
              <div className="pt-2 border-t border-gray-100 space-y-1">
                <span className="text-xxs font-bold text-amber-800 uppercase tracking-wider px-3">Admin Tools</span>
                <Link
                  to="/admin"
                  onClick={closeMobileMenu}
                  className="px-3 py-2 rounded-xl font-bold text-xs text-amber-900 hover:bg-amber-50 flex items-center gap-2"
                >
                  <ShieldCheck className="w-4 h-4 text-amber-700" /> Admin Control Center
                </Link>
                <Link
                  to="/admin/past-year-papers"
                  onClick={closeMobileMenu}
                  className="px-3 py-2 rounded-xl font-bold text-xs text-amber-900 hover:bg-amber-50 flex items-center gap-2"
                >
                  <FileText className="w-4 h-4 text-amber-700" /> Manage Past Papers
                </Link>
                <Link
                  to="/admin/scheduler"
                  onClick={closeMobileMenu}
                  className="px-3 py-2 rounded-xl font-bold text-xs text-amber-900 hover:bg-amber-50 flex items-center gap-2"
                >
                  <Calendar className="w-4 h-4 text-amber-700" /> 7-Day Rolling Scheduler
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Auth Actions */}
          <div className="pt-3 border-t border-gray-100">
            {user ? (
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold text-red-600 bg-red-50 hover:bg-red-100 rounded-xl border border-red-200 transition-colors"
              >
                <LogOut className="w-4 h-4" /> Logout ({user.name})
              </button>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                <Link
                  to="/login"
                  onClick={closeMobileMenu}
                  className="w-full text-center py-2.5 rounded-xl font-bold text-sm text-gray-800 border border-gray-300 hover:bg-gray-100"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  onClick={closeMobileMenu}
                  className="w-full text-center py-2.5 rounded-xl font-bold text-sm text-white bg-sky-600 hover:bg-sky-700 shadow-xs"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};
