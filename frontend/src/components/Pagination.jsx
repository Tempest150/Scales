import { ChevronLeft, ChevronRight } from "react-bootstrap-icons";

/**
 * Shared pager for server-paginated lists. Used below both the table and
 * card views so paging behaves identically regardless of which one is active.
 */
function Pagination({ page, totalPages, total, onPageChange, disabled }) {
  if (totalPages <= 1) return null;

  return (
    <div className="pagination-bar">
      <button
        type="button"
        className="pagination-btn"
        onClick={() => onPageChange(page - 1)}
        disabled={disabled || page <= 1}
        aria-label="Previous page"
      >
        <ChevronLeft size={14} />
      </button>
      <span className="pagination-status">
        Page {page} of {totalPages}
        {typeof total === "number" ? ` · ${total} total` : ""}
      </span>
      <button
        type="button"
        className="pagination-btn"
        onClick={() => onPageChange(page + 1)}
        disabled={disabled || page >= totalPages}
        aria-label="Next page"
      >
        <ChevronRight size={14} />
      </button>
    </div>
  );
}

export default Pagination;
