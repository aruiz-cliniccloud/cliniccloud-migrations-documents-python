import logging
import shutil
import tempfile
import uuid
from pathlib import Path

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from app.infrastructure.manifest_csv_writer import write_package_manifest
from app.infrastructure.zip_package_writer import zip_folder
from app.services.csv_reader import MissingColumnsError, read_manifest_csv
from app.services.package_distributor import distribute_files, package_folder_name
from app.services.path_checker import check_path_mapping

packaging_bp = Blueprint("packaging", __name__)
logger = logging.getLogger(__name__)

_TMP_SUBDIR = "cliniccloud_package"
_DEFAULT_MAX_MB = 480


def _save_uploaded_csv(file) -> Path:
    suffix = Path(file.filename).suffix or ".csv"
    tmp_dir = Path(tempfile.gettempdir()) / _TMP_SUBDIR
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / f"{uuid.uuid4()}{suffix}"
    file.save(tmp_path)
    return tmp_path


def _pkg() -> dict:
    return dict(session.get("pkg", {}))


def _pkg_set(**kwargs) -> None:
    data = _pkg()
    data.update(kwargs)
    session["pkg"] = data


def _get_sample_paths(s: dict, n: int = 5) -> list[str]:
    try:
        rows = read_manifest_csv(Path(s["csv_tmp_path"]))
        return [row["Ruta"] for row in rows if row.get("Ruta")][:n]
    except Exception:
        return []


# ── Step 1 ────────────────────────────────────────────────

@packaging_bp.get("/package")
def index():
    session.pop("pkg", None)
    return render_template("packaging.html", step="load", default_max_mb=_DEFAULT_MAX_MB)


@packaging_bp.post("/package/load")
def load():
    csv_file = request.files.get("csv_file")
    company_id = request.form.get("company_id", "").strip()
    max_size_mb_str = request.form.get("max_size_mb", str(_DEFAULT_MAX_MB)).strip()

    if not csv_file or not csv_file.filename:
        return render_template(
            "packaging.html", step="load",
            default_max_mb=_DEFAULT_MAX_MB,
            error_key="package.error.no_csv_file",
        )
    if not company_id:
        return render_template(
            "packaging.html", step="load",
            default_max_mb=_DEFAULT_MAX_MB,
            error_key="package.error.no_company_id",
        )

    try:
        max_mb = int(max_size_mb_str)
        if max_mb <= 0:
            raise ValueError
    except ValueError:
        return render_template(
            "packaging.html", step="load",
            default_max_mb=_DEFAULT_MAX_MB,
            error_key="package.error.invalid_max_size",
        )

    try:
        csv_tmp_path = _save_uploaded_csv(csv_file)
        rows = read_manifest_csv(csv_tmp_path)
    except MissingColumnsError as exc:
        return render_template(
            "packaging.html", step="load",
            default_max_mb=_DEFAULT_MAX_MB,
            error_key="package.error.missing_columns",
            error_detail=", ".join(exc.missing),
        )
    except Exception as exc:
        return render_template(
            "packaging.html", step="load",
            default_max_mb=_DEFAULT_MAX_MB,
            error_key=None, error_detail=str(exc),
        )

    if not rows:
        return render_template(
            "packaging.html", step="load",
            default_max_mb=_DEFAULT_MAX_MB,
            error_key="package.error.empty_csv",
        )

    logger.info("CSV loaded: %s — %d rows, company_id=%s, max=%dMB",
                csv_file.filename, len(rows), company_id, max_mb)

    session["pkg"] = {
        "csv_tmp_path": str(csv_tmp_path),
        "csv_filename": csv_file.filename,
        "company_id": company_id,
        "max_size_mb": max_mb,
    }
    return redirect(url_for("packaging.map_get"))


# ── Step 2 — Map base directory ──────────────────────────

@packaging_bp.get("/package/map")
def map_get():
    s = _pkg()
    if not s.get("csv_tmp_path"):
        return redirect(url_for("packaging.index"))
    sample_paths = _get_sample_paths(s)
    return render_template(
        "packaging.html",
        step="map",
        csv_filename=s["csv_filename"],
        company_id=s["company_id"],
        max_size_mb=s["max_size_mb"],
        sample_paths=sample_paths,
        base_dir=s.get("base_dir", current_app.config.get("INPUT_DIR", "")),
        map_result=s.get("map_result"),
    )


@packaging_bp.post("/package/map")
def map_post():
    s = _pkg()
    if not s.get("csv_tmp_path"):
        return redirect(url_for("packaging.index"))

    base_dir_str = request.form.get("base_dir", "").strip()
    if not base_dir_str:
        _pkg_set(base_dir="", map_result={"error": "package.map.error.no_base_dir"})
        return redirect(url_for("packaging.map_get"))

    sample_paths = _get_sample_paths(s)
    mapping = check_path_mapping(sample_paths, Path(base_dir_str))
    all_found = bool(mapping) and all(r["exists"] for r in mapping)

    logger.info(
        "Path mapping — base=%s, sample=%d, found=%d, missing=%d",
        base_dir_str, len(mapping),
        sum(r["exists"] for r in mapping),
        sum(not r["exists"] for r in mapping),
    )
    _pkg_set(base_dir=base_dir_str, map_result={"mapping": mapping, "all_found": all_found})
    return redirect(url_for("packaging.map_get"))


