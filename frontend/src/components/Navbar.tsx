import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen, User as UserIcon, LogOut, ShieldCheck, LayoutDashboard } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-lg bg-sky-600 flex items-center justify-center text-white font-bold text-xl shadow">
                TN
              </div>
              <div>
                <span className="text-xl font-extrabold text-gray-900 tracking-tight">TNPSC</span>
                <span className="text-xs font-semibold text-sky-600 block uppercase tracking-wider">Mock Assessment</span>
              </div>
            </Link>
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

          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3">
                <span className="hidden sm:inline-block text-sm font-medium text-gray-700">
                  Hi, <strong className="text-sky-700">{user.name}</strong>
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors border border-red-200"
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
                  className="bg-sky-600 hover:bg-sky-700 text-white font-medium text-sm px-4 py-2 rounded-lg shadow-sm transition-all"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
