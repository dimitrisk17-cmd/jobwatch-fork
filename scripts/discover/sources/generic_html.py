"""Generic and filtered static HTML discovery providers."""

from __future__ import annotations

import re
from collections.abc import Callable
from html import unescape
from urllib.parse import urljoin, urlparse

from discover import helpers, http
from discover.core import Candidate, Coverage, SourceConfig
from discover.registry import SourceAdapter


LIFEATSPOTIFY_API_ROOT = "https://api.lifeatspotify.com/wp-json/animal/v1"
LIFEATSPOTIFY_DETAIL_ROOT = "https://www.lifeatspotify.com/jobs"


def is_same_page_link(source_url: str, candidate_url: str) -> bool:
    return helpers.normalize_url_without_fragment(source_url) == helpers.normalize_url_without_fragment(candidate_url)


def looks_like_non_job_link(text: str, href: str) -> bool:
    text_lower = helpers.normalize_whitespace(text).lower()
    href_lower = href.lower()
    if text_lower in {
        "",
        "skip to content",
        "jump to main content.",
        "top of this page",
        "top of page",
        "privacy",
        "privacy policy",
        "impressum",
        "report this content",
        "collapse this bar",
        "customize",
        "accept all",
        "accept selection",
        "decline non-essential cookies",
        "subscribe",
        "subscribed",
        "log in",
        "login",
        "log in or register",
        "sign in",
        "sign up",
        "register",
        "create account",
        "my account",
    }:
        return True
    return any(
        marker in href_lower
        for marker in (
            "/privacy",
            "/cookie",
            "/impressum",
            "/learn/",
            "/resources/",
            "/resource/",
            "/services/",
            "/abuse/",
            "/login",
            "/signin",
            "/sign-in",
            "/sign_in",
            "/register",
            "/signup",
            "/sign-up",
            "/sign_up",
            "/auth/",
        )
    )


def collect_job_links(html: str, base_url: str, path_fragment: str) -> dict[str, str]:
    parser = helpers.LinkCollector()
    parser.feed(html)
    links: dict[str, str] = {}
    for link in parser.links:
        absolute_url = urljoin(base_url, link["href"])
        if path_fragment not in absolute_url:
            continue
        links[absolute_url] = link["text"]
    return links


