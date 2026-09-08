import React from 'react';

interface QuestionPaletteProps {
  totalQuestions: number;
  currentIndex: number;
  savedAnswers: Record<number, string>;
  questionIds: number[];
  onSelectQuestion: (index: number) => void;
}

export const QuestionPalette: React.FC<QuestionPaletteProps> = ({
  totalQuestions,
  currentIndex,
  savedAnswers,
  questionIds,
  onSelectQuestion,
}) => {
  const answeredCount = Object.keys(savedAnswers).length;
  const unansweredCount = totalQuestions - answeredCount;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <h3 className="font-bold text-gray-900 text-base mb-3 pb-2 border-b border-gray-100 flex justify-between items-center">
        <span>Question Palette</span>
        <span className="text-xs font-semibold px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full">
          {answeredCount}/{totalQuestions} Answered
        </span>
      </h3>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2 text-xs mb-4 p-2 bg-gray-50 rounded-lg text-gray-600">
        <div className="flex items-center gap-1.5">
          <span className="w-3.5 h-3.5 rounded bg-emerald-600 inline-block"></span>
          <span>Answered ({answeredCount})</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3.5 h-3.5 rounded bg-white border border-gray-300 inline-block"></span>
          <span>Unanswered ({unansweredCount})</span>
        </div>
        <div className="flex items-center gap-1.5 col-span-2">
          <span className="w-3.5 h-3.5 rounded bg-sky-600 ring-2 ring-sky-300 inline-block"></span>
          <span>Current Active</span>
        </div>
      </div>

      {/* Grid of Question Numbers */}
      <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-5 gap-2 max-h-64 overflow-y-auto pr-1">
        {Array.from({ length: totalQuestions }).map((_, idx) => {
          const qId = questionIds[idx];
          const isAnswered = qId !== undefined && savedAnswers[qId] !== undefined && savedAnswers[qId] !== null;
          const isCurrent = idx === currentIndex;

          let btnStyle = 'bg-white text-gray-700 border-gray-300 hover:border-sky-500';
          if (isCurrent) {
            btnStyle = 'bg-sky-600 text-white font-bold ring-2 ring-sky-300 border-sky-600';
          } else if (isAnswered) {
            btnStyle = 'bg-emerald-600 text-white font-semibold border-emerald-600';
          }

          return (
            <button
              key={idx}
              onClick={() => onSelectQuestion(idx)}
              className={`w-9 h-9 rounded-lg border text-sm flex items-center justify-center transition-all shadow-sm ${btnStyle}`}
              title={`Question ${idx + 1}: ${isAnswered ? 'Answered' : 'Unanswered'}`}
            >
              {idx + 1}
            </button>
          );
        })}
      </div>
    </div>
  );
};
