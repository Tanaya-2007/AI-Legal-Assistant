import React from 'react';
import { LegalAnalysis } from '../types';

interface AnalysisViewProps {
  analysis: LegalAnalysis;
  ocrText?: string;
}

const AnalysisView: React.FC<AnalysisViewProps> = ({ analysis }) => {
  return (
    <div className="space-y-6 md:space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <section className="bg-white p-6 md:p-12 rounded-3xl shadow-sm border border-slate-100 relative overflow-hidden mb-6 md:mb-10">
        <div className="absolute -top-12 -right-12 w-32 h-32 bg-indigo-50 rounded-full opacity-40"></div>
        <h2 className="serif text-2xl md:text-4xl mb-6 text-slate-900 font-bold">
          Executive Summary
        </h2>
        <div className="relative">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600 rounded-full"></div>
          <p className="text-base md:text-xl leading-relaxed text-slate-700 font-light pl-6 md:pl-10">
            {analysis.summary}
          </p>
        </div>
      </section>

      <section className="mb-6 md:mb-10">
        <div className="flex items-center gap-3 mb-6 md:mb-8 px-2">
          <h2 className="serif text-xl md:text-3xl text-slate-900 font-bold whitespace-nowrap">
            Risk Assessment
          </h2>
          <div className="h-px bg-slate-200 w-full"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-8">
          {analysis.redFlags.map((flag, idx) => (
            <div
              key={idx}
              className="bg-rose-50/50 p-6 md:p-8 rounded-3xl border border-rose-100/50 flex flex-col items-start hover:shadow-md transition-all"
            >
              <span className="text-[10px] font-black text-rose-500 uppercase tracking-[0.2em] mb-4">
                Risk Factor {idx + 1}
              </span>
              <p className="text-rose-950 font-semibold text-sm md:text-base leading-snug">
                {flag}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-slate-900 text-white p-6 md:p-12 rounded-3xl md:rounded-[2.5rem] shadow-2xl relative overflow-hidden">
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl"></div>
        <h2 className="serif text-2xl md:text-4xl mb-8 md:mb-12 font-bold text-indigo-300">
          Decoded Terminology
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-12 gap-y-8 md:gap-y-12">
          {analysis.glossary.map((item, idx) => (
            <div key={idx} className="border-l border-slate-700/50 pl-6 group">
              <h3 className="font-bold text-white text-xs md:text-sm tracking-widest uppercase mb-2 group-hover:text-indigo-400 transition-colors">
                {item.term}
              </h3>
              <p className="text-slate-400 text-sm md:text-base leading-relaxed font-light">
                {item.definition}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default AnalysisView;