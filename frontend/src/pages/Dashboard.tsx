import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import API from '../services/api';
import { useAuth } from '../context/AuthContext';
import { AttemptSummary, Exam, Test } from '../types';
import { ArrowRight, Eye, Globe, Zap } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [exams, setExams] = useState<Exam[]>([]);
  const [todaysTest, setTodaysTest] = useState<Test | null>(null);
  const [pastResults, setPastResults] = useState<AttemptSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    Promise.all([
      API.get('/exams'),
      API.get('/tests'),
      API.get('/results'),
    ])
      .then(([examsRes, testsRes, resultsRes]) => {
        setExams(examsRes.data);
        if (testsRes.data && testsRes.data.length > 0) {
          setTodaysTest(testsRes.data[0]);
        }
        setPastResults(resultsRes.data);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getExamStats = (examName: string) => {
    const matching = pastResults.filter((r) => r.exam_name.toLowerCase() === examName.toLowerCase());
    const count = matching.length;
    const bestScore = count > 0 ? Math.max(...matching.map((r) => r.percentage)) : 0;
    return { count, bestScore };
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="h-64 bg-gray-200 animate-pulse rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-sky-800 to-sky-950 text-white rounded-2xl p-8 shadow-md flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold px-3 py-1 bg-sky-500/20 text-sky-200 rounded-full border border-sky-400/30 uppercase tracking-wider">
            Student Dashboard
          </span>
          <h1 className="text-3xl font-extrabold mt-2">Welcome, {user?.name || 'Student'}</h1>
          <p className="text-sky-100 text-sm mt-1">Track your daily assessments and historical performance metrics.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-center border border-white/10">
            <span className="text-xs text-sky-200 block">Tests Completed</span>
            <span className="text-2xl font-black text-white">{pastResults.length}</span>
          </div>
        </div>
      </div>

      {/* Today's Test Feature Card */}
      {todaysTest && (
        <section className="bg-white rounded-2xl border-2 border-sky-500 shadow-sm p-6 sm:p-8 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3">
            <span className="text-xs font-bold px-3 py-1 bg-sky-100 text-sky-800 rounded-full flex items-center gap-1">
              <Zap className="w-3.5 h-3.5 text-amber-500" /> Today's Featured Assessment
            </span>
            <span className="text-xs text-gray-500">Available Date: {todaysTest.test_date || 'Today'}</span>
          </div>

          <div className="flex flex-wrap justify-between items-center gap-4">
            <div>
              <span className="text-xs font-semibold text-sky-600 uppercase">{todaysTest.exam_name}</span>
              <h2 className="text-2xl font-extrabold text-gray-900">{todaysTest.title}</h2>
              <p className="text-sm text-gray-600 mt-1 max-w-xl">{todaysTest.description}</p>
            </div>

            <div className="flex items-center gap-6 bg-gray-50 p-4 rounded-xl border border-gray-200">
              <div className="text-center">
                <span className="text-xs text-gray-500 block">Questions</span>
                <strong className="text-gray-900">{todaysTest.question_count}</strong>
              </div>
              <div className="text-center">
                <span className="text-xs text-gray-500 block">Duration</span>
                <strong className="text-gray-900">{todaysTest.duration_minutes} Mins</strong>
              </div>
              <div className="text-center">
                <span className="text-xs text-gray-500 block">Price</span>
                <strong className="text-sky-700">₹{todaysTest.price}</strong>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Link
              to={`/exams/${todaysTest.exam_id}`}
              className="bg-sky-600 hover:bg-sky-700 text-white font-bold text-sm px-6 py-3 rounded-xl shadow flex items-center gap-2 transition-all"
            >
              {todaysTest.has_access ? 'Start Exam' : 'Buy & Attend Test'} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>
      )}

      {/* Exam Category Containers (Exactly 3 Containers: Group 1, Group 2, Group 4) */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900">Exam Performance Containers</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
          {exams.map((exam) => {
            const stats = getExamStats(exam.name);
            const isGroup2 = exam.slug === 'tnpsc-group-2';
            return (
              <div key={exam.id} className="bg-white rounded-2xl border border-gray-200 p-6 shadow-xs space-y-4 flex flex-col justify-between hover:border-sky-300 transition-colors">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <h3 className="text-lg font-bold text-gray-900">{exam.name}</h3>
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-sky-100 text-sky-800">
                      {isGroup2 ? 'தமிழ் + EN' : 'தமிழ்'}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500 block">Daily Mock Assessments</span>

                  <div className="mt-4 space-y-2 bg-gray-50 p-3 rounded-lg text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Tests Completed:</span>
                      <strong className="text-gray-900">{stats.count}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Best Score:</span>
                      <strong className="text-emerald-600">{stats.count > 0 ? `${stats.bestScore}%` : 'N/A'}</strong>
                    </div>
                  </div>
                </div>

                <Link
                  to={`/exams/${exam.id}`}
                  className="w-full bg-gray-100 hover:bg-sky-50 hover:text-sky-700 text-gray-700 font-semibold text-xs py-2.5 rounded-lg text-center transition-colors block border border-gray-200"
                >
                  View Category & Tests
                </Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* Past Test Results Section */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900">Recent Test Results</h2>
        <div className="bg-white rounded-2xl border border-gray-200 shadow-xs overflow-hidden">
          {pastResults.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No completed test attempts recorded yet. Purchase and attend your first exam to view results!
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                  <tr>
                    <th className="p-4">Test Title</th>
                    <th className="p-4">Exam</th>
                    <th className="p-4">Submitted Date</th>
                    <th className="p-4">Score</th>
                    <th className="p-4">Percentage</th>
                    <th className="p-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-gray-800">
                  {pastResults.map((res) => (
                    <tr key={res.attempt_id} className="hover:bg-sky-50/50 transition-colors">
                      <td className="p-4 font-bold text-gray-900">{res.test_title}</td>
                      <td className="p-4 font-medium text-sky-700">{res.exam_name}</td>
                      <td className="p-4 text-xs text-gray-500">
                        {res.submitted_at ? new Date(res.submitted_at).toLocaleDateString() : 'Today'}
                      </td>
                      <td className="p-4 font-bold">{res.score} / {res.total_questions}</td>
                      <td className="p-4">
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                          {res.percentage}%
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <Link
                          to={`/result/${res.attempt_id}`}
                          className="inline-flex items-center gap-1 text-xs font-bold text-sky-600 hover:text-sky-800 bg-sky-50 px-3 py-1.5 rounded-lg border border-sky-200"
                        >
                          <Eye className="w-3.5 h-3.5" /> View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
