"""Tests for the Google Maps structured response parser."""

from __future__ import annotations

import json

import pytest

from search_parser.parsers.google_maps import GoogleMapsParseError, GoogleMapsParser


def _place_record() -> list[object | None]:
    record: list[object | None] = [None] * 260
    record[2] = ["205 W Randolph St #1700", "Chicago, IL 60606"]
    record[4] = [None, None, None, ["/search?tbm=lcl&q=reviews"], None, None, None, 4.8, 5123]
    record[7] = ["/url?q=https%3A%2F%2Fexample.com%2F&sa=U", "example.com"]
    record[9] = [None, None, 41.8839259, -87.6341893]
    record[10] = "0x880e2cb9ec507e35:0xe9e2daa04291fdc8"
    record[11] = "Example Law"
    record[13] = ["Personal injury attorney", "Law firm"]
    record[14] = "Chicago Loop"
    record[18] = "Example Law, 205 W Randolph St #1700, Chicago, IL 60606"
    record[30] = "America/Chicago"
    record[72] = [[[["https://lh3.googleusercontent.com/example=w128-h86-k-no"]]]]
    record[76] = [["personal_injury_lawyer", None, 7], ["law_firm", None, 7]]
    record[78] = "ChIJNX5Q7LksDogRyP2RQqDa4uk"
    record[178] = ["(312) 555-0100", None, None, "+13125550100"]
    record[203] = [
        [
            ["Friday", 5, [2026, 8, 14], [["Open 24 hours", [[], []]]]],
            ["Saturday", 6, [2026, 8, 15], [["9 AM–5 PM", [[], []]]]],
        ]
    ]
    return record


def _payload(*records: list[object | None], xssi: bool = True) -> str:
    text = json.dumps([None, [list(records)]])
    return f")]}}'\n{text}" if xssi else text


class TestGoogleMapsParser:
    def setup_method(self) -> None:
        self.parser = GoogleMapsParser()

    def test_can_parse_xssi_payload(self) -> None:
        assert self.parser.can_parse(_payload(_place_record())) == 1.0
        assert self.parser.can_parse("[]") == 0.0

    def test_parse_place_fields(self) -> None:
        results = self.parser.parse(_payload(_place_record()), query="lawyer chicago")

        assert results.search_engine == "google_maps"
        assert results.query == "lawyer chicago"
        assert results.result_count == 1
        place = results.places[0]
        assert place.position == 1
        assert place.name == "Example Law"
        assert place.website == "https://example.com/"
        assert place.domain == "example.com"
        assert place.place_id == "ChIJNX5Q7LksDogRyP2RQqDa4uk"
        assert place.rating == 4.8
        assert place.review_count == 5123
        assert place.phone_e164 == "+13125550100"
        assert place.opening_hours == {"Friday": "Open 24 hours", "Saturday": "9 AM–5 PM"}
        assert place.thumbnail is not None
        assert place.google_maps_url.endswith("query_place_id=ChIJNX5Q7LksDogRyP2RQqDa4uk")

    def test_deduplicates_repeated_place_arrays(self) -> None:
        record = _place_record()
        results = self.parser.parse(_payload(record, record))
        assert results.result_count == 1

    def test_accepts_plain_json_and_missing_optional_fields(self) -> None:
        record = _place_record()
        record[4] = None
        record[7] = None
        record[72] = None
        record[78] = None
        record[178] = None
        record[203] = None

        result = self.parser.parse(_payload(record, xssi=False)).places[0]
        assert result.website is None
        assert result.rating is None
        assert result.place_id is None
        assert result.phone is None
        assert result.opening_hours == {}

    def test_invalid_payload_raises_specific_error(self) -> None:
        with pytest.raises(GoogleMapsParseError, match="Invalid Google Maps"):
            self.parser.parse("<html>captcha</html>")

        with pytest.raises(GoogleMapsParseError, match="XSSI prefix"):
            self.parser.parse(")]}'")

    def test_serializes_to_json(self) -> None:
        encoded = self.parser.parse(_payload(_place_record())).to_json()
        assert '"search_engine": "google_maps"' in encoded
        assert '"result_count": 1' in encoded
