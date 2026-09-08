import React, { useEffect, useState } from 'react';
import API from '../../services/api';
import { Exam, Test } from '../../types';
import { Plus, Edit, Trash2, CheckCircle2, FileText } from 'lucide-react';

export const AdminTests: React.FC = () => {
  const [tests, setTests] = useState<Test[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // Form State
  const [examId, setExamId] = useState<number>(1);
  const [title, setTitle] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [duration, setDuration] = useState<number>(30);
  const [price, setPrice] = useState<number>(29.0);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [testsRes, examsRes] = await Promise.all([
        API.get('/tests'),
        API.get('/exams'),
      ]);
      setTests(testsRes.data);
      setExams(examsRes.data);
      if (examsRes.data.length > 0) {
        setExamId(examsRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await API.post('/admin/tests', {
        exam_id: examId,
        title,
        description,
        duration_minutes: duration,
        price: price,
        question_count: 0,
        status: 'PUBLISHED',
      });
      alert('Daily test created successfully!');
      setShowCreateModal(false);
      setTitle('');
      setDescription('');
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create daily test.');
    }
  };

  const handleDeleteTest = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this test?')) return;
    try {
      await API.delete(`/admin/tests/${id}`);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete test.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900">Daily Assessment Manager</h1>
          <p className="text-gray-600 mt-1">Create, publish, and manage daily test sets for TNPSC aspirants</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-sky-600 hover:bg-sky-700 text-white font-bold text-sm px-5 py-2.5 rounded-xl shadow flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> Create Daily Test
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading daily tests...</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
              <tr>
                <th className="p-4">ID</th>
                <th className="p-4">Exam Category</th>
                <th className="p-4">Test Title</th>
                <th className="p-4">Duration</th>
                <th className="p-4">Questions</th>
                <th className="p-4">Price</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-800">
              {tests.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="p-4 text-xs font-mono text-gray-500">{t.id}</td>
                  <td className="p-4 font-bold text-sky-700">{t.exam_name}</td>
                  <td className="p-4 font-semibold text-gray-900">{t.title}</td>
                  <td className="p-4">{t.duration_minutes} Mins</td>
                  <td className="p-4">{t.question_count} MCQs</td>
                  <td className="p-4 font-bold">₹{t.price}</td>
                  <td className="p-4">
                    <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-bold">
                      {t.status}
                    </span>
                  </td>
                  <td className="p-4 text-right space-x-2">
                    <button
                      onClick={() => handleDeleteTest(t.id)}
                      className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete test"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900">Create New Daily Assessment</h3>
            <form onSubmit={handleCreateTest} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Exam Category
                </label>
                <select
                  value={examId}
                  onChange={(e) => setExamId(parseInt(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm outline-none"
                >
                  {exams.map((e) => (
                    <option key={e.id} value={e.id}>{e.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Test Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Daily Assessment #25"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Test overview..."
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Duration (Mins)
                  </label>
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(parseInt(e.target.value))}
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Price (₹)
                  </label>
                  <input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(parseFloat(e.target.value))}
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-sky-600 text-white text-sm font-bold shadow"
                >
                  Create & Publish
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
