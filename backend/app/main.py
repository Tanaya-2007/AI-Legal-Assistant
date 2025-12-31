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
import requests

# ---------------- API CLIENTS ----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    print("✅ Groq API key found")
else:
    print("⚠️ Groq API key not found")

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

# ---------------- OCR SETUP ----------------
# Tesseract auto-detected on Railway Linux
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@app.get("/")
async def root():
    return {
        "message": "JurisClarify API is running!",
        "status": "healthy",
        "ai_available": {
            "groq": GROQ_API_KEY is not None
        }
    }

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

# ---------------- DOCUMENT VALIDATION ----------------
def is_legal_document(text: str) -> bool:
    """Check if document contains legal language"""
    legal_keywords = [
        'agreement', 'contract', 'party', 'parties', 'terms', 'conditions',
        'liability', 'breach', 'terminate', 'clause', 'legal', 'binding',
        'jurisdiction', 'arbitration', 'indemnify', 'warranty', 'confidential',
        'herein', 'thereof', 'whereby', 'whereas', 'pursuant', 'notwithstanding',
        'obligations', 'rights', 'responsibilities', 'covenant', 'undertake'
    ]
    
    text_lower = text.lower()
    matches = sum(1 for keyword in legal_keywords if keyword in text_lower)
    
    # Need at least 3 legal keywords
    return matches >= 3

# ---------------- AI ANALYSIS WITH FALLBACK ----------------
def analyze_with_groq(text: str):
    """Use Groq AI - 100% FREE"""
    if not GROQ_API_KEY:
        raise Exception("Groq not available")
    
    text = text[:3000]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert legal analyst. Provide clear, concise analysis."
            },
            {
                "role": "user",
                "content": f"""Analyze this legal document:

{text}

Provide exactly:
1. A simple 2-3 sentence summary
2. 3 specific risk warnings (each starting with ⚠️)

Format your response as:

SUMMARY:
[your summary here]

RISKS:
⚠️ [risk 1]
⚠️ [risk 2]
⚠️ [risk 3]"""
            }
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code != 200:
        print(f"Groq API Error: {response.text}")
        raise Exception(f"Groq API failed: {response.status_code}")
    
    data = response.json()
    response_text = data['choices'][0]['message']['content']
    
    # Parse response
    summary = ""
    risks = []
    
    if "SUMMARY:" in response_text:
        summary_section = response_text.split("SUMMARY:")[1].split("RISKS:")[0].strip()
        summary = summary_section
    
    if "RISKS:" in response_text:
        risks_section = response_text.split("RISKS:")[1].strip()
        risk_lines = [line.strip() for line in risks_section.split('\n') if line.strip() and '⚠️' in line]
        risks = risk_lines[:3]
    
    if not summary or len(summary) < 30:
        raise Exception("Groq response too short")
    
    if len(risks) < 3:
        raise Exception("Not enough risks from Groq")
    
    return summary, risks

def detect_risks_rule_based(text: str):
    """Rule-based risk detection as final fallback"""
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
    
    return risks[:3]

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
    
    found_terms = []
    for term, definition in all_terms.items():
        if term.lower() in text_lower:
            found_terms.append({"term": term, "definition": definition})
    
    if len(found_terms) < 5:
        for term, definition in list(all_terms.items())[:5]:
            if {"term": term, "definition": definition} not in found_terms:
                found_terms.append({"term": term, "definition": definition})
    
    return found_terms[:5]

def analyze_rule_based(text: str):
    """Final fallback - rule-based analysis"""
    doc_type = "legal document"
    if "lease" in text.lower() or "rent" in text.lower():
        doc_type = "lease agreement"
    elif "employment" in text.lower():
        doc_type = "employment contract"
    elif "service" in text.lower():
        doc_type = "service agreement"
    
    summary = f"This {doc_type} sets out the rules and responsibilities for both parties. " + \
              f"Before signing, make sure you understand when you can cancel, what happens if something goes wrong, and how disagreements will be resolved."
    
    risks = detect_risks_rule_based(text)
    glossary = extract_legal_terms(text)
    
    return summary, risks, glossary

def analyze_with_ai(text: str):
    """AI analysis with Groq (FREE) fallback to rule-based"""
    
    # Try Groq AI (FREE!)
    try:
        print("Attempting Groq AI analysis...")
        summary, risks = analyze_with_groq(text)
        glossary = extract_legal_terms(text)
        print("✅ Groq AI succeeded")
        return summary, risks, glossary
    except Exception as e:
        print(f"Groq failed: {str(e)}")
    
    # Fallback to rule-based
    print("Using rule-based analysis (Groq failed)")
    return analyze_rule_based(text)

@app.post("/simplify")
async def simplify_legal_text(data: LegalText):
    try:
        text = data.text.strip()
        
        if not text or len(text) < 20:
            return JSONResponse(
                status_code=400,
                content={"error": "Text is too short. Please provide a valid document."}
            )
        
        # Validate it's a legal document
        if not is_legal_document(text):
            return JSONResponse(
                status_code=400,
                content={"error": "This doesn't appear to be a legal document. Please upload contracts, agreements, or legal letters only."}
            )
        
        # Analyze with multi-AI fallback
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