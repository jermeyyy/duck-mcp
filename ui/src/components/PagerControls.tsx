interface PagerControlsProps {
  currentPage: number;
  totalPages: number;
  isFirstPage: boolean;
  isLastPage: boolean;
  onBack: () => void;
  onNext: () => void;
  onSubmit: () => void;
}

export function PagerControls({
  currentPage,
  totalPages,
  isFirstPage,
  isLastPage,
  onBack,
  onNext,
  onSubmit,
}: PagerControlsProps) {
  return (
    <div className="pager-controls">
      <button
        className="pager-btn pager-btn-secondary"
        onClick={onBack}
        disabled={isFirstPage}
        aria-label="Previous question"
      >
        ← Back
      </button>
      <span className="page-indicator">
        {currentPage + 1} / {totalPages}
      </span>
      {isLastPage ? (
        <button
          className="pager-btn pager-btn-primary"
          onClick={onSubmit}
          aria-label="Submit answers"
        >
          Submit →
        </button>
      ) : (
        <button
          className="pager-btn pager-btn-primary"
          onClick={onNext}
          aria-label="Next question"
        >
          Next →
        </button>
      )}
    </div>
  );
}