# ── Step 3 — Preview ──────────────────────────────────────

@packaging_bp.get("/package/preview")
def preview_get():
    s = _pkg()
    if not s.get("csv_tmp_path"):
        return redirect(url_for("packaging.index"))

    base_dir_str = s.get("base_dir") or current_app.config.get("INPUT_DIR", "")
    base_dir = Path(base_dir_str) if base_dir_str else None
    max_size_bytes = s["max_size_mb"] * 1024 * 1024
    company_id = s["company_id"]

    try:
        rows = read_manifest_csv(Path(s["csv_tmp_path"]))
        packages = distribute_files(rows, base_dir, max_size_bytes)
    except Exception as exc:
        return render_template(
            "packaging.html", step="load",
            default_max_mb=_DEFAULT_MAX_MB,
            error_key=None, error_detail=str(exc),
        )

    total_packages = len(packages)
    preview_packages = [
        {
            "name": package_folder_name(company_id, pkg.number, total_packages),
            "file_count": pkg.file_count,
            "total_size_bytes": pkg.total_size_bytes,
            "missing": sum(1 for f in pkg.files if f.size_bytes == 0 and not f.source_path.exists()),
        }
        for pkg in packages
    ]
    total_files = sum(p["file_count"] for p in preview_packages)
    total_size_bytes = sum(p["total_size_bytes"] for p in preview_packages)
    total_missing = sum(1 for pkg in packages for f in pkg.files if not f.source_path.exists())

    return render_template(
        "packaging.html",
        step="preview",
        csv_filename=s["csv_filename"],
        company_id=company_id,
        max_size_mb=s["max_size_mb"],
        preview_packages=preview_packages,
        total_files=total_files,
        total_size_bytes=total_size_bytes,
        total_packages=total_packages,
        total_missing=total_missing,
    )


# ── Step 4 — Apply ────────────────────────────────────────

@packaging_bp.post("/package/apply")
def apply():
    s = _pkg()
    if not s.get("csv_tmp_path"):
        return redirect(url_for("packaging.index"))

    base_dir_str = s.get("base_dir") or current_app.config.get("INPUT_DIR", "")
    base_dir = Path(base_dir_str) if base_dir_str else None
    max_size_bytes = s["max_size_mb"] * 1024 * 1024
    company_id = s["company_id"]

    output_base = Path(current_app.config["OUTPUT_DIR"]) / f"paquetes_{company_id}"
    output_base.mkdir(parents=True, exist_ok=True)

    try:
        rows = read_manifest_csv(Path(s["csv_tmp_path"]))
        packages = distribute_files(rows, base_dir, max_size_bytes)
    except Exception as exc:
        logger.error("Package distribution failed: %s", exc)
        return render_template(
            "packaging.html", step="load",
            default_max_mb=_DEFAULT_MAX_MB,
            error_key=None, error_detail=str(exc),
        )

    total_packages = len(packages)
    files_copied = 0
    files_error = 0
    manifest_rows: list[dict] = []
    package_names: list[str] = []
    errors: list[str] = []

    for pkg in packages:
        folder_name = package_folder_name(company_id, pkg.number, total_packages)
        pkg_dir = output_base / folder_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        package_names.append(folder_name)

        for pf in pkg.files:
            dest = pkg_dir / pf.source_path.name
            try:
                if not pf.source_path.exists():
                    raise FileNotFoundError(f"File not found: {pf.source_path}")
                shutil.copy2(pf.source_path, dest)
                files_copied += 1
                manifest_rows.append({"idImport": pf.id_import, "paquete": folder_name})
                logger.info("Copied: %s → %s/%s", pf.source_path.name, folder_name, pf.source_path.name)
            except (FileNotFoundError, OSError) as exc:
                files_error += 1
                errors.append(str(exc))
                logger.error("Copy failed %s: %s", pf.source_path, exc)

        try:
            zip_folder(pkg_dir)
            logger.info("Zipped: %s", folder_name)
        except Exception as exc:
            logger.error("Zip failed for %s: %s", folder_name, exc)
            errors.append(f"Zip error for {folder_name}: {exc}")

    try:
        manifest_path = write_package_manifest(output_base, company_id, manifest_rows)
        logger.info("Manifest written: %s", manifest_path)
    except Exception as exc:
        logger.error("Could not write manifest: %s", exc)
        manifest_path = output_base / f"manifest_{company_id}.csv"

    logger.info(
        "Packaging complete — packages=%d, copied=%d, errors=%d",
        total_packages, files_copied, files_error,
    )

    _pkg_set(result={
        "packages_created": total_packages,
        "files_total": sum(p.file_count for p in packages),
        "files_copied": files_copied,
        "files_error": files_error,
        "output_dir": str(output_base),
        "manifest_path": str(manifest_path),
        "package_names": package_names,
        "errors": errors[:20],
    })
    return redirect(url_for("packaging.result_get"))


@packaging_bp.get("/package/result")
def result_get():
    s = _pkg()
    r = s.get("result")
    if not r:
        return redirect(url_for("packaging.index"))
    return render_template(
        "packaging.html",
        step="result",
        packages_created=r["packages_created"],
        files_total=r["files_total"],
        files_copied=r["files_copied"],
        files_error=r["files_error"],
        output_dir=r["output_dir"],
        manifest_path=r["manifest_path"],
        package_names=r["package_names"],
        errors=r["errors"],
    )
