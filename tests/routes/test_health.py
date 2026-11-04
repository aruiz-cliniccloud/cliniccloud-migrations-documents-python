class TestHealthRoute:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client):
        response = client.get("/health")
        assert response.get_json()["status"] == "ok"

    def test_health_response_is_json(self, client):
        response = client.get("/health")
        assert response.content_type == "application/json"
