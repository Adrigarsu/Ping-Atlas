from unittest.mock import MagicMock, patch

import pytest

import app.probe.geoip as geoip_module
from app.probe.geoip import ConfigurationError, GeoResult, resolve


def _make_reader(lat: float, lon: float, country: str, city: str) -> MagicMock:
    record = MagicMock()
    record.location.latitude = lat
    record.location.longitude = lon
    record.country.name = country
    record.city.name = city
    reader = MagicMock()
    reader.city.return_value = record
    return reader


@pytest.fixture(autouse=True)
def reset_reader():
    original = geoip_module._reader
    yield
    geoip_module._reader = original


def test_resolve_public_ip_returns_geo_result() -> None:
    geoip_module._reader = _make_reader(37.386, -122.0838, "United States", "Mountain View")
    result = resolve("8.8.8.8")
    assert result.latitude == 37.386
    assert result.longitude == -122.0838
    assert result.country == "United States"
    assert result.city == "Mountain View"


@pytest.mark.parametrize("ip", ["192.168.1.1", "10.0.0.1", "172.16.0.1", "127.0.0.1"])
def test_resolve_private_ip_returns_none(ip: str) -> None:
    geoip_module._reader = MagicMock()
    result = resolve(ip)
    assert result == GeoResult(latitude=None, longitude=None, country=None, city=None)
    geoip_module._reader.city.assert_not_called()


def test_init_raises_configuration_error_on_missing_file() -> None:
    with patch("geoip2.database.Reader", side_effect=FileNotFoundError):
        with pytest.raises(ConfigurationError, match="not found"):
            geoip_module.init()


def test_init_raises_configuration_error_on_generic_exception() -> None:
    with patch("geoip2.database.Reader", side_effect=OSError("permission denied")):
        with pytest.raises(ConfigurationError, match="Failed to open"):
            geoip_module.init()


def test_resolve_invalid_ip_string_returns_none() -> None:
    geoip_module._reader = MagicMock()
    result = resolve("not-an-ip")
    assert result == GeoResult(latitude=None, longitude=None, country=None, city=None)


def test_resolve_address_not_found_returns_none() -> None:
    import geoip2.errors

    reader = MagicMock()
    reader.city.side_effect = geoip2.errors.AddressNotFoundError("not found")
    geoip_module._reader = reader
    result = resolve("1.2.3.4")
    assert result == GeoResult(latitude=None, longitude=None, country=None, city=None)