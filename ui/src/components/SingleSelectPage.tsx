import type { Question } from "../types";
import { Markdown } from "./Markdown";

interface SingleSelectPageProps {
  question: Question;
  value: string | null;
  onChange: (value: string) => void;
}

export function SingleSelectPage({ question, value, onChange }: SingleSelectPageProps) {
  return (
    <fieldset className="question-page">
      <legend className="question-label">
        <Markdown content={question.label} />
        {question.required && <span className="required-indicator">*</span>}
      </legend>
      <div className="options-list">
        {question.options?.map((option, index) => (
          <label key={index} className="option-item radio-option">
            <input
              type="radio"
              name={question.id}
              value={option}
              checked={value === option}
              onChange={() => onChange(option)}
              className="option-input"
            />
            <span className="option-radio" />
            <span className="option-label">
              <Markdown content={option} inline />
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
