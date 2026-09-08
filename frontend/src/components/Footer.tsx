import React from 'react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 text-gray-400 border-t border-gray-800 py-12 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded bg-sky-500 flex items-center justify-center text-white font-bold text-lg">
                TN
              </div>
              <span className="text-xl font-bold text-white tracking-tight">TNPSC Mock Assessment</span>
            </div>
            <p className="text-sm text-gray-400 max-w-md leading-relaxed">
              Prepare Smarter. Test Every Day. Daily online assessments specifically designed for TNPSC Group 1, Group 2, Group 4, and Group 4A competitive exams.
            </p>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Navigation</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/" className="hover:text-white transition-colors">Home</Link></li>
              <li><Link to="/exams" className="hover:text-white transition-colors">Exams</Link></li>
              <li><Link to="/about" className="hover:text-white transition-colors">About Platform</Link></li>
              <li><Link to="/login" className="hover:text-white transition-colors">Login</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Legal & Support</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#terms" className="hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#privacy" className="hover:text-white transition-colors">Privacy Policy</a></li>
              <li><a href="#contact" className="hover:text-white transition-colors">Contact Support</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-gray-800 text-xs text-center text-gray-500">
          <p>© {new Date().getFullYear()} TNPSC Mock Assessment Platform. All rights reserved.</p>
          <p className="mt-1">Designed for daily practice and assessment for Tamil Nadu Public Service Commission exams.</p>
        </div>
      </div>
    </footer>
  );
};
