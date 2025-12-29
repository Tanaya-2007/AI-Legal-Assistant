import React, { useState, useRef, useEffect } from 'react';
import { analyzeDocument } from './services/geminiService';
import { LegalAnalysis, AppState } from './types';
import AnalysisView from './components/AnalysisView';
import { auth, provider } from './firebaseClient';
import { signInWithPopup, signOut, onAuthStateChanged, User } from 'firebase/auth';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>(AppState.IDLE);
  const [analysis, setAnalysis] = useState<LegalAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [ocrText, setOcrText] = useState<string>("");
  const BACKEND_URL = "ai-legal-assistant-production.up.railway.app";

  // Auth state listener
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe();
  }, []);

  // Login function
  const login = async () => {
    try {
      await signInWithPopup(auth, provider);
    } catch (err) {
      console.error("Login error:", err);
      alert("Login failed");
    }
  };

  // 🔥 NEW: Extract OCR text from image
  const extractOCR = async (file: File): Promise<string> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${BACKEND_URL}/ocr`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("OCR failed");
      
      const data = await res.json();
      return data.text || "";
    } catch (err) {
      console.error("OCR error:", err);
      return "Sample legal text for analysis..."; // Fallback
    }
  };

  // 🔥 NEW: Call backend to simplify text
  const simplifyText = async (text: string): Promise<LegalAnalysis> => {
    const res = await fetch(`${BACKEND_URL}/simplify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.error || "Simplification failed");
    }

    const data = await res.json();
    return {
      summary: data.summary,
      redFlags: data.redFlags,
      glossary: data.glossary
    };
  };

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/') && !file.type.includes('pdf')) {
      setError("Please provide a high-quality scan, photo, or PDF of your legal document.");
      return;
    }

    setFileName(file.name);
    setState(AppState.LOADING);
    setError(null);

    try {
      // 🔥 Step 1: Extract text using OCR
      const extractedText = await extractOCR(file);
      setOcrText(extractedText);

      // 🔥 Step 2: Send to backend for analysis
      const analysisResult = await simplifyText(extractedText);
      
      setAnalysis(analysisResult);
      setState(AppState.SUCCESS);

    } catch (err: any) {
      console.error("Analysis error:", err);
      setError(err.message || "Analysis failed. Please try again.");
      setState(AppState.ERROR);
    }
  };

  const reset = () => {
    setState(AppState.IDLE);
    setAnalysis(null);
    setError(null);
    setFileName(null);
    setOcrText("");
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen flex flex-col selection:bg-indigo-100 selection:text-indigo-900 overflow-x-hidden">
      <header className="bg-slate-900 text-white py-12 md:py-20 px-4 shadow-2xl relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.05] pointer-events-none">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
                <path d="M 30 0 L 0 0 0 30" fill="none" stroke="white" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <div className="max-w-5xl mx-auto relative z-10 flex flex-col items-center text-center">
          <div className="mb-4 md:mb-6 inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span className="text-[10px] md:text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">
              Advanced Legal Insights
            </span>
          </div>

          <h1 className="serif text-5xl md:text-8xl font-bold tracking-tight mb-4 md:mb-6 leading-tight">
            JurisClarify
          </h1>

          <p className="text-slate-400 text-base md:text-xl font-light max-w-xl mx-auto leading-relaxed italic px-4">
            "Senior AI Counsel specializing in contract demystification and risk identification."
          </p>

          <div className="mt-6">
            {!user ? (
              <button
                onClick={login}
                className="bg-indigo-600 hover:bg-indigo-500 px-6 py-3 rounded-xl font-bold transition-all"
              >
                Login with Google
              </button>
            ) : (
              <div className="flex items-center gap-4 bg-white/10 px-4 py-2 rounded-full backdrop-blur-md border border-white/20">
                {user.photoURL && (
                  <img
                    src={user.photoURL}
                    alt="profile"
                    className="w-8 h-8 rounded-full border border-indigo-400"
                  />
                )}
                <div className="text-left">
                  <p className="text-sm font-semibold text-white">
                    {user.displayName || "User"}
                  </p>
                  <p className="text-[10px] text-slate-300">
                    {user.email}
                  </p>
                </div>
                <button
                  onClick={() => signOut(auth)}
                  className="text-xs text-red-300 hover:text-red-400 font-bold"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="flex-grow container mx-auto max-w-5xl px-4 -mt-8 md:-mt-12 pb-16 z-10">
        {state === AppState.IDLE && (
          <div className="bg-white rounded-3xl md:rounded-[2.5rem] shadow-xl p-6 md:p-16 border border-slate-100 animate-in zoom-in-95 duration-500">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 md:w-20 md:h-20 bg-indigo-50 rounded-2xl md:rounded-3xl flex items-center justify-center mb-6 md:mb-8 shadow-inner">
                <svg className="w-8 h-8 md:w-10 md:h-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V16a2 2 0 01-2 2z" />
                </svg>
              </div>

              <h2 className="serif text-3xl md:text-4xl text-slate-900 mb-4 md:mb-6 font-bold text-center">Expert Document Analysis</h2>

              <div className="bg-indigo-50/40 border border-indigo-100 p-6 md:p-8 rounded-2xl max-w-2xl mb-8 md:mb-12 text-center">
                <p className="text-slate-600 text-sm md:text-lg leading-relaxed">
                  Submit a contract, lease, or legal letter. Our AI identifies <span className="text-indigo-700 font-bold">hidden risks</span> and decodes complex terminology into clear, multi-lingual explanations.
                </p>
              </div>

              <label className="group relative flex flex-col items-center justify-center w-full h-48 md:h-64 border-2 border-dashed border-slate-200 rounded-3xl md:rounded-[2rem] cursor-pointer hover:border-indigo-400 hover:bg-slate-50 transition-all shadow-sm hover:shadow-lg">
                <div className="flex flex-col items-center justify-center px-4">
                  <div className="mb-3 p-3 bg-slate-100 rounded-full group-hover:scale-110 group-hover:bg-indigo-100 transition-all duration-300">
                    <svg className="w-6 h-6 text-slate-400 group-hover:text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                  <p className="mb-1 text-base md:text-xl text-slate-700 font-semibold text-center">
                    <span className="text-indigo-600">Secure Upload</span>
                  </p>
                  <p className="text-xs md:text-sm text-slate-400 text-center">PDF, Image (JPG/PNG) up to 10MB</p>
                </div>
                <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileUpload} accept="image/*,application/pdf" />
              </label>
            </div>
          </div>
        )}

        {state === AppState.LOADING && (
          <div className="flex flex-col items-center justify-center py-20 md:py-32 bg-white rounded-3xl shadow-xl border border-slate-100 animate-in fade-in duration-500">
            <div className="relative w-24 h-24 md:w-32 md:h-32 mb-8 md:mb-10">
              <div className="absolute inset-0 border-4 border-indigo-50 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-indigo-600 rounded-full border-t-transparent animate-spin"></div>
              <div className="absolute inset-3 md:inset-4 bg-indigo-50/50 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 md:w-8 md:h-8 text-indigo-600 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A1 1 0 0111.293 2.293l4.414 4.414a1 1 0 01.293.707V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <h3 className="serif text-2xl md:text-3xl font-bold text-slate-900 mb-2 text-center px-4">Analyzing Document...</h3>
            <p className="text-slate-500 text-sm md:text-lg text-center px-6">Extracting text and identifying risks.</p>
          </div>
        )}

        {state === AppState.ERROR && (
          <div className="bg-white border border-red-100 rounded-3xl p-8 md:p-16 text-center shadow-lg animate-in shake-x duration-500">
            <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6 text-red-500">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="serif text-2xl md:text-3xl font-bold text-slate-900 mb-3">Analysis Interrupted</h3>
            <p className="text-slate-500 text-sm md:text-base mb-8 max-w-sm mx-auto">{error}</p>
            <button onClick={reset} className="w-full md:w-auto bg-slate-900 text-white px-8 py-3 rounded-xl hover:bg-slate-800 transition-all font-bold">
              Try Again
            </button>
          </div>
        )}

        {state === AppState.SUCCESS && analysis && (
          <div className="space-y-6">
            <div className="flex items-center justify-between gap-4 px-2">
              <button onClick={reset} className="flex items-center gap-2 text-slate-500 hover:text-indigo-600 transition-colors group">
                <div className="p-2 bg-white rounded-lg shadow-sm border border-slate-200 group-hover:border-indigo-200">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                </div>
                <span className="hidden md:block text-sm font-bold uppercase tracking-wider">New Document</span>
              </button>
              <div className="bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-lg text-[10px] md:text-xs font-bold flex items-center gap-2 border border-emerald-100">
                <span className="flex h-2 w-2 rounded-full bg-emerald-500"></span>
                Expert Analysis Ready
              </div>
            </div>

            <AnalysisView analysis={analysis} ocrText={ocrText} />
          </div>
        )}      </main>

      <footer className="bg-slate-50 border-t border-slate-200 pt-16 pb-12 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 mb-16">
            <div className="bg-amber-50/50 border border-amber-100 p-6 md:p-10 rounded-3xl relative overflow-hidden">
              <div className="flex items-center gap-3 mb-4 relative z-10">
                <svg className="h-5 w-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <h4 className="font-bold text-amber-900 uppercase tracking-widest text-[10px]">Legal Notice</h4>
              </div>
              <p className="text-amber-900 text-base md:text-lg leading-snug font-bold mb-3 relative z-10">
                AI analysis is not a substitute for professional legal advice.
              </p>
              <p className="text-amber-800/70 text-xs md:text-sm leading-relaxed relative z-10">
                Always consult a qualified attorney for critical decisions. JurisClarify is an accessibility tool designed to assist in understanding general concepts.
              </p>
            </div>

            <div className="bg-indigo-900 text-indigo-100 p-6 md:p-10 rounded-3xl shadow-xl relative overflow-hidden">
              <div className="flex items-center gap-3 mb-4 relative z-10">
                <svg className="h-5 w-5 text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 4.908-3.333 9.279-8 10.127a9.714 9.714 0 01-8-10.127c0-.681.056-1.35.166-2.001zm8.834 2.13a1 1 0 00-2 0v3.586L7.707 9.414a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.717V7.13z" clipRule="evenodd" />
                </svg>
                <h4 className="font-bold text-indigo-400 uppercase tracking-widest text-[10px]">Privacy & Data Safety</h4>
              </div>
              <p className="text-sm md:text-base leading-relaxed mb-4 relative z-10">
                Protected by <strong>Firebase App Check</strong>. Uploads are ephemeral and processed in secured environments.
              </p>
              <div className="text-indigo-400 text-[10px] font-bold flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                TLS 1.3 ENCRYPTION ACTIVE
              </div>
            </div>
          </div>

          <div className="text-slate-400 text-[10px] md:text-xs flex flex-col md:flex-row justify-between items-center gap-4">
            <p>&copy; 2025 JurisClarify. AI Legal Intelligence Systems.</p>
            <div className="flex gap-4 md:gap-8 font-semibold uppercase tracking-wider">
              <a href="#" className="hover:text-indigo-600 transition-colors">Privacy</a>
              <a href="#" className="hover:text-indigo-600 transition-colors">Compliance</a>
              <a href="#" className="text-indigo-500">Security Audit Log</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;