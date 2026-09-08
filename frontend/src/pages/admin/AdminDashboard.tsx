import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import API from '../../services/api';
import { AdminStats } from '../../types';
import { Users, BookOpen, FileText, CheckCircle2, DollarSign, Clock, ShieldCheck, Key } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    API.get('/admin/stats')
      .then((res) => setStats(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="h-64 bg-gray-200 animate-pulse rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Admin Header */}
      <div className="bg-gradient-to-r from-amber-800 to-amber-950 text-white rounded-2xl p-8 shadow-md flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold px-3 py-1 bg-amber-500/20 text-amber-200 rounded-full border border-amber-400/30 uppercase tracking-wider">
            Admin Control Center
          </span>
          <h1 className="text-3xl font-extrabold mt-2">TNPSC Platform Administration</h1>
          <p className="text-amber-100 text-sm mt-1">Manage exam categories, daily tests, questions, students, and payment audit logs.</p>
        </div>
      </div>

      {/* Admin Navigation Quick Links */}
      <div className="grid grid-cols-2 sm:grid-cols-7 gap-3">
        <Link to="/admin/scheduler" className="bg-amber-600 text-white p-4 rounded-xl text-center font-extrabold hover:bg-amber-700 transition-all text-xs sm:text-sm shadow-sm flex items-center justify-center gap-1">
          📅 Daily Scheduler
        </Link>
        <Link to="/admin/past-year-papers" className="bg-indigo-600 text-white p-4 rounded-xl text-center font-extrabold hover:bg-indigo-700 transition-all text-xs sm:text-sm shadow-sm flex items-center justify-center gap-1">
          📄 Past Papers
        </Link>
        <Link to="/admin/exams" className="bg-white border border-gray-200 p-4 rounded-xl text-center font-bold text-gray-800 hover:border-amber-500 hover:text-amber-700 transition-all text-xs sm:text-sm">
          📚 Exams ({stats?.total_exams || 0})
        </Link>
        <Link to="/admin/tests" className="bg-white border border-gray-200 p-4 rounded-xl text-center font-bold text-gray-800 hover:border-amber-500 hover:text-amber-700 transition-all text-xs sm:text-sm">
          📝 Daily Tests ({stats?.tests_published || 0})
        </Link>
        <Link to="/admin/questions" className="bg-white border border-gray-200 p-4 rounded-xl text-center font-bold text-gray-800 hover:border-amber-500 hover:text-amber-700 transition-all text-xs sm:text-sm">
          ❓ Questions Editor
        </Link>
        <Link to="/admin/students" className="bg-white border border-amber-300 bg-amber-50/50 p-4 rounded-xl text-center font-bold text-amber-900 hover:bg-amber-100 transition-all text-xs sm:text-sm flex items-center justify-center gap-1">
          <Key className="w-4 h-4 text-amber-700" /> Students & Access
        </Link>
        <Link to="/admin/payments" className="bg-white border border-gray-200 p-4 rounded-xl text-center font-bold text-gray-800 hover:border-amber-500 hover:text-amber-700 transition-all text-xs sm:text-sm">
          💳 Payments Audit
        </Link>
      </div>


      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-gray-500 block font-medium">Total Registered Students</span>
            <span className="text-2xl font-black text-gray-900">{stats?.total_students || 0}</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-gray-500 block font-medium">Completed Tests</span>
            <span className="text-2xl font-black text-emerald-600">{stats?.completed_tests || 0}</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-gray-500 block font-medium">Total Revenue</span>
            <span className="text-2xl font-black text-amber-700">₹{stats?.total_revenue || 0}</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-gray-500 block font-medium">Today's Attempts</span>
            <span className="text-2xl font-black text-purple-700">{stats?.today_attempts || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
