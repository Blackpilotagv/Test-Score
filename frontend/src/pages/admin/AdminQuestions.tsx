import React, { useEffect, useState } from 'react';
import API from '../../services/api';
import { Test, QuestionFull } from '../../types';
import { Plus, Trash2, Globe, CheckCircle2, Upload, FileText, Check } from 'lucide-react';

export const AdminQuestions: React.FC = () => {
  const [tests, setTests] = useState<Test[]>([]);
  const [selectedTestId, setSelectedTestId] = useState<number | null>(null);
  const [selectedTest, setSelectedTest] = useState<Test | null>(null);
  const [questions, setQuestions] = useState<QuestionFull[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modals
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [showPdfModal, setShowPdfModal] = useState<boolean>(false);

  // Form State - Single Language (Group 1 & 4)
  const [qText, setQText] = useState<string>('');
  const [optA, setOptA] = useState<string>('');
  const [optB, setOptB] = useState<string>('');
  const [optC, setOptC] = useState<string>('');
  const [optD, setOptD] = useState<string>('');
  const [correctOpt, setCorrectOpt] = useState<string>('A');
  const [explanation, setExplanation] = useState<string>('');

  // Form State - Dual Language (Group 2)
  const [qTextEn, setQTextEn] = useState<string>('');
  const [optAEn, setOptAEn] = useState<string>('');
  const [optBEn, setOptBEn] = useState<string>('');
  const [optCEn, setOptCEn] = useState<string>('');
  const [optDEn, setOptDEn] = useState<string>('');
  const [correctOptEn, setCorrectOptEn] = useState<string>('A');
  const [explanationEn, setExplanationEn] = useState<string>('');

  // PDF Upload State
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [uploadingPdf, setUploadingPdf] = useState<boolean>(false);
  const [pdfPreview, setPdfPreview] = useState<any[] | null>(null);
  const [savingBatch, setSavingBatch] = useState<boolean>(false);

  useEffect(() => {
    API.get('/tests').then((res) => {
      setTests(res.data);
      if (res.data.length > 0) {
        setSelectedTestId(res.data[0].id);
        setSelectedTest(res.data[0]);
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedTestId) return;
    const t = tests.find((x) => x.id === selectedTestId);
    if (t) setSelectedTest(t);
    fetchQuestions(selectedTestId);
  }, [selectedTestId, tests]);

  const fetchQuestions = (tId: number) => {
    setLoading(true);
    API.get(`/admin/tests/${tId}/questions`)
      .then((res) => setQuestions(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  const isGroup2 = selectedTest?.exam_slug === 'tnpsc-group-2';

  const handleCreateSingleQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTestId) return;

    try {
      await API.post('/admin/questions', {
        test_id: selectedTestId,
        question_group_id: 0,
        language: 'ta',
        question_text: qText,
        option_a: optA,
        option_b: optB,
        option_c: optC,
        option_d: optD,
        correct_option: correctOpt,
        explanation: explanation,
        question_order: questions.length + 1,
        source: 'MANUAL',
        status: 'ACTIVE'
      });

      alert('Tamil question added successfully!');
      resetForm();
      fetchQuestions(selectedTestId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add question.');
    }
  };

  const handleCreateGroup2DualQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTestId) return;

    try {
      await API.post('/admin/questions/group2', {
        test_id: selectedTestId,
        question_order: Math.floor(questions.length / 2) + 1,
        question_text_ta: qText,
        option_a_ta: optA,
        option_b_ta: optB,
        option_c_ta: optC,
        option_d_ta: optD,
        correct_option_ta: correctOpt,
        explanation_ta: explanation,
        question_text_en: qTextEn,
        option_a_en: optAEn,
        option_b_en: optBEn,
        option_c_en: optCEn,
        option_d_en: optDEn,
        correct_option_en: correctOptEn,
        explanation_en: explanationEn,
      });

      alert('Dual Tamil + English question pair created successfully!');
      resetForm();
      fetchQuestions(selectedTestId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create Group 2 dual question.');
    }
  };

  const handleUploadPdfSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pdfFile || !selectedTestId) return;

    const formData = new FormData();
    formData.append('file', pdfFile);

    try {
      setUploadingPdf(true);
      const res = await API.post(`/admin/tests/${selectedTestId}/upload-pdf`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setPdfPreview(res.data.preview);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to parse PDF question file.');
    } finally {
      setUploadingPdf(false);
    }
  };

  const handleConfirmBatchSave = async () => {
    if (!pdfPreview || !selectedTestId) return;

    const batchPayload = pdfPreview.map((q, idx) => ({
      test_id: selectedTestId,
      question_group_id: 0,
      language: q.language,
      question_text: q.question_text,
      option_a: q.option_a,
      option_b: q.option_b,
      option_c: q.option_c,
      option_d: q.option_d,
      correct_option: q.correct_option,
      explanation: q.explanation,
      question_order: idx + 1,
      source: 'PDF',
      status: 'ACTIVE'
    }));

    try {
      setSavingBatch(true);
      await API.post('/admin/questions/batch', batchPayload);
      alert(`Successfully saved ${pdfPreview.length} questions from PDF import!`);
      setShowPdfModal(false);
      setPdfFile(null);
      setPdfPreview(null);
      fetchQuestions(selectedTestId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to batch save questions.');
    } finally {
      setSavingBatch(false);
    }
  };

  const resetForm = () => {
    setShowAddModal(false);
    setQText(''); setOptA(''); setOptB(''); setOptC(''); setOptD(''); setExplanation('');
    setQTextEn(''); setOptAEn(''); setOptBEn(''); setOptCEn(''); setOptDEn(''); setExplanationEn('');
  };

  const handleDeleteQuestion = async (qId: number) => {
    if (!window.confirm('Delete this logical question for all language representations?')) return;
    try {
      await API.delete(`/admin/questions/${qId}`);
      if (selectedTestId) fetchQuestions(selectedTestId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete question.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900">Question Bank Editor</h1>
          <p className="text-gray-600 mt-1">Manage questions via manual creation or PDF document text extraction</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedTestId || ''}
            onChange={(e) => setSelectedTestId(parseInt(e.target.value))}
            className="px-4 py-2.5 rounded-xl border border-gray-300 bg-white font-bold text-sm text-gray-800 outline-none"
          >
            {tests.map((t) => (
              <option key={t.id} value={t.id}>
                {t.exam_name} - {t.title}
              </option>
            ))}
          </select>

          <button
            onClick={() => setShowPdfModal(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm px-4 py-2.5 rounded-xl shadow flex items-center gap-2"
          >
            <Upload className="w-4 h-4" /> Upload Question PDF
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="bg-sky-600 hover:bg-sky-700 text-white font-bold text-sm px-4 py-2.5 rounded-xl shadow flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> Add Question
          </button>
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white p-8 rounded-2xl border border-gray-200 text-center text-gray-500">
            Loading questions...
          </div>
        ) : questions.length === 0 ? (
          <div className="bg-white p-8 rounded-2xl border border-gray-200 text-center text-gray-500">
            No questions added to this test yet. Click "Add Question" or "Upload Question PDF" to begin.
          </div>
        ) : (
          questions.map((q) => (
            <div key={q.id} className="bg-white rounded-xl border border-gray-200 shadow-xs p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sky-800 text-sm">Logical Q#{q.question_order}</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                    q.language === 'ta' ? 'bg-emerald-100 text-emerald-800' : 'bg-indigo-100 text-indigo-800'
                  }`}>
                    {q.language === 'ta' ? 'தமிழ்' : 'English'}
                  </span>
                  <span className="text-xs text-gray-400 font-mono">Group ID: {q.question_group_id}</span>
                  {q.source === 'PDF' && (
                    <span className="text-xs font-semibold px-2 py-0.5 bg-amber-100 text-amber-800 rounded">
                      PDF Imported
                    </span>
                  )}
                </div>
                <button
                  onClick={() => handleDeleteQuestion(q.id)}
                  className="text-red-600 hover:bg-red-50 p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1"
                >
                  <Trash2 className="w-4 h-4" /> Delete Question Group
                </button>
              </div>

              <p className="text-base font-semibold text-gray-900">{q.question_text}</p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                {[
                  { key: 'A', text: q.option_a },
                  { key: 'B', text: q.option_b },
                  { key: 'C', text: q.option_c },
                  { key: 'D', text: q.option_d },
                ].map((opt) => {
                  const isCorrect = q.correct_option?.toUpperCase() === opt.key;
                  return (
                    <div
                      key={opt.key}
                      className={`p-3 rounded-lg border flex items-center gap-2 ${
                        isCorrect
                          ? 'bg-emerald-50 border-emerald-500 text-emerald-900 font-bold'
                          : 'bg-gray-50 border-gray-200 text-gray-700'
                      }`}
                    >
                      <span className="font-bold text-xs uppercase px-1.5 py-0.5 bg-white/60 rounded border border-gray-300">
                        {opt.key}
                      </span>
                      <span>{opt.text}</span>
                      {isCorrect && <CheckCircle2 className="w-4 h-4 text-emerald-600 ml-auto" />}
                    </div>
                  );
                })}
              </div>

              {q.explanation && (
                <div className="bg-sky-50 border border-sky-200 rounded-lg p-3 text-xs text-sky-900">
                  <strong>Explanation:</strong> {q.explanation}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* PDF Upload Modal */}
      {showPdfModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Upload className="w-5 h-5 text-emerald-600" /> Upload Question PDF Document
              </h3>
              <span className="text-xs font-bold px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full">
                {selectedTest?.exam_name}
              </span>
            </div>

            {!pdfPreview ? (
              <form onSubmit={handleUploadPdfSubmit} className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center space-y-3 bg-gray-50 hover:bg-gray-100/80 transition-colors">
                  <FileText className="w-12 h-12 text-emerald-600 mx-auto" />
                  <div>
                    <label className="font-bold text-sm text-sky-700 hover:underline cursor-pointer">
                      Select Question PDF File
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setPdfFile(e.target.files ? e.target.files[0] : null)}
                        className="hidden"
                      />
                    </label>
                    <p className="text-xs text-gray-500 mt-1">
                      {pdfFile ? pdfFile.name : 'Supports structured PDF exam papers'}
                    </p>
                  </div>
                </div>

                <div className="bg-sky-50 p-4 rounded-xl border border-sky-200 text-xs text-sky-900 space-y-1">
                  <strong className="block font-bold">PDF Exam Language Rule:</strong>
                  <p>Questions will automatically be assigned the allowed language according to exam rules:</p>
                  <p>• Group 1 / Group 4 → Assigned <strong>Tamil</strong> (`language = 'ta'`)</p>
                  <p>• Group 2 → Assigned <strong>Tamil & English</strong> based on text block structure</p>
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => { setShowPdfModal(false); setPdfFile(null); }}
                    className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!pdfFile || uploadingPdf}
                    className="px-6 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold shadow"
                  >
                    {uploadingPdf ? 'Extracting & Parsing PDF...' : 'Upload & Generate Structured Questions'}
                  </button>
                </div>
              </form>
            ) : (
              /* PDF Extracted Preview Step */
              <div className="space-y-4">
                <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-200 flex justify-between items-center text-xs font-bold text-emerald-900">
                  <span>Successfully extracted {pdfPreview.length} questions from PDF.</span>
                  <span>Review structured questions below before saving:</span>
                </div>

                <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                  {pdfPreview.map((pq, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-lg border text-xs space-y-1">
                      <div className="flex justify-between font-bold text-gray-800">
                        <span>Q#{pq.question_order}: {pq.question_text}</span>
                        <span className="text-sky-700 uppercase">[{pq.language}] Key: {pq.correct_option}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-1 text-gray-600">
                        <span>A: {pq.option_a}</span>
                        <span>B: {pq.option_b}</span>
                        <span>C: {pq.option_c}</span>
                        <span>D: {pq.option_d}</span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setPdfPreview(null)}
                    className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold"
                  >
                    Re-upload PDF
                  </button>
                  <button
                    onClick={handleConfirmBatchSave}
                    disabled={savingBatch}
                    className="px-6 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold shadow flex items-center gap-1"
                  >
                    <Check className="w-4 h-4" />
                    {savingBatch ? 'Saving Questions...' : 'Confirm & Save All Questions to Test'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Manual Add Question Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-xl font-bold text-gray-900">
                Add Question to {selectedTest?.exam_name} ({selectedTest?.title})
              </h3>
              <span className="text-xs font-bold px-2.5 py-1 bg-sky-100 text-sky-800 rounded-full">
                {isGroup2 ? 'Dual Language: தமிழ் + English' : 'Tamil Medium Only'}
              </span>
            </div>

            {isGroup2 ? (
              <form onSubmit={handleCreateGroup2DualQuestion} className="space-y-6">
                <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200 space-y-3">
                  <h4 className="font-bold text-emerald-900 text-sm flex items-center gap-1">
                    <Globe className="w-4 h-4" /> 1. தமிழ் பதிப்பு (Tamil Version)
                  </h4>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">கேள்வி (Question Text)</label>
                    <textarea
                      rows={2}
                      value={qText}
                      onChange={(e) => setQText(e.target.value)}
                      required
                      placeholder="தமிழ் கேள்வி..."
                      className="w-full px-3 py-2 rounded-lg border text-xs outline-none bg-white"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={optA} onChange={(e) => setOptA(e.target.value)} required placeholder="விருப்பம் A" className="px-3 py-1.5 rounded border text-xs bg-white" />
                    <input type="text" value={optB} onChange={(e) => setOptB(e.target.value)} required placeholder="விருப்பம் B" className="px-3 py-1.5 rounded border text-xs bg-white" />
                    <input type="text" value={optC} onChange={(e) => setOptC(e.target.value)} required placeholder="விருப்பம் C" className="px-3 py-1.5 rounded border text-xs bg-white" />
                    <input type="text" value={optD} onChange={(e) => setOptD(e.target.value)} required placeholder="விருப்பம் D" className="px-3 py-1.5 rounded border text-xs bg-white" />
                  </div>
                  <div className="flex gap-4 items-center">
                    <label className="text-xs font-semibold">சரியான விடை:</label>
                    <select value={correctOpt} onChange={(e) => setCorrectOpt(e.target.value)} className="px-3 py-1 rounded border text-xs font-bold">
                      <option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option>
                    </select>
                  </div>
                  <textarea rows={1} value={explanation} onChange={(e) => setExplanation(e.target.value)} placeholder="விளக்கம்..." className="w-full px-3 py-1.5 rounded border text-xs bg-white" />
                </div>

                <div className="bg-indigo-50/60 p-4 rounded-xl border border-indigo-200 space-y-3">
                  <h4 className="font-bold text-indigo-900 text-sm flex items-center gap-1">
                    <Globe className="w-4 h-4" /> 2. English Version
                  </h4>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Question Text (English)</label>
                    <textarea
                      rows={2}
                      value={qTextEn}
                      onChange={(e) => setQTextEn(e.target.value)}
                      required
                      placeholder="English Question Text..."
                      className="w-full px-3 py-2 rounded-lg border text-xs outline-none bg-white"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={optAEn} onChange={(e) => setOptAEn(e.target.value)} required placeholder="Option A" className="px-3 py-1.5 rounded border text-xs bg-white" />
                    <input type="text" value={optBEn} onChange={(e) => setOptBEn(e.target.value)} required placeholder="Option B" className="px-3 py-1.5 rounded border text-xs bg-white" />
                    <input type="text" value={optCEn} onChange={(e) => setOptCEn(e.target.value)} required placeholder="Option C" className="px-3 py-1.5 rounded border text-xs bg-white" />
                    <input type="text" value={optDEn} onChange={(e) => setOptDEn(e.target.value)} required placeholder="Option D" className="px-3 py-1.5 rounded border text-xs bg-white" />
                  </div>
                  <div className="flex gap-4 items-center">
                    <label className="text-xs font-semibold">Correct Answer Key:</label>
                    <select value={correctOptEn} onChange={(e) => setCorrectOptEn(e.target.value)} className="px-3 py-1 rounded border text-xs font-bold">
                      <option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option>
                    </select>
                  </div>
                  <textarea rows={1} value={explanationEn} onChange={(e) => setExplanationEn(e.target.value)} placeholder="English Solution Explanation..." className="w-full px-3 py-1.5 rounded border text-xs bg-white" />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" onClick={resetForm} className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold">
                    Cancel
                  </button>
                  <button type="submit" className="px-6 py-2 rounded-xl bg-sky-600 text-white text-sm font-bold shadow">
                    Save Group 2 Question Pair
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleCreateSingleQuestion} className="space-y-4">
                <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200 space-y-3">
                  <h4 className="font-bold text-emerald-900 text-sm flex items-center gap-1">
                    <Globe className="w-4 h-4" /> தமிழ் வினா (Tamil Question Only)
                  </h4>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">கேள்வி உரை</label>
                    <textarea
                      rows={3}
                      value={qText}
                      onChange={(e) => setQText(e.target.value)}
                      required
                      placeholder="தமிழ் வினா உரை..."
                      className="w-full px-3 py-2 rounded-lg border text-xs outline-none bg-white"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={optA} onChange={(e) => setOptA(e.target.value)} required placeholder="விருப்பம் A" className="px-3 py-2 rounded border text-xs bg-white" />
                    <input type="text" value={optB} onChange={(e) => setOptB(e.target.value)} required placeholder="விருப்பம் B" className="px-3 py-2 rounded border text-xs bg-white" />
                    <input type="text" value={optC} onChange={(e) => setOptC(e.target.value)} required placeholder="விருப்பம் C" className="px-3 py-2 rounded border text-xs bg-white" />
                    <input type="text" value={optD} onChange={(e) => setOptD(e.target.value)} required placeholder="விருப்பம் D" className="px-3 py-2 rounded border text-xs bg-white" />
                  </div>
                  <div className="flex gap-4 items-center">
                    <label className="text-xs font-semibold">சரியான விடை:</label>
                    <select value={correctOpt} onChange={(e) => setCorrectOpt(e.target.value)} className="px-3 py-1.5 rounded border text-xs font-bold">
                      <option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option>
                    </select>
                  </div>
                  <textarea rows={2} value={explanation} onChange={(e) => setExplanation(e.target.value)} placeholder="விளக்கம்..." className="w-full px-3 py-2 rounded border text-xs bg-white" />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" onClick={resetForm} className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold">
                    Cancel
                  </button>
                  <button type="submit" className="px-6 py-2 rounded-xl bg-sky-600 text-white text-sm font-bold shadow">
                    Save Tamil Question
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
