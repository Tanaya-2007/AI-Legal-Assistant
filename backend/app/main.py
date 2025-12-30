import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import pytesseract
from pydantic import BaseModel
import re
import pytesseract
from huggingface_hub import InferenceClient

# ---------------- HF CLIENT ----------------
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("WARNING: HF_TOKEN not found in environment variables!")
    client = None
else:
    client = InferenceClient(api_key=HF_TOKEN)
    print("✅ Hugging Face client initialized")

# ---------------- APP ----------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.railway.app",
        "https://*.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------------- OCR SETUP ----------------
# Tesseract auto-detected on Railway Linux
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@app.get("/")
async def root():
    return {"message": "JurisClarify API is running!", "status": "healthy"}

@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    try:
        image = Image.open(file.file).convert("RGB")
        text = pytesseract.image_to_string(image)
        
        if not text or len(text.strip()) < 20:
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract text from image. Please upload a clearer document."}
            )
        
        return {"text": text}
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------------- DATA MODELS ----------------
class LegalText(BaseModel):
    text: str

# ---------------- AI-POWERED LEGAL ANALYSIS ----------------
def is_legal_document(text: str) -> bool:
    """Check if document contains legal language"""
    legal_keywords = [
        'agreement', 'contract', 'party', 'parties', 'terms', 'conditions',
        'liability', 'breach', 'terminate', 'clause', 'legal', 'binding',
        'jurisdiction', 'arbitration', 'indemnify', 'warranty', 'confidential',
        'herein', 'thereof', 'whereby', 'whereas', 'pursuant', 'notwithstanding'
    ]
    
    text_lower = text.lower()
    matches = sum(1 for keyword in legal_keywords if keyword in text_lower)
    
    # Need at least 3 legal keywords
    return matches >= 3

def analyze_with_ai(text: str):
    """Use Hugging Face AI for intelligent analysis"""
    
    if not client:
        raise Exception("Hugging Face API not configured. Please set HF_TOKEN environment variable.")
    
    # Truncate text for API limits
    text = text[:2000]
    
    try:
        # Generate summary using AI
        summary_prompt = f"""You are a legal expert. Analyze this legal document and provide a simple 2-3 sentence summary that anyone can understand. Focus on what the document is about and the main obligations.

Document:
{text}

Simple Summary:"""

        summary_response = client.text_generation(
            prompt=summary_prompt,
            model="HuggingFaceH4/zephyr-7b-beta",
            max_new_tokens=200,
            temperature=0.3,
        )
        
        summary = summary_response.strip()
        
        # Generate risk analysis using AI
        risk_prompt = f"""You are a legal risk analyst. Identify 3 specific risks or concerns in this legal document. Be specific and mention actual clauses or terms.

Document:
{text}

List exactly 3 risks (one per line, start each with "⚠️"):"""

        risk_response = client.text_generation(
            prompt=risk_prompt,
            model="HuggingFaceH4/zephyr-7b-beta",
            max_new_tokens=300,
            temperature=0.4,
        )
        
        # Parse risks from AI response
        risk_lines = [line.strip() for line in risk_response.split('\n') if line.strip() and '⚠️' in line]
        risks = risk_lines[:3] if risk_lines else []
        
        # If AI didn't generate enough risks, add rule-based ones
        if len(risks) < 3:
            risks = detect_risks_rule_based(text)[:3]
        
        # Generate glossary
        glossary = extract_legal_terms(text)
        
        return summary, risks, glossary
        
    except Exception as e:
        print(f"AI Analysis Error: {str(e)}")
        # Fallback to rule-based analysis
        return analyze_rule_based(text)

