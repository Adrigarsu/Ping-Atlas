import ipaddress
import os
from dataclasses import dataclass

import geoip2.database
import geoip2.errors


class ConfigurationError(Exception):
    pass


@dataclass
class GeoResult:
    latitude: float | None
    longitude: float | None
    country: str | None
    city: str | None


_reader: geoip2.database.Reader | None = None


def init() -> None:
    """Load the GeoLite2 database. Must be called once at application startup."""
    global _reader
    path = os.environ.get("GEOIP_DB_PATH", "backend/data/GeoLite2-City.mmdb")
    try:
        _reader = geoip2.database.Reader(path)
    except FileNotFoundError:
        raise ConfigurationError(f"GeoLite2 database not found at '{path}'")
    except Exception as exc:
        raise ConfigurationError(f"Failed to open GeoLite2 database: {exc}") from exc


def _is_private(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local
    except ValueError:
        return True


def resolve(ip: str) -> GeoResult:
    """Return geolocation for an IP. Private/reserved IPs return all-None result."""
    if _reader is None or _is_private(ip):
        return GeoResult(latitude=None, longitude=None, country=None, city=None)

    try:
        record = _reader.city(ip)
        return GeoResult(
            latitude=record.location.latitude,
            longitude=record.location.longitude,
            country=record.country.name,
            city=record.city.name,
        )
    except geoip2.errors.AddressNotFoundError:
        return GeoResult(latitude=None, longitude=None, country=None, city=None)