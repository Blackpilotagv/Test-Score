import React, { useEffect, useState } from 'react';
import API from '../../services/api';
import { Exam } from '../../types';
import { BookOpen, Edit, Plus, CheckCircle2, AlertCircle } from 'lucide-react';

export const AdminExams: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [priceInput, setPriceInput] = useState<string>('');
  const [descInput, setDescInput] = useState<string>('');

  useEffect(() => {
    fetchExams();
  }, []);

  const fetchExams = () => {
    setLoading(true);
    API.get('/exams')
      .then((res) => setExams(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  const handleEditClick = (exam: Exam) => {
    setEditingExam(exam);
    setPriceInput(exam.price.toString());
    setDescInput(exam.description || '');
  };

  const handleSaveExam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingExam) return;

    try {
      await API.put(`/admin/exams/${editingExam.id}`, {
        price: parseFloat(priceInput),
        description: descInput,
      });
      alert(`Successfully updated price for ${editingExam.name}!`);
      setEditingExam(null);
      fetchExams();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update exam category');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900">Admin Exam Management</h1>
          <p className="text-gray-600 mt-1">Configure pricing, descriptions, and status for TNPSC exam categories</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading exam categories...</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
              <tr>
                <th className="p-4">ID</th>
                <th className="p-4">Exam Category</th>
                <th className="p-4">Slug</th>
                <th className="p-4">Configured Price</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-800">
              {exams.map((exam) => (
                <tr key={exam.id} className="hover:bg-gray-50">
                  <td className="p-4 text-xs font-mono text-gray-500">{exam.id}</td>
                  <td className="p-4 font-bold text-gray-900">{exam.name}</td>
                  <td className="p-4 text-xs font-mono text-gray-600">{exam.slug}</td>
                  <td className="p-4 font-bold text-sky-700">₹{exam.price}</td>
                  <td className="p-4">
                    <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-bold">
                      {exam.status}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => handleEditClick(exam)}
                      className="inline-flex items-center gap-1 text-xs font-bold text-sky-600 hover:text-sky-800 bg-sky-50 px-3 py-1.5 rounded-lg border border-sky-200"
                    >
                      <Edit className="w-3.5 h-3.5" /> Edit Price
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Edit Modal */}
      {editingExam && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900">Edit {editingExam.name}</h3>
            <form onSubmit={handleSaveExam} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Price (₹)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={priceInput}
                  onChange={(e) => setPriceInput(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={descInput}
                  onChange={(e) => setDescInput(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 text-sm outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingExam(null)}
                  className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-sky-600 text-white text-sm font-bold shadow"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
