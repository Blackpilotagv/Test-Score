import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import API from '../services/api';
import { CreditCard, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export const MockPayment: React.FC = () => {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get('order_id') || '';
  const testId = searchParams.get('test_id') || '';

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSimulatePayment = async (success: boolean) => {
    if (!orderId) {
      setErrorMsg('Invalid order ID.');
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await API.post('/payments/process-mock', {
        order_id: orderId,
        success: success,
      });

      if (success) {
        // Redirect to Instructions
        navigate(`/instructions/${testId}`);
      } else {
        setErrorMsg('Test Payment marked FAILED. Exam access remains locked.');
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to process payment choice.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto px-4 py-16">
      <div className="bg-white rounded-2xl border-2 border-sky-500 shadow-xl overflow-hidden">
        {/* Prominent Banner */}
        <div className="bg-gradient-to-r from-amber-500 to-amber-600 text-white px-6 py-3 text-center text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2">
          <AlertTriangle className="w-4 h-4" /> DEMO / TEST PAYMENT GATEWAY
        </div>

        <div className="p-8 space-y-6">
          <div className="text-center space-y-2">
            <div className="w-14 h-14 bg-sky-100 text-sky-700 rounded-2xl flex items-center justify-center mx-auto mb-2">
              <CreditCard className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-black text-gray-900">Simulate Payment Choice</h2>
            <p className="text-xs text-gray-500">
              Phase 1 Development Mode Gateway Abstraction (`MockPaymentService`)
            </p>
          </div>

          {/* Payment Details Summary */}
          <div className="bg-gray-50 rounded-xl p-4 space-y-2 text-sm border border-gray-200">
            <div className="flex justify-between">
              <span className="text-gray-500">Order ID:</span>
              <code className="font-mono text-xs font-bold text-gray-800">{orderId}</code>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Payment Gateway Method:</span>
              <span className="font-bold text-sky-700">MOCK (Simulator)</span>
            </div>
            <div className="flex justify-between border-t border-gray-200 pt-2 font-bold text-base">
              <span>Total Payable:</span>
              <span className="text-emerald-600">₹29.00 / Configured Price</span>
            </div>
          </div>

          {errorMsg && (
            <div className="bg-red-50 text-red-700 text-sm p-4 rounded-xl border border-red-200 flex items-center gap-2">
              <XCircle className="w-5 h-5 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Choice Buttons */}
          <div className="space-y-3 pt-2">
            <button
              onClick={() => handleSimulatePayment(true)}
              disabled={submitting}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-6 rounded-xl shadow transition-all flex items-center justify-center gap-2"
            >
              <CheckCircle2 className="w-5 h-5" />
              {submitting ? 'Processing...' : 'Test Payment - Success'}
            </button>

            <button
              onClick={() => handleSimulatePayment(false)}
              disabled={submitting}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3.5 px-6 rounded-xl shadow transition-all flex items-center justify-center gap-2"
            >
              <XCircle className="w-5 h-5" />
              {submitting ? 'Processing...' : 'Test Payment - Failed'}
            </button>
          </div>

          <p className="text-center text-xs text-gray-400">
            No real money or live credit card credentials are used in this Phase 1 environment.
          </p>
        </div>
      </div>
    </div>
  );
};
