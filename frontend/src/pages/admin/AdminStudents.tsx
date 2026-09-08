import React, { useEffect, useState } from 'react';
import API from '../../services/api';
import { User, Test } from '../../types';
import { Key, ShieldAlert, CheckCircle2, UserCheck, UserX } from 'lucide-react';

export const AdminStudents: React.FC = () => {
  const [students, setStudents] = useState<User[]>([]);
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showGrantModal, setShowGrantModal] = useState<boolean>(false);

  // Grant Access Form
  const [targetStudent, setTargetStudent] = useState<string>('');
  const [targetTestId, setTargetTestId] = useState<number | null>(null);
  const [granting, setGranting] = useState<boolean>(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [studentsRes, testsRes] = await Promise.all([
        API.get('/admin/students'),
        API.get('/tests'),
      ]);
      setStudents(studentsRes.data);
      setTests(testsRes.data);
      if (testsRes.data.length > 0) {
        setTargetTestId(testsRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGrantAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetStudent || !targetTestId) return;

    try {
      setGranting(true);
      const res = await API.post('/admin/grant-access', {
        user_id_or_email: targetStudent,
        test_id: targetTestId,
      });

      alert(res.data.message);
      setShowGrantModal(false);
      setTargetStudent('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to grant exam access.');
    } finally {
      setGranting(false);
    }
  };

  const handleToggleStatus = async (user: User) => {
    const newStatus = user.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE';
    if (!window.confirm(`Change status of ${user.name} to ${newStatus}?`)) return;

    try {
      await API.put(`/admin/students/${user.id}/status?status_str=${newStatus}`);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to change student status.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900">Student Account & Access Manager</h1>
          <p className="text-gray-600 mt-1">View registered students, toggle status, and manually grant test access</p>
        </div>

        <button
          onClick={() => setShowGrantModal(true)}
          className="bg-amber-600 hover:bg-amber-700 text-white font-bold text-sm px-5 py-2.5 rounded-xl shadow flex items-center gap-2"
        >
          <Key className="w-4 h-4" /> Grant Exam Access
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading student directory...</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
              <tr>
                <th className="p-4">ID</th>
                <th className="p-4">Student Name</th>
                <th className="p-4">Email</th>
                <th className="p-4">Mobile</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-800">
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-gray-50">
                  <td className="p-4 text-xs font-mono text-gray-500">{student.id}</td>
                  <td className="p-4 font-bold text-gray-900">{student.name}</td>
                  <td className="p-4 font-mono text-xs text-gray-600">{student.email}</td>
                  <td className="p-4 text-xs">{student.mobile}</td>
                  <td className="p-4">
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        student.status === 'ACTIVE'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {student.status}
                    </span>
                  </td>
                  <td className="p-4 text-right space-x-2">
                    <button
                      onClick={() => {
                        setTargetStudent(student.email);
                        setShowGrantModal(true);
                      }}
                      className="inline-flex items-center gap-1 text-xs font-bold text-amber-700 hover:text-amber-900 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200"
                    >
                      <Key className="w-3.5 h-3.5" /> Grant Test Access
                    </button>

                    <button
                      onClick={() => handleToggleStatus(student)}
                      className="inline-flex items-center gap-1 text-xs font-bold text-gray-600 hover:text-gray-900 bg-gray-100 px-3 py-1.5 rounded-lg border border-gray-200"
                    >
                      {student.status === 'ACTIVE' ? 'Disable' : 'Enable'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Grant Access Modal */}
      {showGrantModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center gap-2">
              <Key className="w-6 h-6 text-amber-600" />
              <h3 className="text-xl font-bold text-gray-900">Grant Manual Exam Access</h3>
            </div>
            <p className="text-xs text-gray-500">
              Grant test access to free pilot users, coaching institute students, or demo accounts.
            </p>

            <form onSubmit={handleGrantAccess} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Student Email or ID
                </label>
                <input
                  type="text"
                  value={targetStudent}
                  onChange={(e) => setTargetStudent(e.target.value)}
                  placeholder="e.g. student@tnpsc.com or 2"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-amber-500 text-sm outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Target Daily Test
                </label>
                <select
                  value={targetTestId || ''}
                  onChange={(e) => setTargetTestId(parseInt(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-amber-500 text-sm font-semibold outline-none"
                >
                  {tests.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.exam_name} - {t.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowGrantModal(false)}
                  className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={granting}
                  className="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-sm font-bold shadow"
                >
                  {granting ? 'Granting...' : 'Grant Access Now'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
