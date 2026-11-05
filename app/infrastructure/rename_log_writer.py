from datetime import datetime
from pathlib import Path


def write_rename_log(
    output_dir: Path,
    excel_filename: str,
    company_id: str,
    result_rows: list[dict],
) -> Path:
    """Write a summary .txt log into output_dir and return the created file path."""
    now = datetime.now()

    success_count = sum(1 for r in result_rows if r["error"] is None)
    error_count = sum(1 for r in result_rows if r["error"] is not None)
    unchanged_count = sum(1 for r in result_rows if r["error"] is None and r["is_unchanged"])

    lines = [
        "=== Rename Operation Log ===",
        f"Date:        {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Company ID:  {company_id}",
        f"Excel file:  {excel_filename}",
        f"Output dir:  {output_dir}",
        "",
        "Summary:",
        f"  Total:     {len(result_rows)}",
        f"  Success:   {success_count}",
        f"  Unchanged: {unchanged_count}",
        f"  Errors:    {error_count}",
        "",
        "Detail:",
    ]

    for row in result_rows:
        if row["error"]:
            lines.append(
                f"  [ERROR] {row['original_name']} → {row['new_name']} — {row['error']}"
            )
        elif row["is_unchanged"]:
            lines.append(f"  [=]     {row['original_name']} (unchanged)")
        else:
            lines.append(f"  [OK]    {row['original_name']} → {row['new_name']}")

    log_path = output_dir / f"_rename_log_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_path
