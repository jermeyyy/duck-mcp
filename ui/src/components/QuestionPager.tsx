import { useState, useCallback, useEffect } from "react";
import type { QuestionConfig, Answers } from "../types";
import { SingleSelectPage } from "./SingleSelectPage";
import { MultiSelectPage } from "./MultiSelectPage";
import { TextInputPage } from "./TextInputPage";
import { PagerControls } from "./PagerControls";

interface QuestionPagerProps {
  config: QuestionConfig;
  onSubmit: (answers: Answers) => void;
}

export function QuestionPager({ config, onSubmit }: QuestionPagerProps) {
  const { questions } = config;
  const [currentPage, setCurrentPage] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [validationError, setValidationError] = useState<string | null>(null);

  const currentQuestion = questions[currentPage];
  const isLastPage = currentPage === questions.length - 1;
  const isFirstPage = currentPage === 0;

  const updateAnswer = useCallback((questionId: string, value: Answers[string]) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
    setValidationError(null);
  }, []);

  const validateCurrent = useCallback((): boolean => {
    const q = questions[currentPage];
    if (!q.required) return true;
    const answer = answers[q.id];
    if (answer === null || answer === undefined) return false;
    if (typeof answer === "string" && answer.trim() === "") return false;
    if (Array.isArray(answer) && answer.length === 0) return false;
    return true;
  }, [questions, currentPage, answers]);

  const handleNext = useCallback(() => {
    if (!validateCurrent()) {
      setValidationError("This question is required");
      return;
    }
    setValidationError(null);
    setCurrentPage((p) => Math.min(p + 1, questions.length - 1));
  }, [validateCurrent, questions.length]);

  const handleBack = useCallback(() => {
    setValidationError(null);
    setCurrentPage((p) => Math.max(p - 1, 0));
  }, []);

  const handleSubmit = useCallback(() => {
    if (!validateCurrent()) {
      setValidationError("This question is required");
      return;
    }
    onSubmit(answers);
  }, [validateCurrent, onSubmit, answers]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" && !isFirstPage) {
        handleBack();
      } else if (e.key === "ArrowRight" && !isLastPage) {
        handleNext();
      } else if (e.key === "Enter" && isLastPage) {
        handleSubmit();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFirstPage, isLastPage, handleBack, handleNext, handleSubmit]);

  const renderQuestion = () => {
    const answer = answers[currentQuestion.id];
    switch (currentQuestion.type) {
      case "single_select":
        return (
          <SingleSelectPage
            question={currentQuestion}
            value={typeof answer === "string" ? answer : null}
            onChange={(val) => updateAnswer(currentQuestion.id, val)}
          />
        );
      case "multi_select":
        return (
          <MultiSelectPage
            question={currentQuestion}
            value={Array.isArray(answer) ? answer : []}
            onChange={(val) => updateAnswer(currentQuestion.id, val)}
          />
        );
      case "text":
        return (
          <TextInputPage
            question={currentQuestion}
            value={typeof answer === "string" ? answer : ""}
            onChange={(val) => updateAnswer(currentQuestion.id, val)}
          />
        );
    }
  };

  return (
    <div className="pager">
      <div className="pager-content">
        {renderQuestion()}
        {validationError && (
          <div className="validation-error">{validationError}</div>
        )}
      </div>
      <PagerControls
        currentPage={currentPage}
        totalPages={questions.length}
        isFirstPage={isFirstPage}
        isLastPage={isLastPage}
        onBack={handleBack}
        onNext={handleNext}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
