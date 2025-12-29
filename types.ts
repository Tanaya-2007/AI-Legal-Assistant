
export interface LegalAnalysis {
  summary: string;
  redFlags: string[];
  glossary: Array<{
    term: string;
    definition: string;
  }>;
}

export enum AppState {
  IDLE = 'IDLE',
  LOADING = 'LOADING',
  SUCCESS = 'SUCCESS',
  ERROR = 'ERROR'
}

export enum Language {
  ENGLISH = 'en',
  HINDI = 'hi',
  MARATHI = 'mr'
}

export const LanguageNames = {
  [Language.ENGLISH]: 'English',
  [Language.HINDI]: 'हिंदी (Hindi)',
  [Language.MARATHI]: 'मराठी (Marathi)'
};
