import type { Question } from "../types";
import { Markdown } from "./Markdown";

interface MultiSelectPageProps {
  question: Question;
  value: string[];
  onChange: (value: string[]) => void;
}

export function MultiSelectPage({ question, value, onChange }: MultiSelectPageProps) {
  const handleToggle = (option: string) => {
    if (value.includes(option)) {
      onChange(value.filter((v) => v !== option));
    } else {
      onChange([...value, option]);
    }
  };

  return (
    <fieldset className="question-page">
      <legend className="question-label">
        <Markdown content={question.label} />
        {question.required && <span className="required-indicator">*</span>}
      </legend>
      <div className="options-list">
        {question.options?.map((option, index) => (
          <label key={index} className="option-item checkbox-option">
            <input
              type="checkbox"
              value={option}
              checked={value.includes(option)}
              onChange={() => handleToggle(option)}
              className="option-input"
            />
            <span className="option-checkbox" />
            <span className="option-label">
              <Markdown content={option} inline />
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
