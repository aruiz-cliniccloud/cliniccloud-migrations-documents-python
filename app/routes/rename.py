import logging
import tempfile
import uuid
from pathlib import Path

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from app.domain.rename_rule import RenameRule
from app.infrastructure.rename_log_writer import write_rename_log
from app.services.document_renamer import build_previews, copy_renames_to_folder
from app.services.excel_reader import DuplicateColumnsError, read_excel
from app.services.path_checker import check_path_mapping, check_paths_sample

rename_bp = Blueprint("rename", __name__)
logger = logging.getLogger(__name__)

_TMP_SUBDIR = "cliniccloud_rename"


def _save_uploaded_excel(file) -> Path:
    suffix = Path(file.filename).suffix or ".xlsx"
    tmp_dir = Path(tempfile.gettempdir()) / _TMP_SUBDIR
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / f"{uuid.uuid4()}{suffix}"
    file.save(tmp_path)
    return tmp_path


def _rnm() -> dict:
    return dict(session.get("rnm", {}))


def _rnm_set(**kwargs) -> None:
    data = _rnm()
    data.update(kwargs)
    session["rnm"] = data


# ── Step 1 ────────────────────────────────────────────────

@rename_bp.get("/rename")
def index():
    session.pop("rnm", None)
    return render_template("rename.html", step="load")


@rename_bp.post("/rename/columns")
def load_columns():
    company_id = request.form.get("company_id", "").strip()
    excel_file = request.files.get("excel_file")

    if not excel_file or not excel_file.filename:
        return render_template(
            "rename.html", step="load", error_key="rename.error.no_excel_file"
        )
    if not company_id:
        return render_template(
            "rename.html", step="load", error_key="rename.error.no_company_id"
        )

    try:
        excel_tmp_path = _save_uploaded_excel(excel_file)
        columns, _ = read_excel(excel_tmp_path)
    except DuplicateColumnsError as exc:
        return render_template(
            "rename.html",
            step="load",
            error_key="rename.error.duplicate_columns",
            error_detail=", ".join(exc.duplicates),
        )
    except Exception as exc:
        return render_template(
            "rename.html", step="load", error_key=None, error_detail=str(exc)
        )

    if not columns:
        return render_template(
            "rename.html", step="load", error_key="rename.error.no_columns"
        )

    logger.info("Excel loaded: %s — %d columns, company_id=%s", excel_file.filename, len(columns), company_id)

    session["rnm"] = {
        "excel_tmp_path": str(excel_tmp_path),
        "excel_filename": excel_file.filename,
        "company_id": company_id,
        "columns": columns,
    }
    return redirect(url_for("rename.configure"))


# ── Step 2 ────────────────────────────────────────────────

@rename_bp.get("/rename/configure")
def configure():
    s = _rnm()
    if not s.get("columns"):
        return redirect(url_for("rename.index"))
    return render_template(
        "rename.html",
        step="configure",
        excel_filename=s["excel_filename"],
        company_id=s["company_id"],
        columns=s["columns"],
        path_column=s.get("path_column", ""),
        name_cols=s.get("name_cols", []),
        separator=s.get("separator", "_"),
    )


@rename_bp.post("/rename/preview")
def preview_post():
    s = _rnm()
    if not s.get("excel_tmp_path"):
        return redirect(url_for("rename.index"))

    path_column = request.form.get("path_column", "").strip()
    name_cols = request.form.getlist("name_col")
    separator = request.form.get("separator", "_")

    if not name_cols:
        return render_template(
            "rename.html",
            step="configure",
            excel_filename=s["excel_filename"],
            company_id=s["company_id"],
            columns=s["columns"],
            path_column=path_column,
            name_cols=name_cols,
            separator=separator,
            error_key="rename.error.no_name_cols",
        )

    _rnm_set(path_column=path_column, name_cols=name_cols, separator=separator,
             check_result=None, base_dir=None, map_result=None)
    return redirect(url_for("rename.map_get"))


@rename_bp.get("/rename/preview")
def preview_get():
    s = _rnm()
    if not s.get("path_column"):
        return redirect(url_for("rename.index"))

    base_dir_str = s.get("base_dir") or current_app.config.get("INPUT_DIR", "")
    base_dir = Path(base_dir_str) if base_dir_str else None

    try:
        rule = RenameRule(
            path_column=s["path_column"],
            name_columns=tuple(s["name_cols"]),
            separator=s["separator"],
        )
        columns, rows = read_excel(Path(s["excel_tmp_path"]))
        previews = build_previews(rows, rule, base_dir=base_dir)
    except FileNotFoundError:
        return render_template(
            "rename.html",
            step="load",
            error_key="rename.error.file_not_found",
            error_detail=s.get("excel_tmp_path", ""),
        )
    except Exception as exc:
        return render_template(
            "rename.html", step="load", error_key=None, error_detail=str(exc)
        )

    return render_template(
        "rename.html",
        step="preview",
        excel_filename=s["excel_filename"],
        company_id=s["company_id"],
        columns=s["columns"],
        path_column=s["path_column"],
        name_cols=s["name_cols"],
        separator=s["separator"],
        previews=previews,
        check_result=s.get("check_result"),
    )


# ── Step 2b — Map base directory ──────────────────────────

def _get_sample_paths(s: dict, n: int = 5) -> list[str]:
    """Extract up to n non-empty path strings from the Excel's path column."""
    try:
        _, rows = read_excel(Path(s["excel_tmp_path"]))
        col = s.get("path_column", "")
        return [row[col] for row in rows if row.get(col)][:n]
    except Exception:
        return []


