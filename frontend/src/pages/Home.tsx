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
            <Zap className="w-3.5 h-3.5 text-amber-400" /> Dedicated TNPSC Mock Exam Platform
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            Prepare Smarter. <span className="text-sky-300">Test Every Day.</span>
          </h1>
          <p className="text-lg sm:text-xl text-sky-100 max-w-2xl mx-auto leading-relaxed">
            Daily online assessments for TNPSC Group 1, Group 2 & Group 4 competitive-exam preparation.
          </p>
          <div className="flex flex-wrap justify-center gap-4 pt-4">
            <Link
              to="/exams"
              className="bg-white text-sky-900 hover:bg-sky-50 font-bold px-8 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
            >
              Explore Exams <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/login"
              className="bg-sky-700/60 hover:bg-sky-700 text-white font-semibold px-8 py-3.5 rounded-xl border border-sky-400/30 transition-all"
            >
              Login to Account
            </Link>
          </div>
        </div>
      </section>

      {/* Supported Exam Categories Cards (Exactly 3 Cards) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900">TNPSC Exam Categories</h2>
          <p className="text-gray-600 mt-2">Targeted mock assessments strictly tailored for Tamil Nadu Public Service Commission exams</p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-64 bg-gray-200 animate-pulse rounded-2xl"></div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {exams.map((exam) => {
              const isGroup2 = exam.slug === 'tnpsc-group-2';
              return (
                <div
                  key={exam.id}
                  className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-lg">
                        {exam.slug.split('-').pop()?.toUpperCase()}
                      </div>
                      <span className={`text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1 ${
                        isGroup2 ? 'bg-indigo-100 text-indigo-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        <Globe className="w-3.5 h-3.5" />
                        {isGroup2 ? 'தமிழ் + English' : 'தமிழ்'}
                      </span>
                    </div>

                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{exam.name}</h3>
                    <p className="text-sm text-gray-600 mb-4 line-clamp-3">{exam.description}</p>
                  </div>

                  <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-gray-500 block">Assessment Price</span>
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
              );
            })}
          </div>
        )}
      </section>

      {/* How It Works Section */}
      <section className="bg-sky-50/70 border-y border-sky-100 py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">How It Works</h2>
            <p className="text-gray-600 mt-2">Simple 5-step journey to boost your exam readiness</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 text-center">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">1</div>
              <h4 className="font-bold text-gray-900 mb-1">Choose Exam</h4>
              <p className="text-xs text-gray-600">Group 1, Group 2, or Group 4.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">2</div>
              <h4 className="font-bold text-gray-900 mb-1">Purchase Test</h4>
              <p className="text-xs text-gray-600">Unlock your daily assessment with ease.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">3</div>
              <h4 className="font-bold text-gray-900 mb-1">Attend Assessment</h4>
              <p className="text-xs text-gray-600">Timed test with auto-save & language switcher.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-sky-100">
              <div className="w-12 h-12 rounded-full bg-sky-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">4</div>
              <h4 className="font-bold text-gray-900 mb-1">Get Instant Result</h4>
              <p className="text-xs text-gray-600">Score, percentage & full explanations.</p>
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
