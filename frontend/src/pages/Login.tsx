import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import API from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Lock, Mail, Phone, LogIn, AlertCircle } from 'lucide-react';

export const Login: React.FC = () => {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setErrorMsg('Please enter email/mobile and password.');
      return;
    }

    try {
      setLoading(true);
      setErrorMsg(null);

      const res = await API.post('/auth/login', { username, password });
      const { access_token, user_id, role, name } = res.data;

      const userObj = {
        id: user_id,
        name: name,
        email: username.includes('@') ? username : '',
        mobile: !username.includes('@') ? username : '',
        role: role,
        status: 'ACTIVE' as const,
        created_at: new Date().toISOString(),
      };

      login(access_token, userObj);

      if (role === 'ADMIN') {
        navigate('/admin');
      } else {
        navigate(from, { replace: true });
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Invalid email/mobile or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-lg p-8 space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-sky-100 text-sky-700 rounded-2xl flex items-center justify-center mx-auto">
            <LogIn className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black text-gray-900">Student & Admin Login</h1>
          <p className="text-xs text-gray-500">Sign in to access your TNPSC mock test portal</p>
        </div>

        {errorMsg && (
          <div className="bg-red-50 text-red-700 text-sm p-4 rounded-xl border border-red-200 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
              Email or Mobile Number
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. student@tnpsc.com or 9876543211"
              required
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 text-sm outline-none transition-all"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Password
              </label>
              <a href="#forgot" onClick={(e) => { e.preventDefault(); alert("Password reset link will be sent to registered mobile/email."); }} className="text-xs text-sky-600 hover:underline">
                Forgot password?
              </a>
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 text-sm outline-none transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-3.5 px-4 rounded-xl shadow transition-all flex items-center justify-center gap-2"
          >
            {loading ? 'Authenticating...' : 'Login'}
          </button>
        </form>

        {/* Demo Credentials Info box */}
        <div className="bg-sky-50 p-4 rounded-xl border border-sky-100 text-xs text-sky-900 space-y-1">
          <strong className="block font-bold">Demo Login Accounts:</strong>
          <p>🎓 Student: <code>student@tnpsc.com</code> / <code>student123</code></p>
          <p>🛡️ Admin: <code>admin@tnpsc.com</code> / <code>admin123</code></p>
        </div>

        <div className="text-center text-xs text-gray-600 pt-2 border-t border-gray-100">
          Don't have an account?{' '}
          <Link to="/register" className="font-bold text-sky-600 hover:underline">
            Register here
          </Link>
        </div>
      </div>
    </div>
  );
};
