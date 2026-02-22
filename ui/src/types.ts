export type QuestionType = "single_select" | "multi_select" | "text";

export interface Question {
  id: string;
  type: QuestionType;
  label: string;
  options?: string[];
  required?: boolean;
}

export interface QuestionConfig {
  session_id: string;
  questions: Question[];
}

export type AnswerValue = string | string[] | null;

export interface Answers {
  [questionId: string]: AnswerValue;
}
