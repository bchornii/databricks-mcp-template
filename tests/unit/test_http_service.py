"""Unit tests for ``server.infrastructure.http``."""

from unittest.mock import MagicMock, patch

from server.infrastructure.http import fetch_url_status


class TestFetchUrlStatus:
    @patch("server.infrastructure.http.request.urlopen")
    def test_successful_json_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.headers.get.return_value = "application/json; charset=utf-8"
        mock_resp.read.return_value = b'{"ok": true}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_url_status("https://api.example.com/health")

        assert result["ok"] is True
        assert result["status_code"] == 200
        assert result["json"] == {"ok": True}

    @patch("server.infrastructure.http.request.urlopen")
    def test_non_json_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.headers.get.return_value = "text/html"
        mock_resp.read.return_value = b"<html>Hello</html>"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_url_status("https://example.com")

        assert result["ok"] is True
        assert "body_preview" in result
        assert "json" not in result

    @patch("server.infrastructure.http.request.urlopen")
    def test_connection_error(self, mock_urlopen):
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Name or service not known")

        result = fetch_url_status("https://nonexistent.invalid")

        assert result["ok"] is False
        assert "Connection error" in result["error"]

    @patch("server.infrastructure.http.request.urlopen")
    def test_http_error(self, mock_urlopen):
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(
            url="https://example.com",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        result = fetch_url_status("https://example.com/missing")

        assert result["ok"] is False
        assert result["status_code"] == 404
        assert "HTTP error" in result["error"]
