import React, { useEffect, useState } from 'react';
import API from '../../services/api';
import { PastYearPaper, Exam, QuestionFull, PastYearPaperStatus } from '../../types';
import {
  Plus, Upload, FileText, Calendar, CheckCircle, Clock,
  Eye, Edit3, Trash2, ShieldCheck, Tag, AlertCircle, RefreshCw, UserCheck
} from 'lucide-react';

export const AdminPastYearPapers: React.FC = () => {
  const [papers, setPapers] = useState<PastYearPaper[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  // Modals state
  const [createModalOpen, setCreateModalOpen] = useState<boolean>(false);
  const [pdfModalOpen, setPdfModalOpen] = useState<boolean>(false);
  const [questionsModalOpen, setQuestionsModalOpen] = useState<boolean>(false);
  const [grantModalOpen, setGrantModalOpen] = useState<boolean>(false);

  const [activePaper, setActivePaper] = useState<PastYearPaper | null>(null);
  const [paperQuestions, setPaperQuestions] = useState<QuestionFull[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState<boolean>(false);

  // Create Paper Form
  const [newExamId, setNewExamId] = useState<number>(1);
  const [newYear, setNewYear] = useState<number>(2025);
  const [newTitle, setNewTitle] = useState<string>('');
  const [newDesc, setNewDesc] = useState<string>('');
  const [newDuration, setNewDuration] = useState<number>(180);
  const [newMarks, setNewMarks] = useState<number>(1.5);
  const [newNegative, setNewNegative] = useState<number>(0.0);
  const [newPrice, setNewPrice] = useState<number>(0.0);
  const [newStatus, setNewStatus] = useState<PastYearPaperStatus>('DRAFT');

  // PDF Upload Form
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [uploadingPdf, setUploadingPdf] = useState<boolean>(false);

  // Grant Access Form
  const [grantStudentIdentifier, setGrantStudentIdentifier] = useState<string>('');
  const [granting, setGranting] = useState<boolean>(false);

  // Add Question Form
  const [addQuestionOpen, setAddQuestionOpen] = useState<boolean>(false);
  const [qTextTa, setQTextTa] = useState<string>('');
  const [optATa, setOptATa] = useState<string>('');
  const [optBTa, setOptBTa] = useState<string>('');
  const [optCTa, setOptCTa] = useState<string>('');
  const [optDTa, setOptDTa] = useState<string>('');
  const [correctTa, setCorrectTa] = useState<string>('A');
  const [expTa, setExpTa] = useState<string>('');
  const [qSource, setQSource] = useState<string>('ORIGINAL');

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [examsRes, papersRes] = await Promise.all([
        API.get('/exams'),
        API.get('/admin/past-year-papers')
      ]);
      setExams(examsRes.data);
      setPapers(papersRes.data);
      if (examsRes.data.length > 0) setNewExamId(examsRes.data[0].id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFilteredPapers = async (examId?: number | null, year?: number | null, status?: string) => {
    try {
      setLoading(true);
      let url = '/admin/past-year-papers?';
      if (examId) url += `exam_id=${examId}&`;
      if (year) url += `year=${year}&`;
      if (status) url += `paper_status=${status}&`;
      const res = await API.get(url);
      setPapers(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePaper = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle) {
      alert('Please enter a paper title.');
      return;
    }
    try {
      await API.post('/admin/past-year-papers', {
        exam_id: newExamId,
        year: newYear,
        title: newTitle,
        description: newDesc,
        duration_minutes: newDuration,
        question_count: 0,
        marks_per_question: newMarks,
        negative_mark: newNegative,
        price: newPrice,
        status: newStatus
      });
      alert('Past Year Paper created successfully!');
      setCreateModalOpen(false);
      setNewTitle('');
      setNewDesc('');
      fetchFilteredPapers(selectedExamId, selectedYear, selectedStatus);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create paper.');
    }
  };

  const handleStatusChange = async (paper: PastYearPaper, targetStatus: PastYearPaperStatus) => {
    try {
      await API.put(`/admin/past-year-papers/${paper.id}`, { status: targetStatus });
      fetchFilteredPapers(selectedExamId, selectedYear, selectedStatus);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status.');
    }
  };

  const handleDeletePaper = async (paperId: number) => {
    if (!window.confirm('Are you sure you want to delete this past year paper and all its questions?')) return;
    try {
      await API.delete(`/admin/past-year-papers/${paperId}`);
      fetchFilteredPapers(selectedExamId, selectedYear, selectedStatus);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete paper.');
    }
  };

  const handleOpenPdfModal = (paper: PastYearPaper) => {
    setActivePaper(paper);
    setPdfFile(null);
    setPdfModalOpen(true);
  };

  const handleUploadPdf = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePaper || !pdfFile) return;

    try {
      setUploadingPdf(true);
      const formData = new FormData();
      formData.append('file', pdfFile);
      const res = await API.post(`/admin/past-year-papers/${activePaper.id}/upload-pdf`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(res.data.message || 'PDF questions uploaded successfully!');
      setPdfModalOpen(false);
      fetchFilteredPapers(selectedExamId, selectedYear, selectedStatus);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'PDF Upload failed.');
    } finally {
      setUploadingPdf(false);
    }
  };

  const handleOpenQuestionsModal = async (paper: PastYearPaper) => {
    setActivePaper(paper);
    setQuestionsModalOpen(true);
    fetchQuestions(paper.id);
  };

  const fetchQuestions = async (paperId: number) => {
    try {
      setLoadingQuestions(true);
      const res = await API.get(`/admin/past-year-papers/${paperId}`);
      setPaperQuestions(res.data.questions || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const handleAddQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePaper || !qTextTa) return;

    try {
      // Find max question_group_id
      const maxGrp = paperQuestions.reduce((max, q) => Math.max(max, q.question_group_id), 1000);
      const nextGrpId = maxGrp + 1;

      await API.post(`/admin/past-year-papers/${activePaper.id}/questions`, {
        question_group_id: nextGrpId,
        language: 'ta',
        question_text: qTextTa,
        option_a: optATa,
        option_b: optBTa,
        option_c: optCTa,
        option_d: optDTa,
        correct_option: correctTa,
        explanation: expTa,
        question_order: paperQuestions.length + 1,
        source: 'MANUAL',
        question_source: qSource,
        status: 'ACTIVE'
      });

      alert('Question added successfully!');
      setAddQuestionOpen(false);
      setQTextTa('');
      setOptATa('');
      setOptBTa('');
      setOptCTa('');
      setOptDTa('');
      setExpTa('');
      fetchQuestions(activePaper.id);
      fetchFilteredPapers(selectedExamId, selectedYear, selectedStatus);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add question.');
    }
  };

  const handleGrantAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePaper || !grantStudentIdentifier) return;

    try {
      setGranting(true);
      const res = await API.post(`/admin/past-year-papers/${activePaper.id}/grant-access`, {
        user_id_or_email: grantStudentIdentifier
      });
      alert(res.data.message);
      setGrantModalOpen(false);
      setGrantStudentIdentifier('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to grant access.');
    } finally {
      setGranting(false);
    }
  };

  const statusColors: Record<PastYearPaperStatus, string> = {
    DRAFT: 'bg-gray-100 text-gray-700 border-gray-300',
    REVIEW: 'bg-amber-100 text-amber-800 border-amber-300',
    PUBLISHED: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    ARCHIVED: 'bg-red-100 text-red-700 border-red-300'
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-200 shadow-xs">
        <div>
          <h1 className="text-2xl font-black text-gray-900 flex items-center gap-2">
            <FileText className="w-6 h-6 text-sky-600" /> Manage Past Year Question Papers
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Create, upload PDFs, edit questions, set scoring parameters, and publish previous 5 years' official TNPSC papers.
          </p>
        </div>

        <button
          onClick={() => setCreateModalOpen(true)}
          className="bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs sm:text-sm px-5 py-2.5 rounded-xl shadow transition-all flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> Create New Past Paper
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-gray-200 shadow-xs flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedExamId || ''}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : null;
              setSelectedExamId(val);
              fetchFilteredPapers(val, selectedYear, selectedStatus);
            }}
            className="px-3 py-2 border rounded-xl text-xs font-semibold bg-gray-50 text-gray-800"
          >
            <option value="">All Exam Categories</option>
            {exams.map((ex) => (
              <option key={ex.id} value={ex.id}>{ex.name}</option>
            ))}
          </select>

          <select
            value={selectedYear || ''}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : null;
              setSelectedYear(val);
              fetchFilteredPapers(selectedExamId, val, selectedStatus);
            }}
            className="px-3 py-2 border rounded-xl text-xs font-semibold bg-gray-50 text-gray-800"
          >
            <option value="">All Years</option>
            {[2025, 2024, 2023, 2022, 2021].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              fetchFilteredPapers(selectedExamId, selectedYear, e.target.value);
            }}
            className="px-3 py-2 border rounded-xl text-xs font-semibold bg-gray-50 text-gray-800"
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">DRAFT</option>
            <option value="REVIEW">REVIEW</option>
            <option value="PUBLISHED">PUBLISHED</option>
            <option value="ARCHIVED">ARCHIVED</option>
          </select>
        </div>

        <button
          onClick={() => fetchFilteredPapers(selectedExamId, selectedYear, selectedStatus)}
          className="text-xs font-bold text-sky-600 hover:text-sky-800 flex items-center gap-1"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh List
        </button>
      </div>

      {/* Table / Cards List */}
      {loading ? (
        <div className="py-16 text-center space-y-3">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-sky-600 border-t-transparent mx-auto"></div>
          <p className="text-xs font-semibold text-gray-500">Loading Past Year Papers...</p>
        </div>
      ) : papers.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-gray-200 space-y-3">
          <FileText className="w-12 h-12 text-gray-300 mx-auto" />
          <h3 className="text-lg font-bold text-gray-700">No Past Year Papers Found</h3>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 font-bold uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Exam & Year</th>
                  <th className="py-3.5 px-4">Paper Title</th>
                  <th className="py-3.5 px-4">Questions</th>
                  <th className="py-3.5 px-4">Scoring Rules</th>
                  <th className="py-3.5 px-4">Price</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-medium text-gray-800">
                {papers.map((paper) => (
                  <tr key={paper.id} className="hover:bg-gray-50/50">
                    <td className="py-4 px-4 whitespace-nowrap">
                      <div className="font-bold text-gray-900">{paper.exam_name}</div>
                      <span className="text-xs text-sky-700 bg-sky-50 px-2 py-0.5 rounded font-extrabold">
                        {paper.year} Paper
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="font-bold text-gray-900">{paper.title}</div>
                      <div className="text-gray-400 text-xxs font-normal line-clamp-1">{paper.description}</div>
                    </td>
                    <td className="py-4 px-4 whitespace-nowrap font-bold text-gray-800">
                      {paper.question_count} Qs ({paper.duration_minutes}m)
                    </td>
                    <td className="py-4 px-4 whitespace-nowrap">
                      <span className="text-emerald-700 font-bold">+{paper.marks_per_question}</span> /
                      <span className="text-red-600 font-bold"> -{paper.negative_mark}</span>
                    </td>
                    <td className="py-4 px-4 whitespace-nowrap font-bold text-gray-900">
                      {paper.price === 0.0 ? <span className="text-emerald-600">FREE</span> : `₹${paper.price}`}
                    </td>
                    <td className="py-4 px-4 whitespace-nowrap">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-extrabold border ${statusColors[paper.status]}`}>
                        {paper.status}
                      </span>
                    </td>
                    <td className="py-4 px-4 whitespace-nowrap text-right space-x-2">
                      {/* PDF Upload Button */}
                      <button
                        onClick={() => handleOpenPdfModal(paper)}
                        title="Upload Questions PDF"
                        className="p-1.5 bg-amber-50 text-amber-700 hover:bg-amber-100 rounded-lg border border-amber-200 transition-all"
                      >
                        <Upload className="w-4 h-4" />
                      </button>

                      {/* Manage Questions */}
                      <button
                        onClick={() => handleOpenQuestionsModal(paper)}
                        title="Manage Questions"
                        className="p-1.5 bg-sky-50 text-sky-700 hover:bg-sky-100 rounded-lg border border-sky-200 transition-all"
                      >
                        <Eye className="w-4 h-4" />
                      </button>

                      {/* Grant Access */}
                      <button
                        onClick={() => {
                          setActivePaper(paper);
                          setGrantModalOpen(true);
                        }}
                        title="Grant Access to Student"
                        className="p-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg border border-emerald-200 transition-all"
                      >
                        <UserCheck className="w-4 h-4" />
                      </button>

                      {/* Status Workflow Action */}
                      {paper.status === 'DRAFT' && (
                        <button
                          onClick={() => handleStatusChange(paper, 'PUBLISHED')}
                          className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs"
                        >
                          Publish
                        </button>
                      )}
                      {paper.status === 'PUBLISHED' && (
                        <button
                          onClick={() => handleStatusChange(paper, 'ARCHIVED')}
                          className="px-2.5 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-xs font-bold shadow-xs"
                        >
                          Archive
                        </button>
                      )}

                      <button
                        onClick={() => handleDeletePaper(paper.id)}
                        className="p-1.5 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg border border-red-200 transition-all"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Paper Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900 border-b pb-3">Create Past Year Paper</h3>
            <form onSubmit={handleCreatePaper} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Exam Category</label>
                  <select
                    value={newExamId}
                    onChange={(e) => setNewExamId(Number(e.target.value))}
                    className="w-full p-2.5 border rounded-xl text-xs bg-gray-50"
                  >
                    {exams.map((ex) => (
                      <option key={ex.id} value={ex.id}>{ex.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Year</label>
                  <select
                    value={newYear}
                    onChange={(e) => setNewYear(Number(e.target.value))}
                    className="w-full p-2.5 border rounded-xl text-xs bg-gray-50"
                  >
                    {[2025, 2024, 2023, 2022, 2021].map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-gray-700 block mb-1">Paper Title</label>
                <input
                  type="text"
                  placeholder="e.g. TNPSC Group 4 Original Question Paper 2024"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full p-2.5 border rounded-xl text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-bold text-gray-700 block mb-1">Description</label>
                <textarea
                  placeholder="Brief paper description..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full p-2.5 border rounded-xl text-xs h-20"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Duration (mins)</label>
                  <input
                    type="number"
                    value={newDuration}
                    onChange={(e) => setNewDuration(Number(e.target.value))}
                    className="w-full p-2.5 border rounded-xl text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Marks / Q</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newMarks}
                    onChange={(e) => setNewMarks(Number(e.target.value))}
                    className="w-full p-2.5 border rounded-xl text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Negative Mark</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newNegative}
                    onChange={(e) => setNewNegative(Number(e.target.value))}
                    className="w-full p-2.5 border rounded-xl text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Price (₹)</label>
                  <input
                    type="number"
                    value={newPrice}
                    onChange={(e) => setNewPrice(Number(e.target.value))}
                    className="w-full p-2.5 border rounded-xl text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Initial Status</label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value as PastYearPaperStatus)}
                    className="w-full p-2.5 border rounded-xl text-xs bg-gray-50"
                  >
                    <option value="DRAFT">DRAFT</option>
                    <option value="REVIEW">REVIEW</option>
                    <option value="PUBLISHED">PUBLISHED</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2.5 rounded-xl text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-sky-600 hover:bg-sky-700 text-white font-bold py-2.5 rounded-xl text-xs shadow"
                >
                  Create Paper
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PDF Upload Modal */}
      {pdfModalOpen && activePaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900">Upload PDF for {activePaper.title}</h3>
            <p className="text-xs text-gray-500">
              Upload official TNPSC question paper PDF. The system will extract questions and option choices into {activePaper.title} and set status to REVIEW.
            </p>
            <form onSubmit={handleUploadPdf} className="space-y-4">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                className="w-full p-2.5 border rounded-xl text-xs"
                required
              />

              <div className="flex gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setPdfModalOpen(false)}
                  disabled={uploadingPdf}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2.5 rounded-xl text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploadingPdf}
                  className="flex-1 bg-amber-600 hover:bg-amber-700 text-white font-bold py-2.5 rounded-xl text-xs shadow"
                >
                  {uploadingPdf ? 'Extracting...' : 'Upload & Process'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Grant Access Modal */}
      {grantModalOpen && activePaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900">Grant Access: {activePaper.title}</h3>
            <p className="text-xs text-gray-500">
              Enter student email or mobile number to grant free access to this past year paper.
            </p>
            <form onSubmit={handleGrantAccess} className="space-y-4">
              <input
                type="text"
                placeholder="Student Email or Mobile Number"
                value={grantStudentIdentifier}
                onChange={(e) => setGrantStudentIdentifier(e.target.value)}
                className="w-full p-2.5 border rounded-xl text-xs"
                required
              />

              <div className="flex gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setGrantModalOpen(false)}
                  disabled={granting}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2.5 rounded-xl text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={granting}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-xl text-xs shadow"
                >
                  {granting ? 'Granting...' : 'Grant Access'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manage Questions Modal / Drawer */}
      {questionsModalOpen && activePaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-6 border-b flex items-center justify-between bg-gray-50">
              <div>
                <h3 className="text-xl font-bold text-gray-900">{activePaper.title} Questions</h3>
                <p className="text-xs text-gray-500">Total Questions: {paperQuestions.length}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setAddQuestionOpen(!addQuestionOpen)}
                  className="bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow"
                >
                  {addQuestionOpen ? 'Close Form' : '+ Add Question'}
                </button>
                <button
                  onClick={() => setQuestionsModalOpen(false)}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 text-xs font-bold px-4 py-2 rounded-xl"
                >
                  Close
                </button>
              </div>
            </div>

            {/* Add Question Form Drawer */}
            {addQuestionOpen && (
              <div className="p-6 bg-sky-50/50 border-b border-sky-100 space-y-4">
                <h4 className="text-sm font-bold text-sky-900">Add Question to Paper</h4>
                <form onSubmit={handleAddQuestion} className="space-y-3">
                  <div>
                    <label className="text-xs font-semibold text-gray-700 block mb-1">Question Text</label>
                    <textarea
                      value={qTextTa}
                      onChange={(e) => setQTextTa(e.target.value)}
                      className="w-full p-2 border rounded-xl text-xs"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      placeholder="Option A"
                      value={optATa}
                      onChange={(e) => setOptATa(e.target.value)}
                      className="p-2 border rounded-xl text-xs"
                      required
                    />
                    <input
                      type="text"
                      placeholder="Option B"
                      value={optBTa}
                      onChange={(e) => setOptBTa(e.target.value)}
                      className="p-2 border rounded-xl text-xs"
                      required
                    />
                    <input
                      type="text"
                      placeholder="Option C"
                      value={optCTa}
                      onChange={(e) => setOptCTa(e.target.value)}
                      className="p-2 border rounded-xl text-xs"
                      required
                    />
                    <input
                      type="text"
                      placeholder="Option D"
                      value={optDTa}
                      onChange={(e) => setOptDTa(e.target.value)}
                      className="p-2 border rounded-xl text-xs"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-semibold text-gray-700 block mb-1">Correct Option</label>
                      <select
                        value={correctTa}
                        onChange={(e) => setCorrectTa(e.target.value)}
                        className="w-full p-2 border rounded-xl text-xs bg-white"
                      >
                        <option value="A">A</option>
                        <option value="B">B</option>
                        <option value="C">C</option>
                        <option value="D">D</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-gray-700 block mb-1">Question Source</label>
                      <select
                        value={qSource}
                        onChange={(e) => setQSource(e.target.value)}
                        className="w-full p-2 border rounded-xl text-xs bg-white"
                      >
                        <option value="ORIGINAL">ORIGINAL</option>
                        <option value="AI_GENERATED">AI_GENERATED</option>
                        <option value="AI_TRANSLATED">AI_TRANSLATED</option>
                        <option value="MANUAL">MANUAL</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-gray-700 block mb-1">Explanation</label>
                      <input
                        type="text"
                        placeholder="Explanation..."
                        value={expTa}
                        onChange={(e) => setExpTa(e.target.value)}
                        className="w-full p-2 border rounded-xl text-xs"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-5 py-2 rounded-xl shadow"
                  >
                    Save Question
                  </button>
                </form>
              </div>
            )}

            {/* Questions List */}
            <div className="p-6 overflow-y-auto flex-1 space-y-4">
              {loadingQuestions ? (
                <div className="py-8 text-center text-xs text-gray-500 font-semibold">Loading questions...</div>
              ) : paperQuestions.length === 0 ? (
                <div className="py-8 text-center text-xs text-gray-500 font-semibold">No questions added yet.</div>
              ) : (
                paperQuestions.map((q, idx) => (
                  <div key={q.id} className="p-4 rounded-xl border border-gray-200 bg-white space-y-2">
                    <div className="flex items-center justify-between text-xs font-bold">
                      <span className="text-sky-700">Q{q.question_order} (Group #{q.question_group_id} - {q.language.toUpperCase()})</span>
                      <span className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-extrabold text-xxs">
                        {q.question_source || 'ORIGINAL'}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-gray-900">{q.question_text}</p>
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-700">
                      <div>A: {q.option_a}</div>
                      <div>B: {q.option_b}</div>
                      <div>C: {q.option_c}</div>
                      <div>D: {q.option_d}</div>
                    </div>
                    <div className="text-xs font-bold text-emerald-700 pt-1">
                      Correct Answer: {q.correct_option}
                    </div>
                    {q.explanation && (
                      <p className="text-xs text-gray-500 italic">Explanation: {q.explanation}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
