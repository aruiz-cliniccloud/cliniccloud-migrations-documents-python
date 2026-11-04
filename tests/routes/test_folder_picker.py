from unittest.mock import patch


class TestFolderPickerRoute:
    def test_browse_folder_returns_200(self, client):
        with patch("app.routes.folder_picker._pick_folder", return_value="/tmp/docs"):
            response = client.get("/browse-folder")
        assert response.status_code == 200

    def test_browse_folder_returns_selected_path(self, client):
        with patch("app.routes.folder_picker._pick_folder", return_value="/tmp/docs"):
            response = client.get("/browse-folder")
        assert response.get_json()["path"] == "/tmp/docs"

    def test_browse_folder_returns_null_when_cancelled(self, client):
        with patch("app.routes.folder_picker._pick_folder", return_value=None):
            response = client.get("/browse-folder")
        assert response.get_json()["path"] is None

    def test_browse_folder_returns_null_when_tkinter_unavailable(self, client):
        with patch("app.routes.folder_picker._pick_folder", side_effect=ImportError):
            response = client.get("/browse-folder")
        assert response.status_code == 200
        assert response.get_json()["path"] is None
