import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../services/api';
import { PastYearPaper, Exam } from '../types';
import { FileText, Calendar, Clock, CheckCircle2, Lock, Sparkles, Filter, Award, ShieldCheck, CreditCard } from 'lucide-react';

export const PastYearPapersPage: React.FC = () => {
  const [papers, setPapers] = useState<PastYearPaper[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [purchasingPaper, setPurchasingPaper] = useState<PastYearPaper | null>(null);
  const [paymentModalOpen, setPaymentModalOpen] = useState<boolean>(false);
  const [paymentLoading, setPaymentLoading] = useState<boolean>(false);

  const navigate = useNavigate();

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [examsRes, papersRes] = await Promise.all([
        API.get('/exams'),
        API.get('/past-year-papers')
      ]);
      setExams(examsRes.data);
      setPapers(papersRes.data);
    } catch (err) {
      console.error('Failed to load past year papers:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFilteredPapers = async (examId: number | null, year: number | null) => {
    try {
      setLoading(true);
      let url = '/past-year-papers?';
      if (examId) url += `exam_id=${examId}&`;
      if (year) url += `year=${year}&`;
      const res = await API.get(url);
      setPapers(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExamFilter = (examId: number | null) => {
    setSelectedExamId(examId);
    fetchFilteredPapers(examId, selectedYear);
  };

  const handleYearFilter = (year: number | null) => {
    setSelectedYear(year);
    fetchFilteredPapers(selectedExamId, year);
  };

  const handleStartAttempt = async (paper: PastYearPaper) => {
    try {
      const res = await API.post(`/past-year-papers/${paper.id}/start`, { language: 'ta' });
      const attemptId = res.data.attempt_id;
      navigate(`/exam-engine/${attemptId}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to start attempt.');
    }
  };

  const handleInitiatePurchase = (paper: PastYearPaper) => {
    setPurchasingPaper(paper);
    setPaymentModalOpen(true);
  };

  const handleProcessPayment = async (success: boolean) => {
    if (!purchasingPaper) return;
    try {
      setPaymentLoading(true);
      const orderRes = await API.post('/payments/create-order', { past_year_paper_id: purchasingPaper.id });

      if (orderRes.data.status === 'ALREADY_PURCHASED') {
        alert('You already have access to this paper!');
        setPaymentModalOpen(false);
        fetchFilteredPapers(selectedExamId, selectedYear);
        return;
      }

      const orderId = orderRes.data.order_id;
      const callbackRes = await API.post('/payments/process-mock', {
        order_id: orderId,
        success: success
      });

      if (success) {
        alert('Payment SUCCESS! Paper access unlocked.');
        setPaymentModalOpen(false);
        fetchFilteredPapers(selectedExamId, selectedYear);
      } else {
        alert('Payment FAILED. Paper remains locked.');
        setPaymentModalOpen(false);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Payment processing error.');
    } finally {
      setPaymentLoading(false);
    }
  };

  const yearsList = [2025, 2024, 2023, 2022, 2021];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-sky-900 via-indigo-900 to-slate-900 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl"></div>
        <div className="relative z-10 space-y-3 max-w-3xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 uppercase tracking-wider">
            <Award className="w-4 h-4" /> Official Previous Years Question Papers
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Past 5 Years TNPSC Question Papers (2021 – 2025)
          </h1>
          <p className="text-sky-200 text-sm sm:text-base leading-relaxed">
            Practice actual past-year original papers for TNPSC Group 1, Group 2 & Group 4 with real-time timed test engine, instant evaluation & detailed solutions. Permanent access included.
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-800 text-sm flex items-center gap-2">
            <Filter className="w-4 h-4 text-sky-600" /> Filter Question Papers
          </h3>
          {(selectedExamId || selectedYear) && (
            <button
              onClick={() => {
                setSelectedExamId(null);
                setSelectedYear(null);
                fetchFilteredPapers(null, null);
              }}
              className="text-xs text-sky-600 font-semibold hover:underline"
            >
              Reset Filters
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-3 items-center">
          {/* Exam Tabs */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleExamFilter(null)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                selectedExamId === null
                  ? 'bg-sky-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All Exams
            </button>
            {exams.map((exam) => (
              <button
                key={exam.id}
                onClick={() => handleExamFilter(exam.id)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  selectedExamId === exam.id
                    ? 'bg-sky-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {exam.name}
              </button>
            ))}
          </div>

          <div className="h-6 w-px bg-gray-200 hidden sm:block"></div>

          {/* Year Filter */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            <span className="text-xs font-semibold text-gray-500 mr-1">Year:</span>
            <button
              onClick={() => handleYearFilter(null)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                selectedYear === null
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All Years
            </button>
            {yearsList.map((yr) => (
              <button
                key={yr}
                onClick={() => handleYearFilter(yr)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  selectedYear === yr
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {yr}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Question Papers Catalog Grid */}
      {loading ? (
        <div className="py-16 text-center space-y-3">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-sky-600 border-t-transparent mx-auto"></div>
          <p className="text-xs font-semibold text-gray-500">Loading Past Year Papers...</p>
        </div>
      ) : papers.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-gray-200 space-y-3">
          <FileText className="w-12 h-12 text-gray-300 mx-auto" />
          <h3 className="text-lg font-bold text-gray-700">No Past Year Papers Found</h3>
          <p className="text-xs text-gray-500">No published papers match your selected filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {papers.map((paper) => (
            <div
              key={paper.id}
              className="bg-white rounded-2xl border border-gray-200 hover:border-sky-300 shadow-xs hover:shadow-md transition-all p-6 flex flex-col justify-between space-y-6"
            >
              <div className="space-y-4">
                {/* Badges Header */}
                <div className="flex items-center justify-between">
                  <span className="bg-sky-100 text-sky-800 text-xs font-extrabold px-3 py-1 rounded-full border border-sky-200 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" /> {paper.year} Paper
                  </span>
                  <span className="bg-slate-100 text-slate-700 text-xs font-semibold px-2.5 py-1 rounded-md">
                    {paper.exam_name}
                  </span>
                </div>

                {/* Title & Description */}
                <div>
                  <h3 className="text-lg font-bold text-gray-900 leading-snug">{paper.title}</h3>
                  {paper.description && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{paper.description}</p>
                  )}
                </div>

                {/* Paper Stats Grid */}
                <div className="grid grid-cols-2 gap-2 bg-gray-50 p-3 rounded-xl border border-gray-100 text-xs">
                  <div>
                    <span className="text-gray-400 block font-medium">Questions</span>
                    <span className="font-bold text-gray-800">{paper.question_count} Questions</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block font-medium">Duration</span>
                    <span className="font-bold text-gray-800">{paper.duration_minutes} Mins (3 Hrs)</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block font-medium">Scoring</span>
                    <span className="font-bold text-emerald-700">+{paper.marks_per_question} Marks / Q</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block font-medium">Negative Mark</span>
                    <span className="font-bold text-gray-700">{paper.negative_mark > 0 ? `-${paper.negative_mark}` : 'No Negative'}</span>
                  </div>
                </div>
              </div>

              {/* Price & Action Button */}
              <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                <div>
                  {paper.price === 0.0 ? (
                    <span className="text-emerald-600 font-extrabold text-sm flex items-center gap-1">
                      <Sparkles className="w-4 h-4" /> FREE PAPER
                    </span>
                  ) : paper.has_access ? (
                    <span className="text-emerald-600 font-extrabold text-xs flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> UNLOCKED
                    </span>
                  ) : (
                    <span className="text-lg font-black text-gray-900">₹{paper.price}</span>
                  )}
                </div>

                {paper.has_access ? (
                  <button
                    onClick={() => handleStartAttempt(paper)}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow transition-all flex items-center gap-1.5"
                  >
                    Start Exam
                  </button>
                ) : (
                  <button
                    onClick={() => handleInitiatePurchase(paper)}
                    className="bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow transition-all flex items-center gap-1.5"
                  >
                    <Lock className="w-3.5 h-3.5" /> Unlock Paper
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Mock Payment Gateway Modal */}
      {paymentModalOpen && purchasingPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 space-y-6 shadow-2xl border border-gray-100">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-sky-100 text-sky-600 rounded-2xl flex items-center justify-center mx-auto">
                <CreditCard className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-sky-600 bg-sky-50 px-3 py-1 rounded-full uppercase tracking-wider">
                DEMO / TEST PAYMENT GATEWAY
              </span>
              <h3 className="text-xl font-extrabold text-gray-900">{purchasingPaper.title}</h3>
              <p className="text-xs text-gray-500">
                Phase 1 Mock Gateway Test Environment. Choose test outcome below to simulate transaction callback.
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-2xl border border-gray-200 text-center space-y-1">
              <span className="text-xs text-gray-500">Total Paper Amount</span>
              <div className="text-3xl font-black text-gray-900">₹{purchasingPaper.price}</div>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => handleProcessPayment(true)}
                disabled={paymentLoading}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 rounded-xl text-sm shadow transition-all flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4" /> {paymentLoading ? 'Processing...' : 'Test Payment - SUCCESS'}
              </button>

              <button
                onClick={() => handleProcessPayment(false)}
                disabled={paymentLoading}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3.5 rounded-xl text-sm shadow transition-all"
              >
                Test Payment - FAILED
              </button>

              <button
                onClick={() => setPaymentModalOpen(false)}
                disabled={paymentLoading}
                className="w-full text-xs font-semibold text-gray-500 hover:text-gray-800 py-2"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
