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
            NEW FEATURE: PAST 5 YEARS PAPERS
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold">Original TNPSC Question Papers (2021 – 2025)</h2>
          <p className="text-sky-200 text-xs sm:text-sm">
            Access previous 5 years' actual TNPSC Group 1, Group 2, and Group 4 papers permanently with instant evaluation and solutions.
          </p>
        </div>
        <Link
          to="/past-year-papers"
          className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-black text-xs sm:text-sm px-6 py-3 rounded-2xl shadow-lg transition-all flex items-center gap-2"
        >
          Explore Past Papers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <div>
        <h1 className="text-3xl font-extrabold text-gray-900">TNPSC Daily Mock Assessments</h1>
        <p className="text-gray-600 mt-2">Select your targeted exam category to explore daily scheduled mock assessments (12 PM IST Rotation)</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-72 bg-gray-200 animate-pulse rounded-2xl"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {exams.map((exam) => {
            const isGroup2 = exam.slug === 'tnpsc-group-2';
            return (
              <div key={exam.id} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition-shadow">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-semibold px-2.5 py-1 bg-sky-100 text-sky-800 rounded-full">
                      Daily Assessment
                    </span>
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full flex items-center gap-1 ${
                      isGroup2 ? 'bg-indigo-100 text-indigo-800' : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      <Globe className="w-3.5 h-3.5" />
                      {isGroup2 ? 'தமிழ் + English' : 'தமிழ்'}
                    </span>
                  </div>

                  <h3 className="text-2xl font-extrabold text-gray-900 mb-2">{exam.name}</h3>
                  <p className="text-sm text-gray-600 mb-6">{exam.description || 'Comprehensive daily practice tests'}</p>

                  <ul className="space-y-2 text-xs text-gray-600 mb-6">
                    <li className="flex items-center justify-between border-b border-gray-100 pb-1">
                      <span>Target Exam:</span>
                      <strong className="text-gray-900">{exam.name}</strong>
                    </li>
                    <li className="flex items-center justify-between border-b border-gray-100 pb-1">
                      <span>Allowed Medium:</span>
                      <strong className="text-sky-800 font-bold">{isGroup2 ? 'Tamil & English' : 'Tamil Only'}</strong>
                    </li>
                    <li className="flex items-center justify-between pb-1">
                      <span>Evaluation:</span>
                      <strong className="text-gray-900">Server-Side Auto</strong>
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
            );
          })}
        </div>
      )}
    </div>
  );
};
