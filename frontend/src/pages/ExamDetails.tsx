import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API from '../services/api';
import { Exam, Test } from '../types';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Clock, Globe, CheckCircle2, ArrowRight } from 'lucide-react';

export const ExamDetails: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const [exam, setExam] = useState<Exam | null>(null);
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [purchasing, setPurchasing] = useState<boolean>(false);

  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!examId) return;

    Promise.all([
      API.get(`/exams/${examId}`),
      API.get(`/tests?exam_id=${examId}`),
    ])
      .then(([examRes, testsRes]) => {
        setExam(examRes.data);
        setTests(testsRes.data);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [examId]);

  const handleBuyOrStart = async (test: Test) => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (test.has_access) {
      navigate(`/instructions/${test.id}`);
      return;
    }

    try {
      setPurchasing(true);
      const res = await API.post('/payments/create-order', { test_id: test.id });
      if (res.data.status === 'ALREADY_PURCHASED') {
        navigate(`/instructions/${test.id}`);
      } else {
        navigate(`/payment/mock?order_id=${res.data.order_id}&test_id=${test.id}`);
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to initiate purchase order.');
    } finally {
      setPurchasing(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="h-64 bg-gray-200 animate-pulse rounded-2xl"></div>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h2 className="text-2xl font-bold text-gray-900">Exam Category Not Found</h2>
      </div>
    );
  }

  const isGroup2 = exam.slug === 'tnpsc-group-2';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-sky-800 to-indigo-900 text-white rounded-2xl p-8 shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-3 py-1 bg-sky-500/20 text-sky-200 rounded-full border border-sky-400/30 uppercase tracking-wider">
                {exam.name}
              </span>
              <span className={`text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1 ${
                isGroup2 ? 'bg-indigo-500/30 text-indigo-200' : 'bg-emerald-500/30 text-emerald-200'
              }`}>
                <Globe className="w-3.5 h-3.5" />
                {isGroup2 ? 'தமிழ் + English Medium' : 'தமிழ் Medium Only'}
              </span>
            </div>
            <h1 className="text-3xl font-extrabold mt-3">{exam.name} Daily Assessments</h1>
            <p className="text-sky-100 text-sm mt-2 max-w-xl">{exam.description}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-center border border-white/10">
            <span className="text-xs text-sky-200 block">Assessment Price</span>
            <span className="text-3xl font-black text-white">₹{exam.price}</span>
          </div>
        </div>
      </div>

      {/* Available Daily Tests List */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-sky-600" /> Available Daily Tests
        </h2>

        {tests.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
            No active tests published for this category yet. Check back soon!
          </div>
        ) : (
          tests.map((test) => (
            <div
              key={test.id}
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4 hover:border-sky-300 transition-colors"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">{test.title}</h3>
                  <span className="text-xs text-gray-500">Date: {test.test_date || 'Today'}</span>
                </div>
                {test.has_access ? (
                  <span className="px-3 py-1 bg-emerald-100 text-emerald-800 font-semibold text-xs rounded-full flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" /> Unlocked & Access Granted
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-amber-100 text-amber-800 font-semibold text-xs rounded-full">
                    Payment Required
                  </span>
                )}
              </div>

              <p className="text-sm text-gray-600">{test.description}</p>

              {/* Test Information Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-gray-50 p-4 rounded-lg text-center text-sm">
                <div>
                  <span className="text-xs text-gray-500 block">Questions</span>
                  <strong className="text-gray-900">{test.question_count} MCQs</strong>
                </div>
                <div>
                  <span className="text-xs text-gray-500 block">Duration</span>
                  <strong className="text-gray-900">{test.duration_minutes} Mins</strong>
                </div>
                <div>
                  <span className="text-xs text-gray-500 block">Languages</span>
                  <strong className="text-sky-800 font-bold">{isGroup2 ? 'Tamil & English' : 'Tamil Only'}</strong>
                </div>
                <div>
                  <span className="text-xs text-gray-500 block">Price</span>
                  <strong className="text-sky-700">₹{test.price}</strong>
                </div>
              </div>

              {/* Schedule Status Notice */}
              {test.next_publish_info && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs font-semibold text-amber-900 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-700 shrink-0" />
                  <span>{test.next_publish_info}</span>
                </div>
              )}

              {/* Action Button */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={() => handleBuyOrStart(test)}
                  disabled={purchasing || (test.has_access && test.has_active_set === false)}
                  className={`px-6 py-3 rounded-xl font-bold text-sm shadow flex items-center gap-2 transition-all ${
                    test.has_access && test.has_active_set === false
                      ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                      : test.has_access
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                      : 'bg-sky-600 hover:bg-sky-700 text-white'
                  }`}
                >
                  {purchasing ? (
                    'Processing...'
                  ) : test.has_access && test.has_active_set === false ? (
                    'Set Activates at 12:00 PM IST'
                  ) : test.has_access ? (
                    <>
                      Start Exam <ArrowRight className="w-4 h-4" />
                    </>
                  ) : (
                    <>
                      Buy & Attend Exam (₹{test.price}) <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

