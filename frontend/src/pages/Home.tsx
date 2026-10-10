import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import API from '../services/api';
import { Exam } from '../types';
import { Award, BookOpen, CheckCircle2, Clock, ShieldAlert, ArrowRight, Zap, Trophy, Globe } from 'lucide-react';

export const Home: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    API.get('/exams')
      .then((res) => setExams(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-sky-900 via-sky-800 to-indigo-900 text-white py-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]"></div>
        <div className="max-w-5xl mx-auto text-center relative z-10 space-y-6">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/20 text-sky-200 border border-sky-400/30">
            <Zap className="w-3.5 h-3.5 text-amber-400" /> Test-Score by MZAB Arcane
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            Prepare Smarter. <span className="text-sky-300">Test Every Day.</span>
          </h1>
          <p className="text-lg sm:text-xl text-sky-100 max-w-3xl mx-auto leading-relaxed">
            Daily online mock tests & FREE 5-year past papers for TNPSC (Group 1, 2, 4) & UPSC (GS & CSAT).
          </p>
          <div className="flex flex-wrap justify-center gap-4 pt-4">
            <Link
              to="/exams"
              className="bg-white text-sky-900 hover:bg-sky-50 font-bold px-8 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
            >
              Daily Mock Tests <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/past-year-papers"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-8 py-3.5 rounded-xl shadow-lg transition-all flex items-center gap-2"
            >
              📚 FREE Past Year Papers <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Primary Category Banner (2 Categories Only) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gradient-to-br from-sky-50 to-blue-100 rounded-3xl p-8 border border-sky-200 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <span className="bg-sky-600 text-white text-xs font-black px-3 py-1 rounded-full uppercase tracking-wider">
                CATEGORY 1
              </span>
              <h3 className="text-2xl font-black text-gray-900">Daily Test Assessments</h3>
              <p className="text-sm text-gray-700 leading-relaxed">
                Unlocked per purchase. Rotates daily at <strong>12:00 PM IST</strong>. Real-time online timed exam engine with server-side auto-evaluation.
              </p>
            </div>
            <div className="pt-6">
              <Link
                to="/exams"
                className="bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs px-5 py-3 rounded-xl transition-all inline-flex items-center gap-2"
              >
                Browse Daily Tests <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-50 to-purple-100 rounded-3xl p-8 border border-indigo-200 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <span className="bg-indigo-600 text-white text-xs font-black px-3 py-1 rounded-full uppercase tracking-wider">
                CATEGORY 2 • 100% FREE
              </span>
              <h3 className="text-2xl font-black text-gray-900">Past 5 Years Question Papers</h3>
              <p className="text-sm text-gray-700 leading-relaxed">
                <strong>FREE permanent questions</strong> from actual past years (2021 – 2025) for TNPSC Group 1, 2, 4 & UPSC (GS & CSAT).
              </p>
            </div>
            <div className="pt-6">
              <Link
                to="/past-year-papers"
                className="bg-indigo-700 hover:bg-indigo-800 text-white font-bold text-xs px-5 py-3 rounded-xl transition-all inline-flex items-center gap-2"
              >
                Attempt Past Papers <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Supported Exam Cards Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900">Supported Exam Categories</h2>
          <p className="text-gray-600 mt-2">Targeted assessments for TNPSC & UPSC Competitive Examinations</p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5].map((n) => (
              <div key={n} className="h-64 bg-gray-200 animate-pulse rounded-2xl"></div>
            ))}
          </div>
        ) : (
          <div className="space-y-10">
            {/* TNPSC Group Section (3 Cards) */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-gray-200 pb-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                <h3 className="text-lg font-bold text-gray-800 uppercase tracking-wider">TNPSC Examinations</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {exams.filter(e => !e.slug.startsWith('upsc')).map((exam) => (
                  <div
                    key={exam.id}
                    className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-black text-sm border border-emerald-100">
                          {exam.slug.split('-').pop()?.toUpperCase()}
                        </div>
                        <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                          <Globe className="w-3.5 h-3.5" /> தமிழ் + English
                        </span>
                      </div>

                      <h4 className="text-xl font-bold text-gray-900 mb-2">{exam.name}</h4>
                      <p className="text-xs text-gray-600 mb-4 line-clamp-3">{exam.description}</p>
                    </div>

                    <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                      <div>
                        <span className="text-xs text-gray-400 block">Assessment Fee</span>
                        <span className="text-lg font-bold text-sky-700">₹{exam.price}</span>
                      </div>
                      <Link
                        to={`/exams/${exam.id}`}
                        className="bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs px-4 py-2 rounded-lg transition-colors"
                      >
                        View Exam
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* UPSC Section (2 Cards Centered) */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-gray-200 pb-2">
                <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                <h3 className="text-lg font-bold text-gray-800 uppercase tracking-wider">UPSC Civil Services</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                {exams.filter(e => e.slug.startsWith('upsc')).map((exam) => (
                  <div
                    key={exam.id}
                    className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center font-black text-sm border border-purple-100">
                          UPSC
                        </div>
                        <span className="text-xs font-bold px-3 py-1 rounded-full bg-purple-100 text-purple-800 flex items-center gap-1">
                          <Globe className="w-3.5 h-3.5" /> English Only
                        </span>
                      </div>

                      <h4 className="text-xl font-bold text-gray-900 mb-2">{exam.name}</h4>
                      <p className="text-xs text-gray-600 mb-4 line-clamp-3">{exam.description}</p>
                    </div>

                    <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                      <div>
                        <span className="text-xs text-gray-400 block">Assessment Fee</span>
                        <span className="text-lg font-bold text-sky-700">₹{exam.price}</span>
                      </div>
                      <Link
                        to={`/exams/${exam.id}`}
                        className="bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs px-4 py-2 rounded-lg transition-colors"
                      >
                        View Exam
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>

      {/* How It Works Section */}
      <section className="bg-sky-50/70 border-y border-sky-100 py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">How It Works</h2>
            <p className="text-gray-600 mt-2">Simple 5-step journey to boost your competitive exam preparation</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 text-center">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">1</div>
              <h4 className="font-bold text-gray-900 mb-1">Choose Exam</h4>
              <p className="text-xs text-gray-600">TNPSC Group 1, 2, 4 or UPSC GS & CSAT.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">2</div>
              <h4 className="font-bold text-gray-900 mb-1">Select Category</h4>
              <p className="text-xs text-gray-600">Daily Test or FREE Past Year Papers.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">3</div>
              <h4 className="font-bold text-gray-900 mb-1">Attend Assessment</h4>
              <p className="text-xs text-gray-600">Timed test with auto-save & language switcher.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">4</div>
              <h4 className="font-bold text-gray-900 mb-1">Get Instant Result</h4>
              <p className="text-xs text-gray-600">Score, percentage & negative mark details.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">5</div>
              <h4 className="font-bold text-gray-900 mb-1">Track Progress</h4>
              <p className="text-xs text-gray-600">Review past test history on dashboard.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
