import type { Question } from "../types";
import { Markdown } from "./Markdown";

interface TextInputPageProps {
  question: Question;
  value: string;
  onChange: (value: string) => void;
}

export function TextInputPage({ question, value, onChange }: TextInputPageProps) {
  return (
    <div className="question-page">
      <div className="question-label">
        <Markdown content={question.label} />
        {question.required && <span className="required-indicator">*</span>}
      </div>
      <textarea
        className="text-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Type your answer..."
        rows={5}
      />
    </div>
  );
}
