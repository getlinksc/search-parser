"""Unit tests for GoogleParser.parse_extras and the ``metadata["extras"]`` it feeds."""

from __future__ import annotations

from search_parser.parsers.google import GoogleParser

PARSER = GoogleParser()

TOTAL_RAW = '<div id="result-stats\\">About 1,234 results\\x3cnobr> (0.24 seconds)'


def _page(body: str) -> str:
    return f"<html><body>{body}</body></html>"


def test_empty_input_returns_empty() -> None:
    assert PARSER.parse_extras("") == {}
    assert PARSER.parse_extras(_page("<p>nothing here</p>")) == {}


def test_total_from_js_string_and_markup() -> None:
    out = PARSER.parse_extras(_page(TOTAL_RAW))
    assert out["total"] == 1234
    assert out["total_text"].startswith("About 1,234 results")
    plain = PARSER.parse_extras(
        _page('<div id="result-stats">About 99 results<nobr> (0.1 s)</nobr></div>')
    )
    assert plain["total"] == 99


def test_total_prefers_first_non_zero_placeholder() -> None:
    html = _page(TOTAL_RAW.replace("1,234", "0") + TOTAL_RAW.replace("1,234", "55"))
    assert PARSER.parse_extras(html)["total"] == 55


def test_videos() -> None:
    html = _page(
        '<div class="xe8e1b"><a class="zReHs" href="/watch?v=1"><h3>How to X</h3></a>'
        '<span class="VuuXrf">YouTube · Some Channel</span>'
        "<cite>2 days ago · 1.2M views</cite><div>12:34</div></div>"
    )
    (video,) = PARSER.parse_extras(html)["videos"]
    assert video["title"] == "How to X"
    assert video["url"] == "https://www.google.com/watch?v=1"
    assert video["site"] == "YouTube"
    assert video["channel"] == "Some Channel"
    assert video["date"] == "2 days ago"
    assert video["stats"] == "1.2M views"
    assert video["duration"] == "12:34"
    assert video["position"] == 1


def test_pagination() -> None:
    html = _page(
        '<a id="pnprev" href="/search?q=x&start=0">Prev</a><a id="pnnext" href="/search?q=x&start=20">Next</a>'
    )
    assert PARSER.parse_extras(html)["pagination"] == {
        "next_start": 20,
        "prev_start": 0,
        "has_next": True,
    }
    first = PARSER.parse_extras(_page('<a id="pnnext" href="/search?q=x&start=10">Next</a>'))
    assert first["pagination"]["prev_start"] is None
    assert PARSER.parse_extras(_page("<p>x</p>")).get("pagination") is None


def test_answers_take_outermost_only_and_drop_hidden_text() -> None:
    html = _page(
        '<div data-attrid="kc:/x:price"><span aria-hidden="true">$9</span><span>9 dollars</span>'
        '<div data-attrid="inner">inner text</div></div>'
    )
    (answer,) = PARSER.parse_extras(html)["answers"]
    assert answer["attrid"] == "kc:/x:price"
    assert "$9" not in answer["text"]
    assert "9 dollars" in answer["text"]


def test_answer_box() -> None:
    html = _page(
        '<div class="xpdopen"><h3>Title</h3><p>Body text</p><a href="https://example.com/a">src</a></div>'
    )
    box = PARSER.parse_extras(html)["answer_box"]
    assert box["title"] == "Title"
    assert "Body text" in box["text"]
    assert box["url"] == "https://example.com/a"


def test_knowledge_panel_links_deduplicated() -> None:
    html = _page(
        '<div id="rhs"><h2>Complementary results</h2><h3>Acme Corp</h3><p>An example company.</p>'
        '<a href="https://acme.example/">Website</a><a href="https://acme.example/">Website</a></div>'
    )
    panel = PARSER.parse_extras(html)["knowledge_panel"]
    assert panel["title"] == "Acme Corp"
    assert panel["links"] == [{"text": "Website", "url": "https://acme.example/"}]


def test_discussions_keep_goto_tokens_unresolved() -> None:
    html = _page(
        '<div><div role="heading">Discussions and forums</div>'
        '<a href="/goto?url=CAESabc"><div role="heading">Is X worth it?</div><span class="R8BTeb">Reddit ·</span> 5 comments · 1 year ago</a></div>'
    )
    (thread,) = PARSER.parse_extras(html)["discussions"]
    assert thread["title"] == "Is X worth it?"
    assert thread["url"] == "/goto?url=CAESabc"
    assert thread["source"] == "Reddit"
    assert thread["meta"] == ["5 comments", "1 year ago"]


def test_ads_use_data_pcu_never_the_click_url() -> None:
    html = _page(
        '<div data-text-ad="1" data-ta-slot="0"><a data-pcu="https://adv.example/landing" data-rw="/aclk?sa=l&adurl=x" href="/aclk?sa=l">'
        '<div role="heading">Buy now</div><span data-dtld="adv.example">adv.example</span><span class="Aozhyc">Adv Inc</span></a>'
        '<div class="p4wth">Great deals</div></div>'
    )
    (ad,) = PARSER.parse_extras(html)["ads"]
    assert ad["link"] == "https://adv.example/landing"
    assert ad["title"] == "Buy now"
    assert ad["display_url"] == "adv.example"
    assert ad["advertiser"] == "Adv Inc"
    assert ad["description"] == "Great deals"
    assert ad["result_type"] == "ad"
    assert "/aclk" not in str(ad)


def test_href_handling() -> None:
    assert PARSER._x_href("") == ""
    assert PARSER._x_href("#frag") == ""
    assert PARSER._x_href("javascript:void(0)") == ""
    assert PARSER._x_href("//cdn.example/x") == "https://cdn.example/x"
    assert PARSER._x_href("/search?q=x") == "https://www.google.com/search?q=x"
    assert PARSER._x_href("https://e.example/") == "https://e.example/"


def test_one_failing_part_does_not_drop_the_rest(monkeypatch) -> None:
    def boom(self, soup):  # noqa: ARG001
        raise RuntimeError("selector broke")

    monkeypatch.setattr(GoogleParser, "_x_videos", boom)
    out = PARSER.parse_extras(_page(TOTAL_RAW))
    assert out["total"] == 1234
    assert "videos" not in out


def test_parse_puts_extras_in_metadata() -> None:
    with_extras = PARSER.parse(
        _page(TOTAL_RAW + '<a id="pnnext" href="/search?q=x&start=10">Next</a>')
    )
    extras = with_extras.metadata["extras"]
    assert isinstance(extras, dict)
    assert extras["total"] == 1234
    assert extras["pagination"]["has_next"] is True
    bare = PARSER.parse(_page("<p>no extras</p>"))
    assert "extras" not in bare.metadata


def test_a_given_soup_gives_the_same_extras() -> None:
    from search_parser.utils import make_soup

    html = _page(TOTAL_RAW)
    assert PARSER.parse_extras(html, make_soup(html)) == PARSER.parse_extras(html)