def detect_risks_rule_based(text: str):
    """Fallback rule-based risk detection"""
    text_lower = text.lower()
    risks = []
    
    risk_patterns = {
        "termination": "⚠️ **Cancellation Terms**: Document includes termination clauses. Check notice period and exit fees carefully.",
        "liability": "⚠️ **Financial Risk**: Contains liability provisions that may hold you responsible for damages or losses.",
        "penalty": "⚠️ **Penalties**: Financial penalties are specified for non-compliance or late payments.",
        "binding": "⚠️ **Legally Binding**: This is a binding contract. Breaking it could lead to legal consequences.",
        "indemnify": "⚠️ **Indemnification**: You may have to compensate the other party for certain losses.",
        "arbitration": "⚠️ **Arbitration Clause**: Disputes will be resolved through arbitration, not regular courts.",
        "confidentiality": "⚠️ **Confidentiality**: Contains non-disclosure requirements that restrict information sharing.",
        "payment": "⚠️ **Payment Obligations**: Specific payment terms and deadlines are outlined."
    }
    
    for keyword, message in risk_patterns.items():
        if keyword in text_lower and len(risks) < 3:
            risks.append(message)
    
    if not risks:
        risks = [
            "⚠️ Always verify the other party's identity and credentials before signing.",
            "⚠️ Understand all payment terms, due dates, and late payment consequences.",
            "⚠️ Check for automatic renewal clauses or cancellation procedures."
        ]
    
    return risks

def extract_legal_terms(text: str):
    """Extract and define legal terms found in document"""
    text_lower = text.lower()
    
    all_terms = {
        "Indemnify": "A promise to compensate the other party for losses. Can be expensive.",
        "Liability": "Being responsible if something goes wrong. You might have to pay damages.",
        "Breach": "Breaking the contract rules. Can lead to penalties or lawsuits.",
        "Termination": "Ending the contract. Check how and when you can do this.",
        "Consideration": "What each side gives (money, work, goods) to make the contract valid.",
        "Force Majeure": "Unexpected events (disasters, wars) that excuse non-performance.",
        "Arbitration": "Solving disputes outside court with a neutral person. Usually final.",
        "Confidential": "Private information you can't share. Breaking this can get you sued.",
        "Warranty": "A promise that something will work as expected. Get fixes or refunds if not.",
        "Jurisdiction": "Which state or country's laws apply and where cases will be heard."
    }
    
    # Find which terms appear in the document
    found_terms = []
    for term, definition in all_terms.items():
        if term.lower() in text_lower:
            found_terms.append({"term": term, "definition": definition})
    
    # Always return at least 5 terms
    if len(found_terms) < 5:
        for term, definition in list(all_terms.items())[:5]:
            if {"term": term, "definition": definition} not in found_terms:
                found_terms.append({"term": term, "definition": definition})
    
    return found_terms[:5]

def analyze_rule_based(text: str):
    """Fallback analysis without AI"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    doc_type = "legal document"
    if "lease" in text.lower() or "rent" in text.lower():
        doc_type = "lease agreement"
    elif "employment" in text.lower():
        doc_type = "employment contract"
    elif "service" in text.lower():
        doc_type = "service agreement"
    
    summary = f"This {doc_type} outlines the rights and responsibilities of both parties. " + \
              f"It covers important terms including obligations, payments, and what happens if something goes wrong. " + \
              f"Make sure you understand the cancellation terms and any penalties before signing."
    
    risks = detect_risks_rule_based(text)
    glossary = extract_legal_terms(text)
    
    return summary, risks, glossary

@app.post("/simplify")
async def simplify_legal_text(data: LegalText):
    try:
        text = data.text.strip()
        
        if not text or len(text) < 20:
            return JSONResponse(
                status_code=400,
                content={"error": "Text is too short. Please provide a valid document."}
            )
        
        # Check if it's a legal document
        if not is_legal_document(text):
            return JSONResponse(
                status_code=400,
                content={"error": "This doesn't appear to be a legal document. Please upload contracts, agreements, or legal letters only."}
            )
        
        
        summary, risks, glossary = analyze_with_ai(text)
        
        return {
            "summary": summary,
            "redFlags": risks,
            "glossary": glossary
        }
        
    except Exception as e:
        print(f"ERROR in /simplify: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Analysis failed: {str(e)}"}
        )