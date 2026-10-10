import React from 'react';
import { BookOpen, CheckCircle, ShieldCheck, Target, Award } from 'lucide-react';

export const About: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
      <div className="text-center space-y-3">
        <span className="text-xs font-semibold px-3 py-1 bg-sky-100 text-sky-800 rounded-full">
          About Platform
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900">
          Test-Score by MZAB Arcane
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Dedicated online mock evaluation system designed for Tamil Nadu competitive exam aspirants.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-xs space-y-6 text-gray-700 leading-relaxed">
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Target className="w-5 h-5 text-sky-600" /> Platform Mission
        </h2>
        <p>
          Our platform provides daily online assessments and FREE 5-year past year question papers specifically structured for competitive exam preparation targeting <strong>TNPSC Group 1, TNPSC Group 2 & 2A, TNPSC Group 4, UPSC General Studies (GS), and UPSC CSAT</strong>.
        </p>

        <p>
          Category 1 features <strong>Daily Test Assessments</strong> (unlocked per purchase, rotating daily at 12:00 PM IST). Category 2 features <strong>FREE Past Year Papers</strong> (2021–2025) with real-time timed test engine, auto-save, instant score evaluation with negative marking penalty calculations, and detailed solutions.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-gray-100">
          <div className="bg-sky-50 p-4 rounded-xl border border-sky-100 space-y-1">
            <strong className="text-sky-900 font-bold block text-sm">Key Capabilities</strong>
            <ul className="text-xs text-sky-800 space-y-1 list-disc list-inside">
              <li>Configurable exam pricing & daily sets</li>
              <li>Real-time server-synced test timer</li>
              <li>Option auto-save during exam</li>
              <li>Instant server-side score calculation</li>
              <li>Detailed question review & explanations</li>
            </ul>
          </div>

          <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-1">
            <strong className="text-gray-900 font-bold block text-sm flex items-center gap-1">
              <ShieldCheck className="w-4 h-4 text-emerald-600" /> Student Guidelines
            </strong>
            <p className="text-xs text-gray-600">
              This platform serves as a self-assessment tool for practice. Success in competitive examinations depends on individual study effort, consistency, and comprehension. We do not claim guaranteed exam success.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
