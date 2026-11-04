from pathlib import Path
from flask import Blueprint, render_template, request, current_app
from app.services.document_lister import DocumentLister
from app.infrastructure.fs_document_repository import FileSystemDocumentRepository

listing_bp = Blueprint("listing", __name__)


def _lister() -> DocumentLister:
    return DocumentLister(FileSystemDocumentRepository())


@listing_bp.get("/documents")
def index():
    default_dir = current_app.config.get("INPUT_DIR", "")
    path_str = request.args.get("path", default_dir).strip()

    if not path_str:
        return render_template("listing.html", path=path_str, documents=None, error=None, default_dir=default_dir)

    directory = Path(path_str)
    try:
        documents = _lister().list_documents(directory)
    except ValueError as exc:
        return render_template("listing.html", path=path_str, documents=None, error=str(exc), default_dir=default_dir)

    return render_template("listing.html", path=path_str, documents=documents, error=None, default_dir=default_dir)
