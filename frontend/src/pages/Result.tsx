import React, { useEffect, useState } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import API from '../services/api';
import { ResultData } from '../types';
import { CheckCircle2, XCircle, AlertCircle, Clock, LayoutDashboard, HelpCircle, Globe } from 'lucide-react';

export const Result: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const [searchParams] = useSearchParams();
  const initialLang = searchParams.get('language') || 'ta';

  const [result, setResult] = useState<ResultData | null>(null);
  const [activeLanguage, setActiveLanguage] = useState<string>(initialLang);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!attemptId) return;
    fetchResult(attemptId, activeLanguage);
  }, [attemptId, activeLanguage]);

  const fetchResult = (attId: string, lang: string) => {
    setLoading(true);
    API.get(`/results/${attId}?language=${lang}`)
      .then((res) => {
        setResult(res.data);
        setActiveLanguage(res.data.active_language || 'ta');
      })
      .catch(() => {
        API.get(`/past-year-papers/attempts/${attId}/result?language=${lang}`)
          .then((res) => {
            setResult(res.data);
            setActiveLanguage(res.data.active_language || 'ta');
          })
          .catch((err) => console.error(err));
      })
      .finally(() => setLoading(false));
  };

  if (loading && !result) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-sky-600 border-t-transparent mx-auto"></div>
        <p className="text-sm font-semibold text-gray-600">Calculating Assessment Performance...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h2 className="text-2xl font-bold text-gray-900">Result Not Found</h2>
      </div>
    );
  }

  const isDualLanguage = result.allowed_languages && result.allowed_languages.length > 1;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-8">
      {/* Top Banner Card */}
      <div className="bg-gradient-to-r from-sky-900 to-indigo-900 text-white rounded-2xl p-8 shadow-lg text-center space-y-4">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 uppercase tracking-wider">
          <CheckCircle2 className="w-4 h-4" /> Assessment Completed
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold">{result.test_title}</h1>
        <p className="text-sky-200 text-sm">{result.exam_name} Daily Mock Examination</p>

        {/* Score & Percentage Big Badges */}
        <div className="flex flex-wrap justify-center items-center gap-6 pt-4">
          <div className="bg-white/10 backdrop-blur-md rounded-2xl px-8 py-4 border border-white/10">
            <span className="text-xs text-sky-200 block uppercase font-medium">Your Score</span>
            <span className="text-4xl font-black text-white">{result.score} <span className="text-xl font-normal text-sky-300">/ {result.total_questions}</span></span>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-2xl px-8 py-4 border border-white/10">
            <span className="text-xs text-sky-200 block uppercase font-medium">Percentage</span>
            <span className="text-4xl font-black text-emerald-400">{result.percentage}%</span>
          </div>
        </div>
      </div>

      {/* Metrics Breakdown Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-xl border border-gray-200 text-center shadow-xs">
          <span className="text-xs text-gray-500 block font-medium">Correct</span>
          <span className="text-2xl font-black text-emerald-600 flex items-center justify-center gap-1 mt-1">
            <CheckCircle2 className="w-5 h-5" /> {result.correct_answers}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 text-center shadow-xs">
          <span className="text-xs text-gray-500 block font-medium">Incorrect</span>
          <span className="text-2xl font-black text-red-600 flex items-center justify-center gap-1 mt-1">
            <XCircle className="w-5 h-5" /> {result.wrong_answers}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 text-center shadow-xs">
          <span className="text-xs text-gray-500 block font-medium">Unanswered</span>
          <span className="text-2xl font-black text-amber-600 flex items-center justify-center gap-1 mt-1">
            <AlertCircle className="w-5 h-5" /> {result.unanswered}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 text-center shadow-xs">
          <span className="text-xs text-gray-500 block font-medium">Total Questions</span>
          <span className="text-2xl font-black text-gray-800 mt-1">{result.total_questions}</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 text-center shadow-xs col-span-2 sm:col-span-1">
          <span className="text-xs text-gray-500 block font-medium">Time Taken</span>
          <span className="text-2xl font-black text-sky-700 flex items-center justify-center gap-1 mt-1">
            <Clock className="w-5 h-5" /> {result.time_taken || 'N/A'}
          </span>
        </div>
      </div>

      {/* Question-by-Question Review Section */}
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-2xl font-bold text-gray-900">Question Review & Solutions</h2>

          <div className="flex items-center gap-3">
            {isDualLanguage && (
              <div className="bg-gray-200 p-1 rounded-xl flex items-center gap-1">
                <span className="text-xs text-gray-600 px-2 flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5" /> Language:
                </span>
                <button
                  onClick={() => setActiveLanguage('ta')}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                    activeLanguage === 'ta'
                      ? 'bg-sky-600 text-white shadow'
                      : 'text-gray-700 hover:text-black'
                  }`}
                >
                  தமிழ்
                </button>
                <button
                  onClick={() => setActiveLanguage('en')}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                    activeLanguage === 'en'
                      ? 'bg-sky-600 text-white shadow'
                      : 'text-gray-700 hover:text-black'
                  }`}
                >
                  English
                </button>
              </div>
            )}

            <Link
              to="/dashboard"
              className="bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs sm:text-sm px-4 py-2 rounded-lg flex items-center gap-1.5 shadow-sm transition-all"
            >
              <LayoutDashboard className="w-4 h-4" /> Return to Dashboard
            </Link>
          </div>
        </div>

        <div className="space-y-6">
          {result.questions_review.map((q) => {
            let statusBadge = (
              <span className="px-3 py-1 bg-gray-100 text-gray-700 font-semibold text-xs rounded-full flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" /> Not Answered
              </span>
            );

            if (q.status === 'Correct') {
              statusBadge = (
                <span className="px-3 py-1 bg-emerald-100 text-emerald-800 font-semibold text-xs rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> ✅ Correct
                </span>
              );
            } else if (q.status === 'Incorrect') {
              statusBadge = (
                <span className="px-3 py-1 bg-red-100 text-red-800 font-semibold text-xs rounded-full flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5" /> ❌ Incorrect
                </span>
              );
            }

            return (
              <div key={q.question_group_id} className="bg-white rounded-xl border border-gray-200 shadow-xs p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <span className="font-bold text-sky-800 text-sm">Question {q.question_order}</span>
                  {statusBadge}
                </div>

                <p className="text-base font-semibold text-gray-900">{q.question_text}</p>

                {/* Options Review List */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                  {[
                    { key: 'A', text: q.option_a },
                    { key: 'B', text: q.option_b },
                    { key: 'C', text: q.option_c },
                    { key: 'D', text: q.option_d },
                  ].map((opt) => {
                    const isStudent = q.student_answer?.toUpperCase() === opt.key;
                    const isCorrect = q.correct_answer?.toUpperCase() === opt.key;

                    let optBg = 'bg-gray-50 border-gray-200 text-gray-700';
                    if (isCorrect) {
                      optBg = 'bg-emerald-50 border-emerald-500 text-emerald-900 font-bold';
                    } else if (isStudent && !isCorrect) {
                      optBg = 'bg-red-50 border-red-400 text-red-900 font-medium';
                    }

                    return (
                      <div key={opt.key} className={`p-3 rounded-lg border flex items-start gap-2 ${optBg}`}>
                        <span className="font-bold text-xs uppercase px-1.5 py-0.5 bg-white/60 rounded border border-gray-300">
                          {opt.key}
                        </span>
                        <span className="flex-1">{opt.text}</span>
                        {isCorrect && <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />}
                        {isStudent && !isCorrect && <XCircle className="w-4 h-4 text-red-600 flex-shrink-0" />}
                      </div>
                    );
                  })}
                </div>

                {/* Answers Comparison Line */}
                <div className="flex flex-wrap gap-4 text-xs font-semibold pt-1">
                  <span className="text-gray-600">
                    Student Answer: <strong className={q.student_answer ? (q.status === 'Correct' ? 'text-emerald-700' : 'text-red-700') : 'text-gray-500'}>{q.student_answer || 'Not Answered'}</strong>
                  </span>
                  <span className="text-gray-600">
                    Correct Answer: <strong className="text-emerald-700">{q.correct_answer}</strong>
                  </span>
                </div>

                {/* Explanation Box */}
                {q.explanation && (
                  <div className="bg-sky-50 border border-sky-200 rounded-lg p-4 text-xs text-sky-950 space-y-1">
                    <strong className="block font-bold text-sky-900 flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5 text-sky-600" /> Explanation
                    </strong>
                    <p className="leading-relaxed">{q.explanation}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
