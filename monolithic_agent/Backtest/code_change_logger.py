"""
Code Change Logger - Track code changes during iterative bot script generation
==============================================================================

Tracks every diff between iterations while the AI attempts to fix a bot script.
Detects when the LLM fails to actually change the code, preventing silent no-op loops.

Features:
- Line-by-line unified diffs between iterations
- Similarity ratio detection (spots no-op fixes)
- Per-strategy log files with timestamps
- Structured change records for programmatic access
- Summary report at end of fix session

Version: 1.0.0
"""

import difflib
import logging
import csv
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


# Similarity threshold below which we consider the code "not meaningfully changed"
NO_CHANGE_THRESHOLD = 0.98  # 98% similar = effectively unchanged


@dataclass
class IterationChange:
    """Record of code changes for a single fix iteration"""
    attempt_number: int
    timestamp: datetime
    error_type: str
    error_summary: str
    lines_before: int
    lines_after: int
    lines_added: int
    lines_removed: int
    similarity_ratio: float          # 1.0 = identical, 0.0 = completely different
    is_meaningful_change: bool       # False when LLM returned nearly identical code
    diff_preview: str                # First N lines of unified diff
    diff_full: str                   # Complete unified diff


class CodeChangeLogger:
    """
    Logs and analyses code changes across iterative fix attempts for a single strategy.

    Usage::

        logger_instance = CodeChangeLogger(strategy_id="algo123", logs_dir=Path("logs/changes"))
        ...
        # after each fix attempt:
        change = logger_instance.record_iteration(
            attempt_number=1,
            code_before=original_code,
            code_after=fixed_code,
            error_type="type_error",
            error_summary="PatternLogger.log_pattern() got unexpected kwarg 'additional_info'"
        )
        if not change.is_meaningful_change:
            logger.warning("LLM returned identical code - no edit was made!")
    """

    def __init__(
        self,
        strategy_id: str,
        logs_dir: Optional[Path] = None,
        diff_preview_lines: int = 40,
    ):
        self.strategy_id = strategy_id
        self.diff_preview_lines = diff_preview_lines
        self.changes: List[IterationChange] = []

        # Determine log directory
        if logs_dir is None:
            logs_dir = Path(__file__).parent / "logs" / "code_changes"
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Session log file (CSV – easy to open in Excel / pandas)
        session_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = self.logs_dir / f"{strategy_id}_code_changes_{session_ts}.csv"
        self._init_csv()

        # Human-readable diff file
        self.diff_path = self.logs_dir / f"{strategy_id}_diffs_{session_ts}.txt"

        logger.info(
            f"[CodeChangeLogger] Initialized for '{strategy_id}' | "
            f"CSV: {self.csv_path.name} | Diffs: {self.diff_path.name}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_iteration(
        self,
        attempt_number: int,
        code_before: str,
        code_after: str,
        error_type: str = "unknown",
        error_summary: str = "",
    ) -> IterationChange:
        """
        Compute and persist the diff between two iterations of the bot code.

        Args:
            attempt_number: 1-based fix iteration index
            code_before:    Code that was passed to the LLM for fixing
            code_after:     Code returned by the LLM after the fix attempt
            error_type:     Classified error type (e.g. 'type_error')
            error_summary:  Short description of the error that was being fixed

        Returns:
            IterationChange dataclass with all diff metrics.
        """
        lines_before = code_before.splitlines(keepends=True)
        lines_after = code_after.splitlines(keepends=True)

        # Unified diff
        diff_lines = list(
            difflib.unified_diff(
                lines_before,
                lines_after,
                fromfile=f"attempt_{attempt_number - 1}_code",
                tofile=f"attempt_{attempt_number}_code",
                lineterm="",
            )
        )

        lines_added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        lines_removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

        # Similarity ratio (fast sequence matcher)
        similarity = difflib.SequenceMatcher(
            None, code_before, code_after, autojunk=False
        ).ratio()
        is_meaningful = similarity < NO_CHANGE_THRESHOLD

        diff_full = "".join(diff_lines)
        diff_preview = "\n".join(diff_lines[: self.diff_preview_lines])
        if len(diff_lines) > self.diff_preview_lines:
            diff_preview += f"\n... ({len(diff_lines) - self.diff_preview_lines} more diff lines)"

        change = IterationChange(
            attempt_number=attempt_number,
            timestamp=datetime.now(),
            error_type=error_type,
            error_summary=error_summary[:200],   # Cap length for CSV readability
            lines_before=len(lines_before),
            lines_after=len(lines_after),
            lines_added=lines_added,
            lines_removed=lines_removed,
            similarity_ratio=round(similarity, 4),
            is_meaningful_change=is_meaningful,
            diff_preview=diff_preview,
            diff_full=diff_full,
        )

        self.changes.append(change)
        self._append_csv(change)
        self._append_diff_file(change)
        self._log_change(change)

        return change

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregate statistics for all recorded iterations."""
        if not self.changes:
            return {
                "strategy_id": self.strategy_id,
                "total_iterations": 0,
                "meaningful_changes": 0,
                "no_op_attempts": 0,
                "total_lines_added": 0,
                "total_lines_removed": 0,
                "csv_log": str(self.csv_path),
                "diff_log": str(self.diff_path),
            }

        meaningful = [c for c in self.changes if c.is_meaningful_change]
        no_ops = [c for c in self.changes if not c.is_meaningful_change]

        return {
            "strategy_id": self.strategy_id,
            "total_iterations": len(self.changes),
            "meaningful_changes": len(meaningful),
            "no_op_attempts": len(no_ops),
            "no_op_attempt_numbers": [c.attempt_number for c in no_ops],
            "total_lines_added": sum(c.lines_added for c in self.changes),
            "total_lines_removed": sum(c.lines_removed for c in self.changes),
            "avg_similarity": round(
                sum(c.similarity_ratio for c in self.changes) / len(self.changes), 4
            ),
            "csv_log": str(self.csv_path),
            "diff_log": str(self.diff_path),
        }

    def log_summary(self) -> None:
        """Write aggregate summary to the logger."""
        summary = self.get_summary()
        logger.info("=" * 70)
        logger.info("[CodeChangeLogger] ITERATION CHANGE SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Strategy:          {summary['strategy_id']}")
        logger.info(f"Total iterations:  {summary['total_iterations']}")
        logger.info(f"Meaningful changes:{summary['meaningful_changes']}")
        logger.info(f"No-op attempts:    {summary['no_op_attempts']}")
        if summary.get("no_op_attempt_numbers"):
            logger.warning(
                f"  No-op at iteration(s): {summary['no_op_attempt_numbers']}"
            )
        logger.info(f"Lines added total: {summary['total_lines_added']}")
        logger.info(f"Lines removed tot: {summary['total_lines_removed']}")
        if summary["total_iterations"]:
            logger.info(f"Avg similarity:    {summary['avg_similarity']}")
        logger.info(f"CSV log:           {summary['csv_log']}")
        logger.info(f"Diff log:          {summary['diff_log']}")
        logger.info("=" * 70)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    _CSV_FIELDS = [
        "attempt_number",
        "timestamp",
        "error_type",
        "error_summary",
        "lines_before",
        "lines_after",
        "lines_added",
        "lines_removed",
        "similarity_ratio",
        "is_meaningful_change",
        "diff_preview",
    ]

    def _init_csv(self) -> None:
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._CSV_FIELDS)
            writer.writeheader()

    def _append_csv(self, change: IterationChange) -> None:
        row = {
            "attempt_number": change.attempt_number,
            "timestamp": change.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "error_type": change.error_type,
            "error_summary": change.error_summary.replace("\n", " "),
            "lines_before": change.lines_before,
            "lines_after": change.lines_after,
            "lines_added": change.lines_added,
            "lines_removed": change.lines_removed,
            "similarity_ratio": change.similarity_ratio,
            "is_meaningful_change": change.is_meaningful_change,
            "diff_preview": change.diff_preview.replace("\n", " | "),
        }
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._CSV_FIELDS)
            writer.writerow(row)

    def _append_diff_file(self, change: IterationChange) -> None:
        header = (
            f"\n{'=' * 70}\n"
            f"ATTEMPT {change.attempt_number} | "
            f"{change.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Error: {change.error_type}\n"
            f"Lines: {change.lines_before} -> {change.lines_after} "
            f"(+{change.lines_added} / -{change.lines_removed}) | "
            f"Similarity: {change.similarity_ratio:.4f} | "
            f"Meaningful: {change.is_meaningful_change}\n"
            f"Error: {change.error_summary}\n"
            f"{'-' * 70}\n"
        )
        diff_body = change.diff_full if change.diff_full else "(no diff - code unchanged)\n"
        with open(self.diff_path, "a", encoding="utf-8") as f:
            f.write(header + diff_body)

    def _log_change(self, change: IterationChange) -> None:
        status = "[CHANGED]" if change.is_meaningful_change else "[NO-OP WARNING]"
        log_msg = (
            f"[CodeChangeLogger] Attempt {change.attempt_number} {status} | "
            f"+{change.lines_added}/-{change.lines_removed} lines | "
            f"similarity={change.similarity_ratio:.4f} | "
            f"error={change.error_type}"
        )
        if change.is_meaningful_change:
            logger.info(log_msg)
        else:
            logger.warning(log_msg)
            logger.warning(
                f"[CodeChangeLogger] LLM returned nearly identical code "
                f"(similarity={change.similarity_ratio:.4f} >= {NO_CHANGE_THRESHOLD}). "
                f"The fix was likely NOT applied to the code."
            )
