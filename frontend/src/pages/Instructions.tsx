import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API from '../services/api';
import { Test } from '../types';
import { FileText, Clock, AlertCircle, CheckSquare, ArrowRight, ShieldCheck } from 'lucide-react';

export const Instructions: React.FC = () => {
  const { testId } = useParams<{ testId: string }>();
  const [test, setTest] = useState<Test | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [confirmed, setConfirmed] = useState<boolean>(false);
  const [starting, setStarting] = useState<boolean>(false);

  const navigate = useNavigate();

  useEffect(() => {
    if (!testId) return;

    API.get(`/tests/${testId}`)
      .then((res) => {
        setTest(res.data);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [testId]);

  const handleStartExam = async () => {
    if (!testId || !confirmed) return;

    try {
      setStarting(true);
      const res = await API.post('/attempts/start', { test_id: parseInt(testId) });
      navigate(`/exam/${res.data.attempt_id}`);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to start exam attempt.');
      setStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <div className="h-64 bg-gray-200 animate-pulse rounded-2xl"></div>
      </div>
    );
  }

  if (!test) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <h2 className="text-2xl font-bold text-gray-900">Test Instructions Not Found</h2>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        {/* Header */}
        <div className="bg-sky-900 text-white p-6 sm:p-8">
          <span className="text-xs font-semibold px-3 py-1 bg-sky-500/20 text-sky-200 rounded-full border border-sky-400/30 uppercase tracking-wider">
            {test.exam_name || 'TNPSC Mock Assessment'}
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold mt-2">{test.title}</h1>
          <p className="text-sky-100 text-sm mt-1">Examination Instructions & Student Guidelines</p>
        </div>

        <div className="p-6 sm:p-8 space-y-6">
          {/* Key Parameters Cards */}
          <div className="grid grid-cols-3 gap-4 bg-sky-50/60 p-4 rounded-xl text-center border border-sky-100">
            <div>
              <span className="text-xs text-gray-500 block font-medium">Total Questions</span>
              <span className="text-xl font-bold text-sky-900">{test.question_count}</span>
            </div>
            <div>
              <span className="text-xs text-gray-500 block font-medium">Duration</span>
              <span className="text-xl font-bold text-sky-900">{test.duration_minutes} Mins</span>
            </div>
            <div>
              <span className="text-xs text-gray-500 block font-medium">Total Marks</span>
              <span className="text-xl font-bold text-sky-900">{test.question_count} Marks</span>
            </div>
          </div>

          {/* Rules List */}
          <div className="space-y-3">
            <h3 className="font-bold text-gray-900 text-base flex items-center gap-2">
              <FileText className="w-5 h-5 text-sky-600" /> Exam Rules & Guidelines
            </h3>
            <ul className="space-y-2 text-sm text-gray-700 list-disc list-inside leading-relaxed bg-gray-50 p-4 rounded-xl border border-gray-200">
              <li>Each question has 4 options (A, B, C, D) with exactly one correct answer.</li>
              <li>Read every question carefully before choosing your response.</li>
              <li>Your selected answers are <strong>automatically saved</strong> to the server in real-time.</li>
              <li>You can navigate between questions using the Previous/Next buttons or the Question Palette.</li>
              <li>Once submitted, the test cannot be restarted or edited.</li>
              <li>The test will <strong>automatically submit</strong> when the timer reaches zero.</li>
            </ul>
          </div>

          {/* Confirmation Checkbox */}
          <div className="pt-4 border-t border-gray-100">
            <label className="flex items-start gap-3 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="w-5 h-5 text-sky-600 rounded border-gray-300 focus:ring-sky-500 mt-0.5"
              />
              <span className="text-sm font-medium text-gray-800">
                I have read and understood all the instructions above and agree to abide by the exam guidelines.
              </span>
            </label>
          </div>

          {/* Action Button */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleStartExam}
              disabled={!confirmed || starting}
              className={`w-full sm:w-auto px-8 py-3.5 rounded-xl font-bold text-sm shadow flex items-center justify-center gap-2 transition-all ${
                confirmed && !starting
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {starting ? 'Initializing Exam...' : 'Start Exam'} <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
