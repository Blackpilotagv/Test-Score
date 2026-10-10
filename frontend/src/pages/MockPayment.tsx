import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import API from '../services/api';
import { CreditCard, CheckCircle2, XCircle, AlertTriangle, ShieldCheck } from 'lucide-react';

export const MockPayment: React.FC = () => {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get('order_id') || '';
  const testId = searchParams.get('test_id') || '';
  const paperId = searchParams.get('paper_id') || '';

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleRazorpayCheckout = () => {
    if (!orderId) {
      setErrorMsg('Invalid order ID.');
      return;
    }

    const RazorpayScript = (window as any).Razorpay;
    if (!RazorpayScript) {
      setErrorMsg('Razorpay SDK failed to load. Please use test simulator buttons below.');
      return;
    }

    const options = {
      key: 'rzp_test_ThzMooUJxyWnfm',
      amount: 2900,
      currency: 'INR',
      name: 'Test-Score by MZAB Arcane',
      description: 'TNPSC Exam Access Order',
      order_id: orderId.startsWith('order_') ? orderId : undefined,
      handler: async function (response: any) {
        try {
          setSubmitting(true);
          setErrorMsg(null);
          await API.post('/payments/verify-razorpay', {
            razorpay_order_id: response.razorpay_order_id || orderId,
            razorpay_payment_id: response.razorpay_payment_id || 'pay_rzp_test_success',
            razorpay_signature: response.razorpay_signature || 'test_sig',
            order_id: orderId
          });
          setSuccessMsg('Razorpay Payment Verified! Access Unlocked.');
          setTimeout(() => {
            if (paperId) {
              navigate('/past-year-papers');
            } else {
              navigate(`/instructions/${testId}`);
            }
          }, 1000);
        } catch (err: any) {
          setErrorMsg(err.response?.data?.detail || 'Razorpay payment verification failed.');
        } finally {
          setSubmitting(false);
        }
      },
      modal: {
        ondismiss: function () {
          setErrorMsg('Razorpay payment modal dismissed. Payment marked FAILED.');
          handleSimulatePayment(false);
        }
      },
      theme: { color: '#0284c7' }
    };

    try {
      const rzp = new RazorpayScript(options);
      rzp.on('payment.failed', function (resp: any) {
        setErrorMsg(`Payment Failed: ${resp.error?.description || 'Transaction declined'}`);
        handleSimulatePayment(false);
      });
      rzp.open();
    } catch (e: any) {
      console.error(e);
      setErrorMsg('Could not open Razorpay checkout popup. Please use test simulation buttons.');
    }
  };

  const handleSimulatePayment = async (success: boolean) => {
    if (!orderId) {
      setErrorMsg('Invalid order ID.');
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      setSuccessMsg(null);
      await API.post('/payments/process-mock', {
        order_id: orderId,
        success: success,
      });

      if (success) {
        setSuccessMsg('Test Payment SUCCESS! Access Unlocked.');
        setTimeout(() => {
          if (paperId) {
            navigate('/past-year-papers');
          } else {
            navigate(`/instructions/${testId}`);
          }
        }, 1000);
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
        {/* Banner */}
        <div className="bg-gradient-to-r from-sky-700 to-indigo-900 text-white px-6 py-3 text-center text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2">
          <ShieldCheck className="w-4 h-4" /> RAZORPAY TEST PAYMENT PORTAL
        </div>

        <div className="p-8 space-y-6">
          <div className="text-center space-y-2">
            <div className="w-14 h-14 bg-sky-100 text-sky-700 rounded-2xl flex items-center justify-center mx-auto mb-2">
              <CreditCard className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-black text-gray-900">Razorpay Payment Portal</h2>
            <p className="text-xs text-gray-500">
              Live Test Credentials Integrated: <code className="bg-gray-100 px-1 py-0.5 rounded text-sky-700 font-mono">rzp_test_ThzMooUJxyWnfm</code>
            </p>
          </div>

          {/* Payment Details Summary */}
          <div className="bg-gray-50 rounded-xl p-4 space-y-2 text-sm border border-gray-200">
            <div className="flex justify-between">
              <span className="text-gray-500">Order Reference:</span>
              <code className="font-mono text-xs font-bold text-gray-800">{orderId}</code>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Payment Gateway:</span>
              <span className="font-bold text-sky-700">Razorpay (Test Mode)</span>
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

          {successMsg && (
            <div className="bg-emerald-50 text-emerald-800 text-sm p-4 rounded-xl border border-emerald-200 flex items-center gap-2 font-semibold">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Buttons */}
          <div className="space-y-3 pt-2">
            <button
              onClick={handleRazorpayCheckout}
              disabled={submitting}
              className="w-full bg-sky-600 hover:bg-sky-700 text-white font-extrabold py-3.5 px-6 rounded-xl shadow transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <CreditCard className="w-5 h-5" />
              {submitting ? 'Verifying...' : 'Pay with Razorpay Popup (Test Key)'}
            </button>

            <div className="relative flex py-1 items-center">
              <div className="flex-grow border-t border-gray-200"></div>
              <span className="flex-shrink mx-3 text-xs text-gray-400 font-semibold uppercase">Or Instant Test Simulation</span>
              <div className="flex-grow border-t border-gray-200"></div>
            </div>

            <button
              onClick={() => handleSimulatePayment(true)}
              disabled={submitting}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 rounded-xl shadow transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <CheckCircle2 className="w-5 h-5" />
              {submitting ? 'Processing...' : 'Test Payment - Success (Instant Unlock)'}
            </button>

            <button
              onClick={() => handleSimulatePayment(false)}
              disabled={submitting}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-xl shadow transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <XCircle className="w-5 h-5" />
              {submitting ? 'Processing...' : 'Test Payment - Failed (Keep Locked)'}
            </button>
          </div>

          <p className="text-center text-xs text-gray-400">
            Official Razorpay Test Credentials (rzp_test_ThzMooUJxyWnfm). Supports test success and test failure simulation.
          </p>
        </div>
      </div>
    </div>
  );
};
