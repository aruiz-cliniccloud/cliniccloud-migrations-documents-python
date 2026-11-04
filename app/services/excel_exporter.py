import logging
from io import BytesIO
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

from app.domain.document import Document

logger = logging.getLogger(__name__)

_UPLOADED_FILES_ANCHOR = "uploaded_files"


def _resolve_export_relative_path(document: Document, root: Path) -> str:
    full_path = root / document.relative_path
    parts = full_path.parts
    if _UPLOADED_FILES_ANCHOR in parts:
        idx = parts.index(_UPLOADED_FILES_ANCHOR)
        return str(Path(*parts[idx:]))
    return document.relative_path


def generate_excel(documents: list[Document], root: Path) -> bytes:
    logger.info("Excel export started: %d documents from %s", len(documents), root)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Documents"

    headers = ["ruta", "ruta_relativa", "nombre_fichero", "extension"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "A2"

    for doc in documents:
        full_path = str(root / doc.relative_path)
        relative = _resolve_export_relative_path(doc, root)
        ws.append([full_path, relative, doc.name.value, doc.extension])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 80)

    buffer = BytesIO()
    wb.save(buffer)
    size_kb = round(len(buffer.getvalue()) / 1024, 1)
    logger.info("Excel export complete: %s KB (%d rows)", size_kb, len(documents))
    return buffer.getvalue()
