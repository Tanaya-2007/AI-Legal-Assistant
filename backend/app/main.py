import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
import traceback

# Try to import pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except Exception as e:
    TESSERACT_AVAILABLE = False
    print(f"Tesseract not available: {e}")

# ---------------- APP ----------------
app = FastAPI(title="JurisClarify Backend", version="1.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-legal-assistant-chi.vercel.app",
        "https://ai-legal-assistant-9m722vw12-tanaya-pawars-projects.vercel.app",  # Add this!
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROOT ----------------
@app.get("/")
async def root():
    return {
        "status": "JurisClarify Backend is Live! ✅",
        "tesseract": TESSERACT_AVAILABLE,
        "version": "1.0",
        "endpoints": ["/ocr", "/simplify", "/docs"]
    }

# ---------------- HEALTH CHECK ----------------
@app.get("/health")
async def health():
    return {"status": "healthy"}

# ---------------- OCR ----------------
@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    try:
        print(f"Received file: {file.filename}, content_type: {file.content_type}")
        
        if not TESSERACT_AVAILABLE:
            return JSONResponse(
                status_code=200,
                content={"text": "OCR not available. Please paste text directly for analysis."}
            )
        
        # Read and process image
        image = Image.open(file.file).convert("RGB")
        text = pytesseract.image_to_string(image)
        
        print(f"Extracted text length: {len(text)}")
        return {"text": text}
        
    except Exception as e:
        error_msg = str(e)
        print(f"OCR Error: {error_msg}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"OCR processing failed: {error_msg}"}
        )

# ---------------- DATA MODEL ----------------
class LegalText(BaseModel):
    text: str

# ---------------- SIMPLIFY ----------------
@app.post("/simplify")
async def simplify_legal_text(data: LegalText):
    try:
        print(f"Received text for analysis, length: {len(data.text)}")
        
        text = data.text.strip()[:3000]  # Limit to 3000 chars

        if not text:
            return JSONResponse(
                status_code=400,
                content={"error": "No text provided for analysis"}
            )

        word_count = len(text.split())
        
        # Generate summary
        summary = f"This document contains approximately {word_count} words covering legal terms and obligations between parties. It outlines rights, responsibilities, and potential consequences."

        # Risk detection
        risks = []
        risk_keywords = {
            "termination": "⚠️ HIGH RISK: Termination clauses present. Review exit conditions and penalties carefully.",
            "terminate": "⚠️ HIGH RISK: Agreement can be terminated under certain conditions. Understand the terms.",
            "liability": "🚨 CRITICAL: Liability clauses found. You may be financially responsible for damages or losses.",
            "liable": "🚨 CRITICAL: You could be held liable. Understand your potential exposure.",
            "indemnify": "⚠️ HIGH RISK: You may need to compensate the other party for certain claims or losses.",
            "indemnification": "⚠️ HIGH RISK: Indemnity obligations exist. Could result in financial responsibility.",
            "breach": "⚠️ MEDIUM RISK: Breach provisions outlined. Non-compliance has consequences.",
            "penalty": "⚠️ HIGH RISK: Penalties for non-compliance. Review financial consequences.",
            "penalties": "⚠️ HIGH RISK: Multiple penalty clauses detected.",
            "fine": "⚠️ MEDIUM RISK: Fines may be imposed.",
            "arbitration": "📋 MEDIUM RISK: Disputes resolved through arbitration, not court.",
            "non-compete": "⚠️ HIGH RISK: Non-compete restrictions may limit future opportunities.",
            "confidential": "🔒 MEDIUM RISK: Confidentiality obligations apply. Information must stay private.",
            "waive": "⚠️ MEDIUM RISK: You may be waiving certain legal rights.",
            "waiver": "⚠️ MEDIUM RISK: Rights waiver detected.",
        }
        
        text_lower = text.lower()
        for keyword, warning in risk_keywords.items():
            if keyword in text_lower:
                risks.append(warning)
        
        # Default risks if none found
        if not risks:
            risks = [
                "✅ No obvious high-risk clauses detected.",
                "💡 Always have a lawyer review legal documents.",
                "📋 Read the entire document carefully before signing."
            ]
        
        # Take top 3 risks
        risks = risks[:3]

        # Glossary
        glossary = []
        glossary_terms = {
            "indemnify": "To compensate someone for harm or loss. You agree to cover their losses in certain situations.",
            "liability": "Legal responsibility for damages. Being liable means you can be held accountable.",
            "breach": "Failure to fulfill contract terms. Breaking your obligations has consequences.",
            "arbitration": "Resolving disputes outside court through a neutral third party.",
            "terminate": "To end an agreement before its natural expiration.",
            "non-compete": "Restriction preventing work with competitors for a set time and area.",
            "confidential": "Information that must be kept private and not shared.",
            "waive": "To voluntarily give up a right or claim.",
            "penalty": "Punishment or fine for breaking rules or terms.",
        }
        
        for term, definition in glossary_terms.items():
            if term in text_lower:
                glossary.append({
                    "term": term.title(),
                    "definition": definition
                })
        
        # Add defaults if too few
        if len(glossary) < 3:
            glossary.extend([
                {"term": "Contract", "definition": "Legally binding agreement between parties."},
                {"term": "Obligation", "definition": "Legal duty to do or not do something."},
            ])
        
        # Limit to 5 terms
        glossary = glossary[:5]

        result = {
            "summary": summary,
            "redFlags": risks,
            "glossary": glossary
        }
        
        print(f"Analysis complete, returning result")
        return result

    except Exception as e:
        error_msg = str(e)
        print(f"Simplify Error: {error_msg}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Analysis failed: {error_msg}"}
        )

# ---------------- STARTUP EVENT ----------------
@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("JurisClarify Backend Starting...")
    print(f"Tesseract Available: {TESSERACT_AVAILABLE}")
    print("=" * 50)