def discover_html(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    if "lifeatspotify.com" in (urlparse(source.url).hostname or "").lower():
        return discover_lifeatspotify_jobs(source, terms, timeout_seconds)
    html = http.fetch_text(source.url, timeout_seconds)
    parser = helpers.LinkCollector()
    parser.feed(html)
    candidates: list[Candidate] = []
    seen_urls: set[str] = set()
    for link in parser.links:
        href = link["href"]
        text = helpers.normalize_whitespace(link["text"])
        if href.startswith("#"):
            continue
        absolute_url = helpers.normalize_url_without_fragment(urljoin(source.url, href))
        if absolute_url in seen_urls:
            continue
        if urlparse(absolute_url).scheme not in {"file", "http", "https"}:
            continue
        if looks_like_non_job_link(text, absolute_url):
            continue
        if is_same_page_link(source.url, absolute_url):
            continue
        matched_terms = helpers.match_terms(f"{text} {absolute_url}", terms)
        if not matched_terms and not helpers.looks_like_job_link(text, absolute_url):
            continue
        if matched_terms and not helpers.should_keep_candidate(text or "unknown", matched_terms, f"{text} {absolute_url}"):
            continue
        seen_urls.add(absolute_url)
        candidates.append(
            Candidate(
                employer=source.source,
                title=text or "unknown",
                url=absolute_url,
                source_url=source.url,
                matched_terms=matched_terms,
                notes="Static HTML enumeration",
            )
        )
    return Coverage(
        source=source.source,
        source_url=source.url,
        discovery_mode=source.discovery_mode,
        cadence_group=source.cadence_group,
        last_checked=source.last_checked,
        due_today=False,
        status="complete",
        listing_pages_scanned=1,
        search_terms_tried=terms,
        result_pages_scanned="local_filter=1",
        direct_job_pages_opened=0,
        enumerated_jobs=len(parser.links),
        matched_jobs=len(candidates),
        limitations=[],
        candidates=candidates,
    )


def _lifeatspotify_searchable_text(job: dict) -> str:
    title = unescape(str(job.get("text") or ""))
    main_cat = (job.get("main_category") or {}).get("name") or ""
    sub_cat = (job.get("sub_category") or {}).get("name") or ""
    job_type = (job.get("job_type") or {}).get("name") or ""
    locations = "; ".join(
        str(entry.get("location") or "")
        for entry in (job.get("locations") or [])
        if isinstance(entry, dict)
    )
    return " ".join(part for part in [title, main_cat, sub_cat, job_type, locations] if part)


def _lifeatspotify_detail_notes(detail: dict) -> str:
    note_parts = ["Enumerated through lifeatspotify.com jobs API"]
    content = detail.get("content") if isinstance(detail, dict) else None
    if not isinstance(content, dict):
        return "; ".join(note_parts)
    description_html = content.get("descriptionHtml") or ""
    if description_html:
        description_text = " ".join(helpers.extract_visible_text_lines_from_html(description_html))
        if description_text:
            note_parts.append(f"Description: {helpers.truncate_text(description_text, 260)}")
    for section in content.get("lists") or []:
        if not isinstance(section, dict):
            continue
        heading = unescape(str(section.get("text") or "")).strip()
        body_text = " ".join(helpers.extract_visible_text_lines_from_html(section.get("content") or ""))
        if heading and body_text:
            note_parts.append(f"{heading}: {helpers.truncate_text(body_text, 260)}")
    return "; ".join(note_parts)


def _lifeatspotify_location(job: dict) -> str:
    locations = [
        unescape(str(entry.get("location") or ""))
        for entry in (job.get("locations") or [])
        if isinstance(entry, dict) and entry.get("location")
    ]
    return "; ".join(locations) or "unknown"


def discover_lifeatspotify_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    search_endpoint = f"{LIFEATSPOTIFY_API_ROOT}/job/search"
    payload = http.fetch_json(search_endpoint, timeout_seconds)
    jobs = payload.get("result", []) if isinstance(payload, dict) else []
    candidates_by_url: dict[str, Candidate] = {}
    direct_job_pages_opened = 0
    limitations: list[str] = []

    for job in jobs:
        if not isinstance(job, dict):
            continue
        job_id = str(job.get("id") or "").strip()
        if not job_id:
            continue
        title = helpers.normalize_whitespace(unescape(str(job.get("text") or ""))) or "unknown"
        searchable_text = _lifeatspotify_searchable_text(job)
        matched_terms = sorted(set(helpers.match_terms(searchable_text, terms)))
        if not helpers.should_keep_candidate(title, matched_terms, searchable_text):
            continue
        detail_notes = "Enumerated through lifeatspotify.com jobs API"
        try:
            detail_payload = http.fetch_json(
                f"{LIFEATSPOTIFY_API_ROOT}/job/single/{job_id}", timeout_seconds
            )
            direct_job_pages_opened += 1
        except Exception as exc:
            limitations.append(f"Could not fetch detail for {job_id}: {type(exc).__name__}: {exc}")
            detail_payload = None
        if isinstance(detail_payload, dict):
            detail_notes = _lifeatspotify_detail_notes(detail_payload.get("data") or {})
        helpers.merge_candidate(
            candidates_by_url,
            Candidate(
                employer=source.source,
                title=title,
                url=f"{LIFEATSPOTIFY_DETAIL_ROOT}/{job_id}",
                source_url=source.url,
                location=_lifeatspotify_location(job),
                matched_terms=matched_terms,
                notes=detail_notes,
            ),
        )

    return Coverage(
        source=source.source,
        source_url=source.url,
        discovery_mode=source.discovery_mode,
        cadence_group=source.cadence_group,
        last_checked=source.last_checked,
        due_today=False,
        status="complete",
        listing_pages_scanned=1,
        search_terms_tried=terms,
        result_pages_scanned="local_filter=1",
        direct_job_pages_opened=direct_job_pages_opened,
        enumerated_jobs=len(jobs),
        matched_jobs=len(candidates_by_url),
        limitations=limitations,
        candidates=list(candidates_by_url.values()),
    )


def discover_filtered_html_links(
    source: SourceConfig,
    terms: list[str],
    timeout_seconds: int,
    url_filter: Callable[[str], bool],
    notes: str,
    limitation_if_empty: str | None = None,
) -> Coverage:
    html = http.fetch_text(source.url, timeout_seconds)
    parser = helpers.LinkCollector()
    parser.feed(html)
    raw_urls: set[str] = set()
    candidates_by_url: dict[str, Candidate] = {}

    for link in parser.links:
        absolute_url = helpers.normalize_url_without_fragment(urljoin(source.url, link["href"]))
        if urlparse(absolute_url).scheme not in {"http", "https"}:
            continue
        if not url_filter(absolute_url):
            continue
        raw_urls.add(absolute_url)
        text = helpers.normalize_whitespace(link["text"]) or "unknown"
        visible_lines = helpers.split_visible_lines(link["text"])
        title = visible_lines[0] if visible_lines else text
        searchable_text = f"{title} {text} {absolute_url}"
        matched_terms = sorted(set(helpers.match_terms(searchable_text, terms)))
        if not helpers.should_keep_candidate(title, matched_terms, searchable_text):
            continue
        helpers.merge_candidate(
            candidates_by_url,
            Candidate(
                employer=source.source,
                title=title,
                url=absolute_url,
                source_url=source.url,
                matched_terms=matched_terms,
                notes=notes,
            ),
        )

    limitations = [limitation_if_empty] if not raw_urls and limitation_if_empty else []
    return Coverage(
        source=source.source,
        source_url=source.url,
        discovery_mode=source.discovery_mode,
        cadence_group=source.cadence_group,
        last_checked=source.last_checked,
        due_today=False,
        status="complete",
        listing_pages_scanned=1,
        search_terms_tried=terms,
        result_pages_scanned="filtered_links=1",
        direct_job_pages_opened=0,
        enumerated_jobs=len(raw_urls),
        matched_jobs=len(candidates_by_url),
        limitations=limitations,
        candidates=list(candidates_by_url.values()),
    )


def discover_cybernetica_teamdash(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    return discover_filtered_html_links(
        source,
        terms,
        timeout_seconds,
        lambda url: "cyber.teamdash.com/p/job/" in url,
        notes="Enumerated through Teamdash links on the Cybernetica careers page",
        limitation_if_empty="No Teamdash job links were visible on the Cybernetica careers page.",
    )


def discover_secunet_jobboard(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    pattern = re.compile(r"^https://jobs\.secunet\.com/.+-j\d+\.html$")
    return discover_filtered_html_links(
        source,
        terms,
        timeout_seconds,
        lambda url: bool(pattern.match(url)),
        notes="Enumerated through direct secunet job-detail links",
        limitation_if_empty="No secunet job-detail links matching the standard job pattern were visible.",
    )


SOURCES = [
    SourceAdapter(modes=("html", "icims_html"), discover=discover_html),
    SourceAdapter(modes=("cybernetica_teamdash",), discover=discover_cybernetica_teamdash),
    SourceAdapter(modes=("secunet_jobboard",), discover=discover_secunet_jobboard),
]
