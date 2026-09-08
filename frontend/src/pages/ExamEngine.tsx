import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API from '../services/api';
import { AttemptEngineData, QuestionClient } from '../types';
import { QuestionPalette } from '../components/QuestionPalette';
import { Clock, ArrowLeft, ArrowRight, Save, Globe, AlertCircle } from 'lucide-react';

export const ExamEngine: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const [engineData, setEngineData] = useState<AttemptEngineData | null>(null);
  const [currentLanguage, setCurrentLanguage] = useState<string>('ta');
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [savedAnswers, setSavedAnswers] = useState<Record<number, string>>({}); // question_group_id -> option
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [switchingLanguage, setSwitchingLanguage] = useState<boolean>(false);
  const [savingAnswer, setSavingAnswer] = useState<boolean>(false);
  const [showSubmitModal, setShowSubmitModal] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const navigate = useNavigate();
  const timerRef = useRef<any>(null);

  const [isPastYear, setIsPastYear] = useState<boolean>(false);

  // Load initial attempt data
  useEffect(() => {
    if (!attemptId) return;

    // Try past-year attempt first, fallback to daily mock attempt
    API.get(`/past-year-papers/attempts/${attemptId}?language=ta`)
      .then((res) => {
        const data: AttemptEngineData = res.data;
        setEngineData(data);
        setIsPastYear(true);
        setCurrentLanguage(data.current_language || 'ta');
        setSavedAnswers(data.saved_answers || {});
        setRemainingSeconds(data.remaining_seconds);
      })
      .catch(() => {
        // Fallback to daily mock attempt
        API.get(`/attempts/${attemptId}?language=ta`)
          .then((res) => {
            const data: AttemptEngineData = res.data;
            setEngineData(data);
            setIsPastYear(false);
            setCurrentLanguage(data.current_language || 'ta');
            setSavedAnswers(data.saved_answers || {});
            setRemainingSeconds(data.remaining_seconds);
          })
          .catch((err) => {
            alert(err.response?.data?.detail || 'Failed to load exam attempt.');
            navigate('/dashboard');
          });
      })
      .finally(() => setLoading(false));
  }, [attemptId, navigate]);

  // Countdown Timer
  useEffect(() => {
    if (remainingSeconds <= 0) return;

    timerRef.current = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [remainingSeconds]);

  // Language Switcher for Group 2
  const handleSwitchLanguage = async (targetLang: string) => {
    if (targetLang === currentLanguage || switchingLanguage || !attemptId) return;

    try {
      setSwitchingLanguage(true);
      const endpoint = isPastYear
        ? `/past-year-papers/attempts/${attemptId}?language=${targetLang}`
        : `/attempts/${attemptId}?language=${targetLang}`;
      const res = await API.get(endpoint);
      const data: AttemptEngineData = res.data;
      setEngineData(data);
      setCurrentLanguage(targetLang);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to switch question language.');
    } finally {
      setSwitchingLanguage(false);
    }
  };

  // Option Select (Auto-save against question_group_id)
  const handleSelectOption = async (option: string) => {
    if (!engineData) return;
    const currentQ = engineData.questions[currentIndex];
    if (!currentQ) return;

    const groupId = currentQ.question_group_id;

    // Optimistic UI state update
    const updatedAnswers = { ...savedAnswers, [groupId]: option };
    setSavedAnswers(updatedAnswers);

    // Auto-save to backend using question_group_id
    try {
      setSavingAnswer(true);
      const endpoint = isPastYear
        ? `/past-year-papers/attempts/${attemptId}/answer`
        : `/attempts/${attemptId}/answer`;
      await API.post(endpoint, {
        question_group_id: groupId,
        selected_option: option,
      });
    } catch (error) {
      console.error('Failed to auto-save answer', error);
    } finally {
      setSavingAnswer(false);
    }
  };

  const handleAutoSubmit = async () => {
    if (submitting) return;
    try {
      setSubmitting(true);
      const endpoint = isPastYear
        ? `/past-year-papers/attempts/${attemptId}/submit`
        : `/attempts/${attemptId}/submit`;
      await API.post(endpoint);
      navigate(`/result/${attemptId}?language=${currentLanguage}`);
    } catch (err) {
      console.error(err);
      navigate(`/result/${attemptId}?language=${currentLanguage}`);
    }
  };

  const handleSubmitConfirmed = async () => {
    if (!attemptId) return;
    try {
      setSubmitting(true);
      const endpoint = isPastYear
        ? `/past-year-papers/attempts/${attemptId}/submit`
        : `/attempts/${attemptId}/submit`;
      await API.post(endpoint);
      navigate(`/result/${attemptId}?language=${currentLanguage}`);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to submit exam.');
      setSubmitting(false);
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (loading || !engineData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-sky-600 border-t-transparent mx-auto"></div>
          <p className="text-sm font-semibold text-gray-600">Loading TNPSC Exam Interface...</p>
        </div>
      </div>
    );
  }

  const questions = engineData.questions || [];
  const currentQuestion = questions[currentIndex];
  const totalQuestions = engineData.questions.length;
  const isDualLanguage = engineData.allowed_languages && engineData.allowed_languages.length > 1;

  // Calculate answered count based on question_group_ids in current test
  const questionGroupIds = questions.map((q) => q.question_group_id);
  const answeredCount = questionGroupIds.filter((gid) => savedAnswers[gid] !== undefined && savedAnswers[gid] !== null).length;
  const unansweredCount = totalQuestions - answeredCount;

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Top Fixed Header Bar */}
      <header className="bg-sky-900 text-white px-4 sm:px-8 py-3 flex items-center justify-between shadow-md sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <span className="font-bold text-lg">{engineData.exam_name || 'TNPSC'}</span>
          <span className="text-sky-300 hidden sm:inline">|</span>
          <span className="text-xs bg-sky-800 text-sky-100 px-2.5 py-1 rounded-md hidden sm:inline">
            {engineData.test_title}
          </span>
        </div>

        {/* Middle: Language Selector for Group 2 */}
        <div className="flex items-center gap-2">
          {isDualLanguage ? (
            <div className="bg-sky-950 p-1 rounded-xl border border-sky-700 flex items-center gap-1">
              <span className="text-xs text-sky-300 px-1 hidden sm:inline flex items-center gap-1">
                <Globe className="w-3 h-3" /> Language:
              </span>
              <button
                onClick={() => handleSwitchLanguage('ta')}
                disabled={switchingLanguage}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  currentLanguage === 'ta'
                    ? 'bg-sky-500 text-white shadow'
                    : 'text-sky-200 hover:text-white'
                }`}
              >
                தமிழ்
              </button>
              <button
                onClick={() => handleSwitchLanguage('en')}
                disabled={switchingLanguage}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  currentLanguage === 'en'
                    ? 'bg-sky-500 text-white shadow'
                    : 'text-sky-200 hover:text-white'
                }`}
              >
                English
              </button>
            </div>
          ) : (
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 flex items-center gap-1">
              <Globe className="w-3.5 h-3.5" /> தமிழ் Medium
            </span>
          )}
        </div>

        {/* Right: Timer & Submit Button */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 font-mono text-xl font-bold bg-sky-950 px-3 py-1 rounded-lg border border-sky-700 text-amber-400">
            <Clock className="w-5 h-5 text-amber-400 animate-pulse" />
            <span>{formatTimer(remainingSeconds)}</span>
          </div>

          <button
            onClick={() => setShowSubmitModal(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs sm:text-sm font-bold px-4 py-2 rounded-lg shadow transition-all"
          >
            Submit Test
          </button>
        </div>
      </header>

      {/* Main Examination Engine Content */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Question & Options Area */}
        <div className="lg:col-span-2 space-y-6 flex flex-col justify-between">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8 space-y-6">
            {/* Question Header */}
            <div className="flex items-center justify-between border-b border-gray-100 pb-4">
              <span className="font-bold text-sky-700 text-sm">
                Question {currentIndex + 1} of {totalQuestions}
              </span>
              <div className="flex items-center gap-3">
                {switchingLanguage && (
                  <span className="text-xs text-amber-600 font-semibold animate-pulse">Switching language...</span>
                )}
                {savingAnswer && (
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Save className="w-3.5 h-3.5 animate-spin text-sky-600" /> Saving...
                  </span>
                )}
              </div>
            </div>

            {/* Question Text */}
            {currentQuestion ? (
              <div className="space-y-6">
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 leading-relaxed">
                  {currentQuestion.question_text}
                </h2>

                {/* MCQ Options A, B, C, D */}
                <div className="space-y-3">
                  {[
                    { key: 'A', text: currentQuestion.option_a },
                    { key: 'B', text: currentQuestion.option_b },
                    { key: 'C', text: currentQuestion.option_c },
                    { key: 'D', text: currentQuestion.option_d },
                  ].map((opt) => {
                    const isSelected = savedAnswers[currentQuestion.question_group_id] === opt.key;
                    return (
                      <button
                        key={opt.key}
                        onClick={() => handleSelectOption(opt.key)}
                        className={`w-full text-left p-4 rounded-xl border text-sm sm:text-base flex items-start gap-3 transition-all ${
                          isSelected
                            ? 'bg-sky-50 border-sky-600 text-sky-900 font-semibold ring-2 ring-sky-200'
                            : 'bg-white border-gray-200 hover:border-sky-300 text-gray-800'
                        }`}
                      >
                        <span
                          className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 ${
                            isSelected ? 'bg-sky-600 text-white' : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {opt.key}
                        </span>
                        <span className="pt-0.5">{opt.text}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No questions available in selected language.</p>
            )}
          </div>

          {/* Question Navigation Controls */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between shadow-sm">
            <button
              onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentIndex === 0}
              className={`px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-1.5 transition-all ${
                currentIndex === 0
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
              }`}
            >
              <ArrowLeft className="w-4 h-4" /> Previous
            </button>

            <button
              onClick={() => setCurrentIndex((prev) => Math.min(totalQuestions - 1, prev + 1))}
              disabled={currentIndex === totalQuestions - 1}
              className={`px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-1.5 transition-all ${
                currentIndex === totalQuestions - 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-sky-600 hover:bg-sky-700 text-white shadow'
              }`}
            >
              Next <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right Column: Question Palette */}
        <div className="lg:col-span-1">
          <QuestionPalette
            totalQuestions={totalQuestions}
            currentIndex={currentIndex}
            savedAnswers={savedAnswers}
            questionIds={questionGroupIds}
            onSelectQuestion={(idx) => setCurrentIndex(idx)}
          />
        </div>
      </div>

      {/* Submission Confirmation Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">Confirm Submission</h3>
              <p className="text-xs text-gray-500">
                Are you sure you want to submit your TNPSC test attempt?
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-xl border border-gray-200 text-center">
              <div>
                <span className="text-xs text-gray-500 block font-medium">Answered</span>
                <span className="text-2xl font-black text-emerald-600">{answeredCount}</span>
                <span className="text-xs text-gray-400 block">/ {totalQuestions}</span>
              </div>
              <div>
                <span className="text-xs text-gray-500 block font-medium">Unanswered</span>
                <span className="text-2xl font-black text-amber-600">{unansweredCount}</span>
                <span className="text-xs text-gray-400 block">/ {totalQuestions}</span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowSubmitModal(false)}
                disabled={submitting}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 rounded-xl text-sm transition-all"
              >
                Continue Exam
              </button>
              <button
                onClick={handleSubmitConfirmed}
                disabled={submitting}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl text-sm shadow transition-all"
              >
                {submitting ? 'Submitting...' : 'Submit Test'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