@rename_bp.get("/rename/map")
def map_get():
    s = _rnm()
    if not s.get("path_column"):
        return redirect(url_for("rename.index"))
    sample_paths = _get_sample_paths(s)
    return render_template(
        "rename.html",
        step="map",
        excel_filename=s["excel_filename"],
        company_id=s["company_id"],
        columns=s["columns"],
        path_column=s["path_column"],
        name_cols=s["name_cols"],
        separator=s["separator"],
        sample_paths=sample_paths,
        base_dir=s.get("base_dir", current_app.config.get("INPUT_DIR", "")),
        map_result=s.get("map_result"),
    )


@rename_bp.post("/rename/map")
def map_post():
    s = _rnm()
    if not s.get("path_column"):
        return redirect(url_for("rename.index"))

    base_dir_str = request.form.get("base_dir", "").strip()
    if not base_dir_str:
        _rnm_set(base_dir="", map_result={"error": "rename.map.error.no_base_dir"})
        return redirect(url_for("rename.map_get"))

    sample_paths = _get_sample_paths(s)
    mapping = check_path_mapping(sample_paths, Path(base_dir_str))
    all_found = bool(mapping) and all(r["exists"] for r in mapping)

    logger.info(
        "Path mapping — base=%s, sample=%d, found=%d, missing=%d",
        base_dir_str, len(mapping),
        sum(r["exists"] for r in mapping),
        sum(not r["exists"] for r in mapping),
    )
    _rnm_set(base_dir=base_dir_str, map_result={"mapping": mapping, "all_found": all_found})
    return redirect(url_for("rename.map_get"))


# ── Path check ────────────────────────────────────────────

@rename_bp.post("/rename/check-paths")
def check_paths():
    s = _rnm()
    if not s.get("excel_tmp_path"):
        return redirect(url_for("rename.index"))

    base_dir_str = s.get("base_dir") or current_app.config.get("INPUT_DIR", "")
    base_dir = Path(base_dir_str) if base_dir_str else None

    try:
        rule = RenameRule(
            path_column=s["path_column"],
            name_columns=tuple(s["name_cols"]),
            separator=s["separator"],
        )
        _, rows = read_excel(Path(s["excel_tmp_path"]))
        previews = build_previews(rows, rule, base_dir=base_dir)
        items = check_paths_sample(previews)
    except Exception as exc:
        logger.error("Path check failed: %s", exc)
        _rnm_set(check_result={"sample": [], "all_ok": False, "error": str(exc)})
        return redirect(url_for("rename.preview_get"))

    all_ok = bool(items) and all(item["exists"] for item in items)
    logger.info(
        "Path check — sample=%d, ok=%d, missing=%d",
        len(items),
        sum(item["exists"] for item in items),
        sum(not item["exists"] for item in items),
    )
    _rnm_set(check_result={"sample": items, "all_ok": all_ok})
    return redirect(url_for("rename.preview_get"))


# ── Step 3 ────────────────────────────────────────────────

@rename_bp.post("/rename/apply")
def apply():
    s = _rnm()
    if not s.get("excel_tmp_path"):
        return redirect(url_for("rename.index"))

    output_folder_name = f"documentos{s['company_id']}_renombrado"
    output_dir = Path(current_app.config["OUTPUT_DIR"]) / output_folder_name

    base_dir_str = s.get("base_dir") or current_app.config.get("INPUT_DIR", "")
    base_dir = Path(base_dir_str) if base_dir_str else None

    logger.info(
        "Apply started — company_id=%s, output=%s, base_dir=%s",
        s["company_id"], output_folder_name, base_dir,
    )

    try:
        rule = RenameRule(
            path_column=s["path_column"],
            name_columns=tuple(s["name_cols"]),
            separator=s["separator"],
        )
        _, rows = read_excel(Path(s["excel_tmp_path"]))
        previews = build_previews(rows, rule, base_dir=base_dir)
        logger.info("Processing %d files", len(previews))
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_results = copy_renames_to_folder(previews, output_dir)
    except Exception as exc:
        logger.error("Apply failed: %s", exc)
        return render_template(
            "rename.html", step="load", error_key=None, error_detail=str(exc)
        )

    result_rows = [
        {
            "original_name": p.original_path.name,
            "new_name": p.new_name,
            "is_unchanged": p.is_unchanged,
            "error": err,
        }
        for p, (_, _, err) in zip(previews, raw_results)
    ]

    success_count = sum(1 for r in result_rows if r["error"] is None)
    error_count = sum(1 for r in result_rows if r["error"] is not None)
    unchanged_count = sum(
        1 for r in result_rows if r["error"] is None and r["is_unchanged"]
    )

    logger.info(
        "Apply complete — success=%d, unchanged=%d, errors=%d",
        success_count, unchanged_count, error_count,
    )

    try:
        log_path = write_rename_log(output_dir.parent, s["excel_filename"], s["company_id"], result_rows)
        logger.info("Rename log written: %s", log_path)
    except Exception as exc:
        logger.error("Could not write rename log: %s", exc)

    _rnm_set(
        result={
            "rows": result_rows,
            "success_count": success_count,
            "error_count": error_count,
            "unchanged_count": unchanged_count,
            "output_folder": output_folder_name,
            "output_dir": str(output_dir),
        }
    )
    return redirect(url_for("rename.result_get"))


@rename_bp.get("/rename/result")
def result_get():
    s = _rnm()
    r = s.get("result")
    if not r:
        return redirect(url_for("rename.index"))
    return render_template(
        "rename.html",
        step="result",
        result_rows=r["rows"],
        success_count=r["success_count"],
        error_count=r["error_count"],
        unchanged_count=r["unchanged_count"],
        output_folder=r["output_folder"],
        output_dir=r["output_dir"],
    )
