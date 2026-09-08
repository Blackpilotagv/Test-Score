import React, { useEffect, useState } from 'react';
import API from '../../services/api';
import { Exam, Test, QuestionSet, SchedulerCalendarDay, AuditLog } from '../../types';
import { Calendar, Clock, CheckCircle2, AlertCircle, Play, XCircle, Plus, RefreshCw, FileText, Upload, Sparkles, Shield, Trash2, ArrowLeft, ArrowRight } from 'lucide-react';

export const AdminScheduler: React.FC = () => {
  const [calendar, setCalendar] = useState<SchedulerCalendarDay[]>([]);
  const [questionSets, setQuestionSets] = useState<QuestionSet[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [tests, setTests] = useState<Test[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showLogsModal, setShowLogsModal] = useState<boolean>(false);
  
  // Form state
  const [formData, setFormData] = useState({
    exam_id: 0,
    test_id: 0,
    title: '',
    schedule_date: '',
    status: 'SCHEDULED'
  });

  const getTodayISTString = (): string => {
    const now = new Date();
    // Convert to IST date YYYY-MM-DD
    const istOffset = 5.5 * 60 * 60 * 1000;
    const istTime = new Date(now.getTime() + (now.getTimezoneOffset() * 60000) + istOffset);
    return istTime.toISOString().split('T')[0];
  };

  const todayStr = getTodayISTString();

  const fetchSchedulerData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const [calRes, setsRes, examsRes, testsRes, logsRes] = await Promise.all([
        API.get('/admin/question-sets/calendar'),
        API.get('/admin/question-sets'),
        API.get('/admin/exams'),
        API.get('/admin/tests'),
        API.get('/admin/question-sets/audit-logs/recent')
      ]);


      setCalendar(calRes.data);
      setQuestionSets(setsRes.data);
      setExams(examsRes.data);
      setTests(testsRes.data);
      setAuditLogs(logsRes.data);

      if (examsRes.data.length > 0) {
        setFormData(prev => ({ ...prev, exam_id: examsRes.data[0].id }));
      }
      if (testsRes.data.length > 0) {
        setFormData(prev => ({ ...prev, test_id: testsRes.data[0].id }));
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Failed to load scheduler data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedulerData();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.exam_id || !formData.test_id || !formData.schedule_date) {
      setErrorMsg('Please select an Exam, Test, and Schedule Date.');
      return;
    }

    setActionLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const selectedTest = tests.find(t => t.id === formData.test_id);
      const title = formData.title.trim() || `${selectedTest?.title || 'Daily Test'} Set (${formData.schedule_date})`;

      await API.post('/admin/question-sets', {
        exam_id: Number(formData.exam_id),
        test_id: Number(formData.test_id),
        title,
        schedule_date: formData.schedule_date,
        status: formData.status
      });

      setSuccessMsg(`Question Set successfully scheduled for ${formData.schedule_date}.`);
      setShowCreateModal(false);
      fetchSchedulerData();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Error creating question set.');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePublishNow = async (setId: number, title: string) => {
    if (!window.confirm(`Are you sure you want to manually publish '${title}' immediately? Existing active sets will be expired.`)) {
      return;
    }

    setActionLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await API.post(`/admin/question-sets/${setId}/publish-now`);
      setSuccessMsg(`Successfully published '${title}' immediately!`);
      fetchSchedulerData();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to publish question set');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelSet = async (setId: number, title: string) => {
    if (!window.confirm(`Are you sure you want to cancel '${title}'?`)) return;

    setActionLoading(true);
    setErrorMsg(null);
    try {
      await API.post(`/admin/question-sets/${setId}/cancel`);
      setSuccessMsg(`Cancelled '${title}'.`);
      fetchSchedulerData();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to cancel question set');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteSet = async (setId: number) => {
    if (!window.confirm('Delete this question set?')) return;

    setActionLoading(true);
    try {
      await API.delete(`/admin/question-sets/${setId}`);
      setSuccessMsg('Deleted question set.');
      fetchSchedulerData();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to delete set');
    } finally {
      setActionLoading(false);
    }
  };

  // Metrics
  const activeSetsCount = questionSets.filter(s => s.status === 'ACTIVE').length;
  const scheduledSetsCount = questionSets.filter(s => s.status === 'SCHEDULED').length;
  const expiredSetsCount = questionSets.filter(s => s.status === 'EXPIRED').length;
  const draftSetsCount = questionSets.filter(s => s.status === 'DRAFT').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-amber-900 via-amber-800 to-amber-950 text-white rounded-2xl p-8 shadow-xl flex flex-wrap items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold px-3 py-1 bg-amber-500/30 text-amber-200 rounded-full border border-amber-400/40 uppercase tracking-widest">
              Daily Automation Engine
            </span>
            <span className="text-xs font-medium px-2.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full border border-emerald-500/30">
              12:00 PM IST Cron Active
            </span>
          </div>
          <h1 className="text-3xl font-extrabold mt-3 tracking-tight">7-Day Rolling Daily Question Scheduler</h1>
          <p className="text-amber-100 text-sm mt-1 max-w-2xl">
            Prepare and schedule daily question sets up to 7 days in advance. Sets automatically expire and activate every day at 12:00 PM Asia/Kolkata. Historical data is preserved indefinitely.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={fetchSchedulerData}
            className="px-4 py-2.5 bg-amber-800/80 hover:bg-amber-700 text-white text-sm font-semibold rounded-xl border border-amber-600/50 flex items-center gap-2 transition-all shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <button
            onClick={() => setShowLogsModal(true)}
            className="px-4 py-2.5 bg-amber-800/80 hover:bg-amber-700 text-white text-sm font-semibold rounded-xl border border-amber-600/50 flex items-center gap-2 transition-all shadow-sm"
          >
            <Shield className="w-4 h-4 text-amber-300" /> Audit Logs
          </button>
          <button
            onClick={() => {
              setFormData({
                exam_id: exams[0]?.id || 0,
                test_id: tests[0]?.id || 0,
                title: '',
                schedule_date: todayStr,
                status: 'SCHEDULED'
              });
              setShowCreateModal(true);
            }}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold rounded-xl shadow-lg hover:shadow-emerald-900/30 flex items-center gap-2 transition-all"
          >
            <Plus className="w-5 h-5" /> Schedule Question Set
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {errorMsg && (
        <div className="p-4 bg-rose-50 border-l-4 border-rose-600 text-rose-800 rounded-xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 border-l-4 border-emerald-600 text-emerald-800 rounded-xl flex items-center gap-3 text-sm">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-emerald-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">Today's Active</p>
            <h3 className="text-2xl font-black text-emerald-900 mt-1">{activeSetsCount} Set</h3>
            <p className="text-xs text-emerald-600 mt-0.5">Live for students now</p>
          </div>
          <div className="w-12 h-12 bg-emerald-100 rounded-2xl flex items-center justify-center text-emerald-700 font-bold">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-blue-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-blue-800 uppercase tracking-wider">Next Scheduled</p>
            <h3 className="text-2xl font-black text-blue-900 mt-1">{scheduledSetsCount} Sets</h3>
            <p className="text-xs text-blue-600 mt-0.5">Publishes at 12:00 PM IST</p>
          </div>
          <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center text-blue-700 font-bold">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-amber-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-amber-800 uppercase tracking-wider">Draft Sets</p>
            <h3 className="text-2xl font-black text-amber-900 mt-1">{draftSetsCount} Sets</h3>
            <p className="text-xs text-amber-600 mt-0.5">In preparation</p>
          </div>
          <div className="w-12 h-12 bg-amber-100 rounded-2xl flex items-center justify-center text-amber-700 font-bold">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Expired History</p>
            <h3 className="text-2xl font-black text-slate-900 mt-1">{expiredSetsCount} Sets</h3>
            <p className="text-xs text-slate-500 mt-0.5">Preserved for attempts</p>
          </div>
          <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-600 font-bold">
            <Shield className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* 7-Day Rolling Calendar View */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex flex-wrap items-center justify-between gap-4 bg-slate-50/50">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-amber-700" />
              7-Day Rolling Schedule Grid
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Maximum scheduling horizon is strictly 7 days (Asia/Kolkata).
            </p>
          </div>
          <span className="text-xs font-medium px-3 py-1 bg-amber-100 text-amber-900 rounded-full border border-amber-200">
            Today (IST): <strong className="font-bold">{todayStr}</strong>
          </span>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
            {calendar.map((day) => (
              <div
                key={day.date_str}
                className={`rounded-xl border p-4 flex flex-col justify-between transition-all ${
                  day.is_today
                    ? 'border-amber-500 bg-amber-50/40 ring-2 ring-amber-400/30'
                    : day.is_allowed
                    ? 'border-gray-200 bg-white hover:border-amber-300'
                    : 'border-gray-100 bg-gray-50 opacity-60'
                }`}
              >
                {/* Date Header */}
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold uppercase text-gray-600">{day.day_name.slice(0, 3)}</span>
                    {day.is_today && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 bg-amber-600 text-white rounded-md uppercase">
                        Today
                      </span>
                    )}
                  </div>
                  <h4 className="text-sm font-black text-gray-900 mt-1">{day.date_str}</h4>

                  {/* Scheduled Sets List for this day */}
                  <div className="mt-3 space-y-2">
                    {day.sets.length === 0 ? (
                      <div className="p-3 rounded-lg border border-dashed border-gray-200 text-center text-xs text-gray-400 font-medium">
                        No set scheduled
                      </div>
                    ) : (
                      day.sets.map((set) => (
                        <div
                          key={set.id}
                          className={`p-2.5 rounded-lg border text-xs space-y-1.5 transition-all ${
                            set.status === 'ACTIVE'
                              ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                              : set.status === 'SCHEDULED'
                              ? 'bg-blue-50 border-blue-300 text-blue-950'
                              : set.status === 'DRAFT'
                              ? 'bg-amber-50 border-amber-300 text-amber-950'
                              : set.status === 'EXPIRED'
                              ? 'bg-gray-100 border-gray-300 text-gray-700'
                              : 'bg-rose-50 border-rose-300 text-rose-950'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-1">
                            <span className="font-bold truncate text-[11px]">{set.title}</span>
                            <span
                              className={`text-[9px] font-extrabold px-1.5 py-0.5 rounded-md uppercase shrink-0 ${
                                set.status === 'ACTIVE'
                                  ? 'bg-emerald-600 text-white'
                                  : set.status === 'SCHEDULED'
                                  ? 'bg-blue-600 text-white'
                                  : set.status === 'DRAFT'
                                  ? 'bg-amber-600 text-white'
                                  : 'bg-gray-500 text-white'
                              }`}
                            >
                              {set.status}
                            </span>
                          </div>

                          <div className="text-[10px] text-gray-600 font-medium flex items-center justify-between">
                            <span>{set.question_count} Logical Qs</span>
                            <span>{set.exam_name}</span>
                          </div>

                          {/* Quick Actions */}
                          <div className="pt-1.5 flex flex-wrap gap-1 border-t border-gray-200/50">
                            {set.status === 'SCHEDULED' && (
                              <>
                                <button
                                  onClick={() => handlePublishNow(set.id, set.title)}
                                  disabled={actionLoading}
                                  className="text-[10px] px-1.5 py-0.5 bg-emerald-600 text-white rounded font-bold hover:bg-emerald-700 flex items-center gap-0.5"
                                  title="Publish immediately"
                                >
                                  <Play className="w-2.5 h-2.5 fill-white" /> Publish Now
                                </button>
                                <button
                                  onClick={() => handleCancelSet(set.id, set.title)}
                                  disabled={actionLoading}
                                  className="text-[10px] px-1.5 py-0.5 bg-rose-100 text-rose-800 rounded font-semibold hover:bg-rose-200"
                                >
                                  Cancel
                                </button>
                              </>
                            )}

                            {set.status === 'DRAFT' && (
                              <>
                                <button
                                  onClick={async () => {
                                    try {
                                      await API.post(`/admin/question-sets/${set.id}/schedule`);
                                      setSuccessMsg(`Scheduled '${set.title}'`);
                                      fetchSchedulerData();
                                    } catch (err: any) {
                                      setErrorMsg(err.response?.data?.detail || 'Schedule error');
                                    }
                                  }}
                                  className="text-[10px] px-1.5 py-0.5 bg-blue-600 text-white rounded font-bold hover:bg-blue-700"
                                >
                                  Schedule
                                </button>
                                <button
                                  onClick={() => handleDeleteSet(set.id)}
                                  className="text-[10px] px-1.5 py-0.5 bg-rose-100 text-rose-700 rounded font-semibold hover:bg-rose-200"
                                >
                                  Delete
                                </button>
                              </>
                            )}

                            {set.status === 'ACTIVE' && (
                              <span className="text-[10px] text-emerald-700 font-bold flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Active Now
                              </span>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Add set button for allowed dates */}
                {day.is_allowed && (
                  <button
                    onClick={() => {
                      setFormData({
                        exam_id: exams[0]?.id || 0,
                        test_id: tests[0]?.id || 0,
                        title: '',
                        schedule_date: day.date_str,
                        status: 'SCHEDULED'
                      });
                      setShowCreateModal(true);
                    }}
                    className="mt-3 w-full py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Set
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* All Scheduled & Active Question Sets Table */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-slate-50/50">
          <h2 className="text-lg font-bold text-gray-900">All Scheduled & Historical Question Sets</h2>
          <span className="text-xs text-gray-500 font-medium">Total Records: {questionSets.length}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-slate-100/60 text-slate-700 font-semibold border-b border-gray-200 text-xs uppercase tracking-wider">
                <th className="py-3.5 px-4">Set ID</th>
                <th className="py-3.5 px-4">Title</th>
                <th className="py-3.5 px-4">Exam & Test</th>
                <th className="py-3.5 px-4">Schedule Date (IST)</th>
                <th className="py-3.5 px-4">Logical Qs</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-800">
              {questionSets.map((qs) => (
                <tr key={qs.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs font-bold text-gray-500">#{qs.id}</td>
                  <td className="py-3.5 px-4 font-bold text-gray-900">{qs.title}</td>
                  <td className="py-3.5 px-4 text-xs">
                    <span className="font-semibold text-amber-900">{qs.exam_name}</span>
                    <br />
                    <span className="text-gray-500">{qs.test_title}</span>
                  </td>
                  <td className="py-3.5 px-4 font-medium text-xs text-gray-700">{qs.schedule_date} (12:00 PM)</td>
                  <td className="py-3.5 px-4 font-bold text-xs">{qs.question_count} Qs</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`text-xs font-bold px-2.5 py-1 rounded-full uppercase ${
                        qs.status === 'ACTIVE'
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : qs.status === 'SCHEDULED'
                          ? 'bg-blue-100 text-blue-800 border border-blue-300'
                          : qs.status === 'DRAFT'
                          ? 'bg-amber-100 text-amber-800 border border-amber-300'
                          : qs.status === 'EXPIRED'
                          ? 'bg-gray-100 text-gray-700 border border-gray-300'
                          : 'bg-rose-100 text-rose-800 border border-rose-300'
                      }`}
                    >
                      {qs.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right space-x-2">
                    {qs.status === 'SCHEDULED' && (
                      <button
                        onClick={() => handlePublishNow(qs.id, qs.title)}
                        className="px-2.5 py-1 bg-emerald-600 text-white rounded text-xs font-bold hover:bg-emerald-700"
                      >
                        Publish Now
                      </button>
                    )}
                    {qs.status === 'DRAFT' && (
                      <button
                        onClick={async () => {
                          try {
                            await API.post(`/admin/question-sets/${qs.id}/schedule`);
                            setSuccessMsg(`Scheduled '${qs.title}'`);
                            fetchSchedulerData();
                          } catch (err: any) {
                            setErrorMsg(err.response?.data?.detail || 'Schedule failed');
                          }
                        }}
                        className="px-2.5 py-1 bg-blue-600 text-white rounded text-xs font-bold hover:bg-blue-700"
                      >
                        Schedule
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create & Schedule Question Set Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b pb-4">
              <h3 className="text-xl font-bold text-gray-900">Schedule Question Set</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600">
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Select Exam Category</label>
                <select
                  value={formData.exam_id}
                  onChange={(e) => {
                    const exId = Number(e.target.value);
                    const filteredTests = tests.filter(t => t.exam_id === exId);
                    setFormData(prev => ({
                      ...prev,
                      exam_id: exId,
                      test_id: filteredTests[0]?.id || prev.test_id
                    }));
                  }}
                  className="w-full border border-gray-300 rounded-xl p-3 text-sm focus:ring-2 focus:ring-amber-500 font-medium"
                >
                  {exams.map(e => (
                    <option key={e.id} value={e.id}>{e.name} ({e.language_mode})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Select Daily Test</label>
                <select
                  value={formData.test_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, test_id: Number(e.target.value) }))}
                  className="w-full border border-gray-300 rounded-xl p-3 text-sm focus:ring-2 focus:ring-amber-500 font-medium"
                >
                  {tests.filter(t => t.exam_id === formData.exam_id).map(t => (
                    <option key={t.id} value={t.id}>{t.title} ({t.question_count} Qs)</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Question Set Title</label>
                <input
                  type="text"
                  placeholder="e.g. Group 4 Daily Assessment #24 Set"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full border border-gray-300 rounded-xl p-3 text-sm focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">
                  Schedule Date (Asia/Kolkata IST)
                </label>
                <input
                  type="date"
                  min={todayStr}
                  value={formData.schedule_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, schedule_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-xl p-3 text-sm focus:ring-2 focus:ring-amber-500 font-bold"
                  required
                />
                <p className="text-[11px] text-amber-700 mt-1 font-medium">
                  Automated activation will occur at 12:00 PM IST on this date. Max 7-day horizon.
                </p>
              </div>

              <div className="pt-4 border-t flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-6 py-2.5 bg-amber-700 hover:bg-amber-800 text-white font-bold text-sm rounded-xl shadow-md"
                >
                  {actionLoading ? 'Scheduling...' : 'Save & Schedule Set'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Audit Logs Modal */}
      {showLogsModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b pb-4 shrink-0">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Shield className="w-5 h-5 text-amber-700" /> Audit & Transition History
              </h3>
              <button onClick={() => setShowLogsModal(false)} className="text-gray-400 hover:text-gray-600">
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <div className="overflow-y-auto space-y-3 pr-2">
              {auditLogs.map((log) => (
                <div key={log.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-800">
                    <span className="text-amber-800 uppercase tracking-wider">{log.action}</span>
                    <span className="text-slate-400 font-mono text-[10px]">{new Date(log.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-gray-600 font-medium">{log.details}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
