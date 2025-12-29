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

# ---------------- APP ----------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",  
        "https://*.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- OCR SETUP ----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# pytesseract.pytesseract.tesseract_cmd = 'tesseract'  

@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    try:
        image = Image.open(file.file).convert("RGB")
        text = pytesseract.image_to_string(image)
        return {"text": text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------------- DATA MODEL ----------------
class LegalText(BaseModel):
    text: str

# ---------------- SIMPLE RULE-BASED SIMPLIFICATION ----------------
def analyze_legal_text(text: str):
    """Enhanced rule-based legal analysis with better quality"""
    
    # Clean the text
    text_lower = text.lower()
    
    # Generate smarter summary
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    # Detect document type
    doc_type = "contract"
    if "lease" in text_lower or "rent" in text_lower:
        doc_type = "lease agreement"
    elif "employment" in text_lower or "employee" in text_lower:
        doc_type = "employment contract"
    elif "service" in text_lower:
        doc_type = "service agreement"
    elif "non-disclosure" in text_lower or "nda" in text_lower:
        doc_type = "non-disclosure agreement"
    
    # Generate SIMPLE, friendly summary
    if len(sentences) >= 5:
        summary = f"This is a {doc_type} that sets out the rules and responsibilities for both parties. " + \
                  f"Before signing, make sure you understand when you can cancel, what happens if something goes wrong, and how disagreements will be resolved. " + \
                  f"It's always smart to have a lawyer review important contracts."
    elif len(sentences) >= 3:
        summary = f"This {doc_type} explains what each party agrees to do. " + \
                  f"Pay special attention to your obligations, any penalties, and how to exit the agreement if needed."
    else:
        summary = f"This is a short {doc_type} covering the basic terms. " + \
                  f"Make sure you understand your responsibilities before agreeing to anything."
    
    # Detect risks
    risks = []
    
    risk_patterns = {
        "termination": ["terminate", "cancellation", "cancel", "end this agreement", "discontinue"],
        "liability": ["liable", "liability", "responsible for damages", "hold harmless", "at own risk"],
        "penalty": ["penalty", "fine", "forfeit", "liquidated damages", "late fee"],
        "binding": ["binding", "enforceable", "legally bound", "irrevocable"],
        "indemnify": ["indemnify", "indemnification", "defend and hold", "defend, indemnify"],
        "arbitration": ["arbitration", "dispute resolution", "mediation", "binding arbitration"],
        "confidentiality": ["confidential", "non-disclosure", "proprietary", "trade secret"],
        "payment": ["payment", "fees", "compensation", "remuneration", "installment"],
        "warranty": ["warranty", "guarantee", "warrants that", "representation"],
        "jurisdiction": ["jurisdiction", "governing law", "courts of", "legal venue"]
    }
    
    detected_risks = []
    for risk_type, keywords in risk_patterns.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected_risks.append(risk_type)
                break
    
    # Create SIMPLE, friendly risk messages with more detail
    risk_messages = {
        "termination": "⚠️ **Cancellation Terms**: You or the other party can end this agreement. Make sure you know: How much notice is needed? Are there exit fees? What happens to payments already made?",
        "liability": "⚠️ **Financial Risk**: If something goes wrong, you might have to pay for damages. This could be expensive. Check: What's the maximum you could owe? Is there insurance available?",
        "penalty": "⚠️ **Late Fees & Penalties**: Missing payments or breaking rules will cost you money. Find out: How much are the penalties? When do they kick in? Can they be negotiated?",
        "binding": "⚠️ **Legally Binding**: Once you sign, you're locked in. Breaking this contract could lead to lawsuits. Ask yourself: Am I 100% sure about this? Can I afford legal trouble?",
        "indemnify": "⚠️ **You Pay Their Losses**: If the other party faces losses because of you, you must pay them back. This could be very expensive. Understand: What situations trigger this? Is there a limit?",
        "arbitration": "⚠️ **No Court Access**: Disagreements won't go to regular court. You'll use arbitration instead. Know that: You can't appeal the decision, it's usually final.",
        "confidentiality": "⚠️ **Secrets Required**: You can't share certain information. Breaking this rule can get you sued. Be clear on: What's confidential? For how long? What if you accidentally tell someone?",
        "payment": "💰 **Payment Obligations**: Know exactly when and how much you need to pay. Check: Are payments one-time or recurring? What payment methods are accepted? What if you're late?",
        "warranty": "⚠️ **Quality Promises**: There are guarantees about performance or quality. If not met, you should get fixes or refunds. Verify: What's covered? For how long? Who pays for repairs?",
        "jurisdiction": "⚠️ **Location Matters**: Legal disputes will be handled in a specific location's courts. This matters because: It might not be where you live. Travel could be expensive. Different laws apply."
    }
    
    for risk in detected_risks[:3]:  # Limit to 3 most critical risks
        risks.append(risk_messages[risk])
    
    if not risks:
        # If no specific risks found, give helpful general warnings
        risks = [
            "⚠️ Always verify the other party's identity and credentials before signing any agreement.",
            "⚠️ Make sure you understand ALL payment terms, due dates, and what happens if you miss a payment.",
            "⚠️ Check if there are any automatic renewal clauses or cancellation fees before committing."
        ]
    
    # Generate glossary based on detected terms
    glossary = []
    
    glossary_terms = {
        "indemnify": "A promise to pay if the other party faces losses because of you. Can be expensive.",
        "liability": "Being responsible if something goes wrong. You might have to pay for damages.",
        "breach": "Breaking the rules of the contract. This can lead to penalties or being sued.",
        "termination": "Ending the contract. Check how and when you can do this without penalties.",
        "consideration": "What each side gives (money, work, goods). Makes the contract valid.",
        "force majeure": "Big unexpected events (like natural disasters) that excuse not doing what you promised.",
        "arbitration": "Solving disagreements outside of court with a neutral person. Faster but final.",
        "confidential": "Private information you can't share. Breaking this can get you in legal trouble.",
        "warranty": "A promise that something will work as expected. If not, you should get a fix or refund.",
        "jurisdiction": "Which state or country's laws apply and where legal cases will be heard."
    }
    
    # Add relevant terms found in the document
    for term, definition in glossary_terms.items():
        if term in text_lower:
            glossary.append({"term": term.title(), "definition": definition})
    
    # Always ensure we have at least 5 glossary items
    if len(glossary) < 5:
        all_terms = [{"term": k.title(), "definition": v} for k, v in glossary_terms.items()]
        glossary = all_terms[:5]
    
    return summary, risks, glossary

@app.post("/simplify")
async def simplify_legal_text(data: LegalText):
    try:
        text = data.text.strip()
        
        if not text or len(text) < 10:
            return JSONResponse(
                status_code=400,
                content={"error": "Text is too short or empty. Please provide a valid legal document."}
            )
        
        # Analyze the text
        summary, risks, glossary = analyze_legal_text(text)
        
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