import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import API from '../services/api';
import { Exam } from '../types';
import { CheckCircle, Globe, ArrowRight } from 'lucide-react';

export const Exams: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    API.get('/exams')
      .then((res) => setExams(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      {/* Top Past Year Banner */}
      <div className="bg-gradient-to-r from-sky-900 via-indigo-900 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-wrap items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <span className="bg-amber-400/20 text-amber-300 text-xs font-extrabold px-3 py-1 rounded-full uppercase tracking-wider border border-amber-400/30">
            CATEGORY 2: 100% FREE PAST YEAR PAPERS
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold">Original TNPSC & UPSC Question Papers (2021 – 2025)</h2>
          <p className="text-sky-200 text-xs sm:text-sm">
            Access previous 5 years' actual papers for TNPSC (Group 1, 2, 4) & UPSC (GS & CSAT) permanently with instant evaluation.
          </p>
        </div>
        <Link
          to="/past-year-papers"
          className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-black text-xs sm:text-sm px-6 py-3 rounded-2xl shadow-lg transition-all flex items-center gap-2"
        >
          Explore Free Past Papers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <div>
        <h1 className="text-3xl font-extrabold text-gray-900">Daily Mock Assessments</h1>
        <p className="text-gray-600 mt-2">Daily assessments for TNPSC & UPSC (Rotates daily at 12:00 PM IST; Unlocked per purchase)</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5].map((n) => (
            <div key={n} className="h-72 bg-gray-200 animate-pulse rounded-2xl"></div>
          ))}
        </div>
      ) : (
        <div className="space-y-12">
          {/* TNPSC Examinations (3 Cards) */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 border-b border-gray-200 pb-2">
              <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
              <h3 className="text-lg font-bold text-gray-800 uppercase tracking-wider">TNPSC Examinations</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {exams.filter(e => !e.slug.startsWith('upsc')).map((exam) => (
                <div key={exam.id} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-xs font-semibold px-2.5 py-1 bg-sky-100 text-sky-800 rounded-full">
                        Daily Assessment
                      </span>
                      <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                        <Globe className="w-3.5 h-3.5" /> தமிழ் + English
                      </span>
                    </div>

                    <h4 className="text-2xl font-extrabold text-gray-900 mb-2">{exam.name}</h4>
                    <p className="text-sm text-gray-600 mb-6">{exam.description || 'Comprehensive daily practice tests'}</p>

                    <ul className="space-y-2 text-xs text-gray-600 mb-6">
                      <li className="flex items-center justify-between border-b border-gray-100 pb-1">
                        <span>Target Exam:</span>
                        <strong className="text-gray-900">{exam.name}</strong>
                      </li>
                      <li className="flex items-center justify-between border-b border-gray-100 pb-1">
                        <span>Medium:</span>
                        <strong className="text-sky-800 font-bold">Tamil & English</strong>
                      </li>
                      <li className="flex items-center justify-between pb-1">
                        <span>Negative Marking:</span>
                        <strong className="text-emerald-700 font-bold">No Negative Marks</strong>
                      </li>
                    </ul>
                  </div>

                  <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-gray-400 block">Assessment Fee</span>
                      <span className="text-2xl font-black text-sky-700">₹{exam.price}</span>
                    </div>
                    <Link
                      to={`/exams/${exam.id}`}
                      className="bg-sky-600 hover:bg-sky-700 text-white font-semibold text-sm px-4 py-2.5 rounded-xl flex items-center gap-1 shadow-sm transition-all"
                    >
                      View Exam <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* UPSC Examinations (2 Cards Centered) */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 border-b border-gray-200 pb-2">
              <span className="w-3 h-3 rounded-full bg-purple-500"></span>
              <h3 className="text-lg font-bold text-gray-800 uppercase tracking-wider">UPSC Civil Services</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {exams.filter(e => e.slug.startsWith('upsc')).map((exam) => (
                <div key={exam.id} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-xs font-semibold px-2.5 py-1 bg-purple-100 text-purple-800 rounded-full">
                        Daily Assessment
                      </span>
                      <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-purple-100 text-purple-800 flex items-center gap-1">
                        <Globe className="w-3.5 h-3.5" /> English Only
                      </span>
                    </div>

                    <h4 className="text-2xl font-extrabold text-gray-900 mb-2">{exam.name}</h4>
                    <p className="text-sm text-gray-600 mb-6">{exam.description || 'Comprehensive daily practice tests'}</p>

                    <ul className="space-y-2 text-xs text-gray-600 mb-6">
                      <li className="flex items-center justify-between border-b border-gray-100 pb-1">
                        <span>Target Exam:</span>
                        <strong className="text-gray-900">{exam.name}</strong>
                      </li>
                      <li className="flex items-center justify-between border-b border-gray-100 pb-1">
                        <span>Medium:</span>
                        <strong className="text-purple-800 font-bold">English Only</strong>
                      </li>
                      <li className="flex items-center justify-between pb-1">
                        <span>Negative Marking:</span>
                        <strong className="text-amber-700 font-extrabold">1/3rd Penalty</strong>
                      </li>
                    </ul>
                  </div>

                  <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-gray-400 block">Assessment Fee</span>
                      <span className="text-2xl font-black text-sky-700">₹{exam.price}</span>
                    </div>
                    <Link
                      to={`/exams/${exam.id}`}
                      className="bg-sky-600 hover:bg-sky-700 text-white font-semibold text-sm px-4 py-2.5 rounded-xl flex items-center gap-1 shadow-sm transition-all"
                    >
                      View Exam <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
