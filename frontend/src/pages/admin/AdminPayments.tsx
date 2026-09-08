import React, { useEffect, useState } from 'react';
import API from '../../services/api';
import { Payment } from '../../types';
import { CreditCard, CheckCircle2, XCircle, Clock, ShieldCheck } from 'lucide-react';

export const AdminPayments: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    API.get('/admin/payments')
      .then((res) => setPayments(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-gray-900">Payment Audit Logs</h1>
        <p className="text-gray-600 mt-1">Audit log of all test order payments, mock simulations, and manual admin access grants</p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading payment audit log...</div>
        ) : payments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No payment transaction records found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                <tr>
                  <th className="p-4">ID</th>
                  <th className="p-4">Student Name / Email</th>
                  <th className="p-4">Test Title</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Order ID</th>
                  <th className="p-4">Payment Method</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Created Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-800">
                {payments.map((p) => {
                  let statusBadge = (
                    <span className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-bold">
                      {p.status}
                    </span>
                  );
                  if (p.status === 'SUCCESS') {
                    statusBadge = (
                      <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-bold flex items-center gap-1 w-max">
                        <CheckCircle2 className="w-3.5 h-3.5" /> SUCCESS
                      </span>
                    );
                  } else if (p.status === 'FAILED') {
                    statusBadge = (
                      <span className="px-2.5 py-1 bg-red-100 text-red-800 rounded-full text-xs font-bold flex items-center gap-1 w-max">
                        <XCircle className="w-3.5 h-3.5" /> FAILED
                      </span>
                    );
                  }

                  return (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="p-4 text-xs font-mono text-gray-500">{p.id}</td>
                      <td className="p-4">
                        <strong className="block text-gray-900">{p.user_name || 'Student'}</strong>
                        <span className="text-xs text-gray-500 font-mono">{p.user_email}</span>
                      </td>
                      <td className="p-4 font-semibold text-gray-900">{p.test_title}</td>
                      <td className="p-4 font-bold text-emerald-700">₹{p.amount}</td>
                      <td className="p-4 text-xs font-mono text-gray-600">{p.gateway_order_id || 'N/A'}</td>
                      <td className="p-4">
                        <span className="px-2.5 py-1 bg-sky-50 text-sky-700 border border-sky-200 rounded-lg text-xs font-bold">
                          {p.payment_method}
                        </span>
                      </td>
                      <td className="p-4">{statusBadge}</td>
                      <td className="p-4 text-xs text-gray-500">
                        {new Date(p.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
