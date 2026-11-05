import pytest

from app.domain.package_config import PackageConfig


class TestPackageConfig:
    def test_valid_config_creates_correctly(self):
        cfg = PackageConfig(company_id="40826", max_size_bytes=480 * 1024 * 1024)
        assert cfg.company_id == "40826"
        assert cfg.max_size_bytes == 480 * 1024 * 1024

    def test_empty_company_id_raises_value_error(self):
        with pytest.raises(ValueError, match="company_id"):
            PackageConfig(company_id="", max_size_bytes=100)

    def test_zero_max_size_raises_value_error(self):
        with pytest.raises(ValueError, match="max_size_bytes"):
            PackageConfig(company_id="123", max_size_bytes=0)

    def test_negative_max_size_raises_value_error(self):
        with pytest.raises(ValueError, match="max_size_bytes"):
            PackageConfig(company_id="123", max_size_bytes=-1)

    def test_is_immutable(self):
        cfg = PackageConfig(company_id="123", max_size_bytes=100)
        with pytest.raises(Exception):
            cfg.company_id = "456"
