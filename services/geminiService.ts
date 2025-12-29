
import { GoogleGenAI, Type } from "@google/genai";
import { LegalAnalysis, Language } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

export const analyzeDocument = async (
  fileData: string,
  mimeType: string
): Promise<LegalAnalysis> => {
  // Use pro for initial heavy analysis
  const model = 'gemini-3-pro-preview';
  
  const systemInstruction = `
    You are a world-class senior legal expert. Analyze the provided document.
    Generate:
    1. A 3-sentence executive summary.
    2. Exactly 3 'Red Flags' (one-sided or harmful clauses).
    3. Exactly 5 complex legal terms found in the text with simple definitions.
    
    Output must be strict JSON. Return the response in English initially.
  `;

  const response = await ai.models.generateContent({
    model: model,
    contents: [
      {
        parts: [
          {
            inlineData: {
              data: fileData.split(',')[1],
              mimeType: mimeType,
            },
          },
          { text: "Analyze this legal document precisely." }
        ],
      },
    ],
    config: {
      systemInstruction,
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          summary: { type: Type.STRING },
          redFlags: { type: Type.ARRAY, items: { type: Type.STRING } },
          glossary: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                term: { type: Type.STRING },
                definition: { type: Type.STRING }
              },
              required: ["term", "definition"]
            }
          }
        },
        required: ["summary", "redFlags", "glossary"]
      }
    },
  });

  const resultText = response.text;
  if (!resultText) throw new Error("No response from AI");
  return JSON.parse(resultText) as LegalAnalysis;
};

export const translateAnalysis = async (
  analysis: LegalAnalysis,
  targetLanguage: Language
): Promise<LegalAnalysis> => {
  if (targetLanguage === Language.ENGLISH) return analysis;

  const model = 'gemini-3-flash-preview';
  const targetName = targetLanguage === Language.HINDI ? 'Hindi' : 'Marathi';

  const prompt = `
    Translate the following JSON legal analysis into ${targetName}. 
    Keep the legal precision but ensure the language is accessible to a common person.
    Ensure the JSON structure remains IDENTICAL.
    
    JSON to translate:
    ${JSON.stringify(analysis)}
  `;

  const response = await ai.models.generateContent({
    model: model,
    contents: prompt,
    config: {
      responseMimeType: "application/json",
    },
  });

  const resultText = response.text;
  if (!resultText) throw new Error("Translation failed");
  return JSON.parse(resultText) as LegalAnalysis;
};
