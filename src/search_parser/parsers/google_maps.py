"""Parser for Google Maps' XSSI-prefixed structured search response."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from search_parser.core.models import GoogleMapsPlace, GoogleMapsResults


class GoogleMapsParseError(ValueError):
    """Raised when a Google Maps structured response cannot be decoded."""


class GoogleMapsParser:
    """Decode places from Google Maps' undocumented ``tbm=map`` response.

    Google prefixes this JSON response with an XSSI guard. Place data is stored
    in positional arrays, so all index knowledge is intentionally isolated in
    this parser.
    """

    engine_name = "google_maps"

    def can_parse(self, payload: str | bytes) -> float:
        """Return a confidence score for a possible structured Maps payload."""
        text = payload.decode("utf-8", "replace") if isinstance(payload, bytes) else payload
        return 1.0 if text.lstrip().startswith(")]}'") else 0.0

    def parse(self, payload: str | bytes, query: str | None = None) -> GoogleMapsResults:
        """Parse a raw Maps response into typed place records."""
        data, xssi_prefixed = self._decode_payload(payload)
        places: list[GoogleMapsPlace] = []
        seen: set[str] = set()

        for value in self._walk_lists(data):
            if not self._is_place_record(value) or value[10] in seen:
                continue
            seen.add(value[10])
            places.append(self._parse_place(value, len(places) + 1))

        return GoogleMapsResults(
            query=query,
            places=places,
            result_count=len(places),
            metadata={"xssi_prefixed": xssi_prefixed, "schema": "tbm-map-positional-v1"},
        )

    @staticmethod
    def _decode_payload(payload: str | bytes) -> tuple[Any, bool]:
        text = payload.decode("utf-8", "replace") if isinstance(payload, bytes) else payload
        text = text.lstrip()
        xssi_prefixed = text.startswith(")]}'")
        if xssi_prefixed:
            _, separator, text = text.partition("\n")
            if not separator:
                raise GoogleMapsParseError("XSSI prefix was not followed by a JSON payload")
        try:
            return json.loads(text), xssi_prefixed
        except (json.JSONDecodeError, TypeError) as exc:
            raise GoogleMapsParseError("Invalid Google Maps structured response") from exc

    @staticmethod
    def _walk_lists(value: Any) -> Iterator[list[Any]]:
        stack = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, list):
                yield current
                stack.extend(reversed(current))
            elif isinstance(current, dict):
                stack.extend(reversed(list(current.values())))

    @classmethod
    def _is_place_record(cls, value: list[Any]) -> bool:
        return (
            len(value) > 18
            and isinstance(value[9], list)
            and len(value[9]) >= 4
            and cls._is_number(value[9][2])
            and cls._is_number(value[9][3])
            and isinstance(value[10], str)
            and value[10].startswith("0x")
            and isinstance(value[11], str)
            and isinstance(value[13], list)
        )

    @staticmethod
    def _is_number(value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _parse_place(self, record: list[Any], position: int) -> GoogleMapsPlace:
        website, domain = self._website(record)
        place_id = self._place_id(record)
        rating, review_count, review_url = self._reviews(record)
        phone, phone_e164 = self._phone(record)

        return GoogleMapsPlace(
            position=position,
            name=record[11],
            data_id=record[10],
            place_id=place_id,
            google_maps_url=self._maps_url(record[11], place_id),
            website=website,
            domain=domain,
            address=self._string_at(record, 18),
            address_lines=self._string_list_at(record, 2),
            district=self._string_at(record, 14),
            latitude=float(record[9][2]),
            longitude=float(record[9][3]),
            rating=rating,
            review_count=review_count,
            review_url=review_url,
            categories=self._string_list_at(record, 13),
            category_ids=self._category_ids(record),
            phone=phone,
            phone_e164=phone_e164,
            timezone=self._string_at(record, 30),
            thumbnail=self._thumbnail(record),
            opening_hours=self._opening_hours(record),
        )

    @staticmethod
    def _value_at(record: list[Any], index: int) -> Any:
        return record[index] if len(record) > index else None

    @classmethod
    def _string_at(cls, record: list[Any], index: int) -> str | None:
        value = cls._value_at(record, index)
        return value if isinstance(value, str) and value else None

    @classmethod
    def _string_list_at(cls, record: list[Any], index: int) -> list[str]:
        value = cls._value_at(record, index)
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str) and item]

    @classmethod
    def _website(cls, record: list[Any]) -> tuple[str | None, str | None]:
        value = cls._value_at(record, 7)
        if not isinstance(value, list) or not value or not isinstance(value[0], str):
            return None, None
        website = cls._decode_redirect(value[0])
        domain = value[1] if len(value) > 1 and isinstance(value[1], str) else None
        return website, domain or urlparse(website).netloc or None

    @staticmethod
    def _decode_redirect(url: str) -> str:
        if not url.startswith("/url?"):
            return url
        parsed = parse_qs(urlparse(url).query)
        return parsed.get("q", parsed.get("url", [url]))[0]

    @classmethod
    def _place_id(cls, record: list[Any]) -> str | None:
        direct = cls._string_at(record, 78)
        if direct and direct.startswith("ChIJ"):
            return direct
        for nested in cls._walk_lists(record):
            for item in nested:
                if isinstance(item, str) and item.startswith("ChIJ"):
                    return item
        return None

    @classmethod
    def _reviews(cls, record: list[Any]) -> tuple[float | None, int | None, str | None]:
        value = cls._value_at(record, 4)
        if not isinstance(value, list):
            return None, None, None
        rating = value[7] if len(value) > 7 and cls._is_number(value[7]) else None
        count = value[8] if len(value) > 8 and isinstance(value[8], int) else None
        review_url = cls._nested_string(value, (3, 0))
        return float(rating) if rating is not None else None, count, cls._absolute_url(review_url)

    @classmethod
    def _phone(cls, record: list[Any]) -> tuple[str | None, str | None]:
        value = cls._value_at(record, 178)
        if not isinstance(value, list):
            return None, None
        phone = value[0] if value and isinstance(value[0], str) else None
        e164 = value[3] if len(value) > 3 and isinstance(value[3], str) else None
        return phone, e164

    @classmethod
    def _category_ids(cls, record: list[Any]) -> list[str]:
        value = cls._value_at(record, 76)
        if not isinstance(value, list):
            return []
        return [
            item[0]
            for item in value
            if isinstance(item, list) and item and isinstance(item[0], str)
        ]

    @classmethod
    def _thumbnail(cls, record: list[Any]) -> str | None:
        photos = cls._value_at(record, 72)
        for nested in cls._walk_lists(photos):
            for item in nested:
                if (
                    isinstance(item, str)
                    and item.startswith("https://")
                    and "googleusercontent.com" in item
                ):
                    return item
        return None

    @classmethod
    def _opening_hours(cls, record: list[Any]) -> dict[str, str]:
        value = cls._value_at(record, 203)
        days = value[0] if isinstance(value, list) and value and isinstance(value[0], list) else []
        hours: dict[str, str] = {}
        for day in days:
            name = day[0] if isinstance(day, list) and day and isinstance(day[0], str) else None
            display = cls._nested_string(day, (3, 0, 0))
            if name and display:
                hours[name] = display
        return hours

    @staticmethod
    def _nested_string(value: Any, path: tuple[int, ...]) -> str | None:
        for index in path:
            if not isinstance(value, list) or len(value) <= index:
                return None
            value = value[index]
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _absolute_url(url: str | None) -> str | None:
        return urljoin("https://www.google.com", url) if url else None

    @staticmethod
    def _maps_url(name: str, place_id: str | None) -> str:
        params = {"api": "1", "query": name}
        if place_id:
            params["query_place_id"] = place_id
        return f"https://www.google.com/maps/search/?{urlencode(params)}"
