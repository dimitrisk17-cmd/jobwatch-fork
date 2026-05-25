"""Generic and filtered static HTML discovery providers."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from html import unescape
from urllib.parse import urlencode, urljoin, urlparse

from discover import helpers, http
from discover.core import Candidate, Coverage, SourceConfig
from discover.registry import SourceAdapter


LIFEATSPOTIFY_API_ROOT = "https://api.lifeatspotify.com/wp-json/animal/v1"
LIFEATSPOTIFY_DETAIL_ROOT = "https://www.lifeatspotify.com/jobs"

HARMAN_JOBSEARCH_HOST = "jobsearch.harman.com"
HARMAN_JOBSEARCH_JOBDETAIL_RE = re.compile(
    r"^https://jobsearch\.harman\.com/[^/]+/careers/JobDetail/[^/]+/\d+$"
)

JOBVITE_HOST = "jobs.jobvite.com"
JOBVITE_JOB_ROW_RE = re.compile(
    r'<a\s+href="(?P<href>/[^"]+/job/[^"]+)"[^>]*>\s*'
    r'<div\s+class="jv-job-list-name">\s*(?P<title>[^<]+?)\s*</div>\s*'
    r'(?:<div\s+class="jv-job-id">\s*(?P<reqid>[^<]*?)\s*</div>\s*)?'
    r'<div\s+class="[^"]*\bjv-job-list-location\b[^"]*">\s*(?P<location>.*?)\s*</div>',
    re.DOTALL,
)
JOBVITE_TASK_HEADINGS = (
    "Responsibilities",
    "Key Responsibilities",
    "Your Responsibilities",
    "What You'll Do",
    "What You Will Do",
    "What Youll Do",
    "What You'll Be Doing",
    "Job Description",
    "Position Summary",
    "Position Overview",
    "Role Summary",
    "The Role",
    "About the Role",
    "Your Role",
    "Your Mission",
    "Job Summary",
)
JOBVITE_QUALIFICATION_HEADINGS = (
    "Qualifications",
    "Requirements",
    "Required Qualifications",
    "Required Skills",
    "Minimum Qualifications",
    "Preferred Qualifications",
    "Basic Qualifications",
    "What You Bring",
    "What You'll Bring",
    "What You Will Bring",
    "What We're Looking For",
    "Who You Are",
    "You Have",
    "You'll Need",
    "What You'll Need",
)
JOBVITE_COMPENSATION_HEADINGS = (
    "Compensation",
    "Pay Range",
    "Salary Range",
    "Total Rewards",
)
JOBVITE_DETAIL_STOP_HEADINGS = (
    *JOBVITE_TASK_HEADINGS,
    *JOBVITE_QUALIFICATION_HEADINGS,
    *JOBVITE_COMPENSATION_HEADINGS,
    "About Us",
    "About the Company",
    "About Xperi",
    "Benefits",
    "Equal Opportunity",
    "Equal Employment Opportunity",
    "EEO Statement",
    "Apply",
    "Apply Now",
    "Apply for this Job",
)
JOBVITE_COMPENSATION_MARKERS = (
    "salary range",
    "pay range",
    "compensation",
    "base pay",
    "hourly rate",
)

DOVER_HOST = "app.dover.com"
DOVER_API_ROOT = "https://app.dover.com/api/v1/careers-page"
DOVER_DETAIL_ROOT = "https://app.dover.com/dover/careers"
DOVER_CAREERS_PATH_RE = re.compile(
    r"^/(?:[^/]+/)?careers/(?P<id>[0-9a-fA-F-]{36})/?$"
)

DEMANT_RSS_ENDPOINT = "https://careers.demant.com/services/rss/job/"
DEMANT_TITLE_LOCATION_RE = re.compile(r"\s*\(([^()]+)\)\s*$")

SENNHEISER_JOBS_HOST = "jobs.sennheiser.com"
SENNHEISER_RSS_ENDPOINT = "https://jobs.sennheiser.com/services/rss/job/"
SENNHEISER_TITLE_LOCATION_RE = re.compile(r"\s*\(([^()]+)\)\s*$")

TEAMTAILOR_HOSTS = {"www.rolandcareers.com", "rolandcareers.com"}
TEAMTAILOR_FEED_PATH = "/jobs.json"

ULTIPRO_HOST = "recruiting2.ultipro.com"
ULTIPRO_BOARD_PATH_RE = re.compile(
    r"^/(?P<tenant>[^/]+)/JobBoard/(?P<board>[0-9a-fA-F-]+)/?",
)
ULTIPRO_PAGE_SIZE = 100
ULTIPRO_MAX_PAGES = 10

ALPHATHETA_HOSTS = {"alphatheta.com", "www.alphatheta.com"}
ALPHATHETA_NO_OPENINGS_MARKERS = (
    "no open positions",
    "no positions available",
)


KRISP_HOST = "krisp.ai"
KRISP_JOB_PATH_RE = re.compile(r"^/jobs/[^/]+/?$")
KRISP_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
KRISP_REMOTE_TOKENS = ("On-site", "Onsite", "Hybrid", "Remote")
KRISP_TASK_HEADINGS = (
    "What you'll do",
    "What you will do",
    "Your Responsibilities",
    "Responsibilities",
    "Key Responsibilities",
    "The Role",
    "About the Role",
    "Your Role",
    "What you do",
    "Day-to-day",
    "Your day-to-day",
)
KRISP_QUALIFICATION_HEADINGS = (
    "What we are looking for",
    "What we're looking for",
    "What we look for",
    "Requirements",
    "Qualifications",
    "Required Qualifications",
    "Required Skills",
    "Your Profile",
    "About You",
    "Who You Are",
    "What You Bring",
)
KRISP_DETAIL_STOP_HEADINGS = (
    *KRISP_TASK_HEADINGS,
    *KRISP_QUALIFICATION_HEADINGS,
    "How to apply",
    "Apply",
    "Apply now",
    "About us",
    "About Krisp",
    "Benefits",
    "What we offer",
    "We offer",
    "Why join us",
    "Equal Opportunity",
    "Krisp is an Equal Opportunity Employer",
    "Krisp is an Equal Opportunity Employer:",
)


BAMBOOHR_HOST_SUFFIX = ".bamboohr.com"
BAMBOOHR_TASK_HEADINGS = (
    "Overview",
    "Role Overview",
    "About the Role",
    "About this Role",
    "The Role",
    "Your Role",
    "Position Summary",
    "Position Overview",
    "Job Description",
    "Job Summary",
    "Job Purpose",
    "Summary",
    "Responsibilities",
    "Key Responsibilities",
    "What You'll Do",
    "What You Will Do",
    "What Youll Do",
    "What You'll Be Doing",
    "Your Mission",
    "Your Responsibilities",
)
BAMBOOHR_QUALIFICATION_HEADINGS = (
    "Qualifications",
    "Requirements",
    "Required Qualifications",
    "Required Skills",
    "Minimum Qualifications",
    "Preferred Qualifications",
    "Basic Qualifications",
    "Skills & Requirements",
    "What You Bring",
    "What You'll Bring",
    "What You Will Bring",
    "What We're Looking For",
    "Who You Are",
    "You Have",
    "You'll Need",
    "What You'll Need",
)
BAMBOOHR_COMPENSATION_HEADINGS = (
    "Compensation",
    "Pay Range",
    "Salary Range",
    "Total Rewards",
)
BAMBOOHR_DETAIL_STOP_HEADINGS = (
    *BAMBOOHR_TASK_HEADINGS,
    *BAMBOOHR_QUALIFICATION_HEADINGS,
    *BAMBOOHR_COMPENSATION_HEADINGS,
    "About Us",
    "About the Company",
    "Benefits",
    "Perks",
    "Perks & Benefits",
    "Equal Opportunity",
    "Equal Employment Opportunity",
    "EEO Statement",
    "Apply",
)
BAMBOOHR_COMPENSATION_MARKERS = (
    "salary range",
    "pay range",
    "compensation",
    "base pay",
    "hourly rate",
)


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
        "careers",
        "career",
        "view openings",
        "view all openings",
        "see openings",
        "see all openings",
        "browse openings",
        "current openings",
        "open positions",
        "view open positions",
        "see open positions",
        "open roles",
        "view open roles",
        "view jobs",
        "view all jobs",
        "see jobs",
        "see all jobs",
        "all jobs",
        "browse jobs",
        "explore opportunities",
        "explore careers",
        "view all",
        "see all",
    }:
        return True
    parsed = urlparse(href)
    if parsed.path in ("", "/") and "locale=" in parsed.query.lower():
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
    host = (urlparse(source.url).hostname or "").lower()
    if "lifeatspotify.com" in host:
        return discover_lifeatspotify_jobs(source, terms, timeout_seconds)
    if host == HARMAN_JOBSEARCH_HOST:
        return discover_harman_jobsearch_jobs(source, terms, timeout_seconds)
    if host == JOBVITE_HOST:
        return discover_jobvite_jobs(source, terms, timeout_seconds)
    if host == DOVER_HOST:
        return discover_dover_jobs(source, terms, timeout_seconds)
    if host == "demant.com" or host.endswith(".demant.com"):
        return discover_demant_successfactors(source, terms, timeout_seconds)
    if host == SENNHEISER_JOBS_HOST:
        return discover_sennheiser_jobs(source, terms, timeout_seconds)
    if host in TEAMTAILOR_HOSTS:
        return discover_teamtailor_jobs(source, terms, timeout_seconds)
    if host == ULTIPRO_HOST:
        return discover_ultipro_jobs(source, terms, timeout_seconds)
    if host == KRISP_HOST:
        return discover_krisp_jobs(source, terms, timeout_seconds)
    if host.endswith(BAMBOOHR_HOST_SUFFIX):
        return discover_bamboohr_jobs(source, terms, timeout_seconds)
    html = http.fetch_text(source.url, timeout_seconds)
    parser = helpers.LinkCollector()
    parser.feed(html)
    if host in ALPHATHETA_HOSTS:
        visible_text = " ".join(helpers.extract_visible_text_lines_from_html(html)).lower()
        if any(marker in visible_text for marker in ALPHATHETA_NO_OPENINGS_MARKERS):
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
                matched_jobs=0,
                limitations=["AlphaTheta career page reports no open positions"],
                candidates=[],
            )
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


def _dover_careers_id(url: str) -> str | None:
    path = urlparse(url).path or ""
    match = DOVER_CAREERS_PATH_RE.match(path)
    return match.group("id") if match else None


def _dover_job_location(job: dict) -> str:
    parts: list[str] = []
    for entry in job.get("locations") or []:
        if not isinstance(entry, dict):
            continue
        name = unescape(str(entry.get("name") or "")).strip()
        if name:
            parts.append(name)
    return "; ".join(parts) or "unknown"


def discover_dover_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    careers_id = _dover_careers_id(source.url)
    if not careers_id:
        return Coverage(
            source=source.source,
            source_url=source.url,
            discovery_mode=source.discovery_mode,
            cadence_group=source.cadence_group,
            last_checked=source.last_checked,
            due_today=False,
            status="failed",
            listing_pages_scanned="unknown",
            search_terms_tried=terms,
            result_pages_scanned="unknown",
            direct_job_pages_opened=0,
            enumerated_jobs=0,
            matched_jobs=0,
            limitations=[f"Could not extract Dover careers id from URL: {source.url}"],
            candidates=[],
        )

    jobs_endpoint = f"{DOVER_API_ROOT}/{careers_id}/jobs"
    payload = http.fetch_json(jobs_endpoint, timeout_seconds)
    jobs = payload.get("results", []) if isinstance(payload, dict) else []
    candidates_by_url: dict[str, Candidate] = {}

    for job in jobs:
        if not isinstance(job, dict):
            continue
        if not job.get("is_published"):
            continue
        if job.get("is_sample"):
            continue
        job_id = str(job.get("id") or "").strip()
        title = helpers.normalize_whitespace(unescape(str(job.get("title") or ""))) or "unknown"
        if not job_id:
            continue
        location = _dover_job_location(job)
        searchable_text = f"{title} {location}"
        matched_terms = sorted(set(helpers.match_terms(searchable_text, terms)))
        if not helpers.should_keep_candidate(title, matched_terms, searchable_text):
            continue
        helpers.merge_candidate(
            candidates_by_url,
            Candidate(
                employer=source.source,
                title=title,
                url=f"{DOVER_DETAIL_ROOT}/{careers_id}/{job_id}",
                source_url=source.url,
                location=location,
                matched_terms=matched_terms,
                notes="Enumerated through Dover careers-page API",
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
        direct_job_pages_opened=0,
        enumerated_jobs=len(jobs),
        matched_jobs=len(candidates_by_url),
        limitations=[],
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


def discover_harman_jobsearch_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    return discover_filtered_html_links(
        source,
        terms,
        timeout_seconds,
        lambda url: bool(HARMAN_JOBSEARCH_JOBDETAIL_RE.match(url)),
        notes="Enumerated through direct Harman careers (Avature) JobDetail links",
        limitation_if_empty="No Harman careers JobDetail links matching the standard Avature pattern were visible.",
    )


def extract_jobvite_detail_sections(detail_html: str) -> dict[str, str]:
    detail_text = "\n".join(helpers.extract_visible_text_lines_from_html(detail_html))
    tasks = helpers.extract_visible_text_section(
        detail_text,
        JOBVITE_TASK_HEADINGS,
        JOBVITE_DETAIL_STOP_HEADINGS,
    )
    qualifications = helpers.extract_visible_text_section(
        detail_text,
        JOBVITE_QUALIFICATION_HEADINGS,
        JOBVITE_DETAIL_STOP_HEADINGS,
    )
    compensation_section = helpers.extract_visible_text_section(
        detail_text,
        JOBVITE_COMPENSATION_HEADINGS,
        JOBVITE_DETAIL_STOP_HEADINGS,
    )
    compensation = compensation_section or helpers.extract_visible_text_marker_snippet(
        detail_text,
        JOBVITE_COMPENSATION_MARKERS,
        JOBVITE_DETAIL_STOP_HEADINGS,
    )
    return {
        "tasks": tasks,
        "qualifications": qualifications,
        "compensation": compensation,
    }


def build_jobvite_detail_note_parts(sections: dict[str, str]) -> list[str]:
    parts: list[str] = []
    if sections.get("tasks"):
        parts.append(f"Tasks: {helpers.truncate_text(sections['tasks'], 260)}")
    if sections.get("qualifications"):
        parts.append(f"Qualifications: {helpers.truncate_text(sections['qualifications'], 260)}")
    if sections.get("compensation"):
        parts.append(f"Compensation: {helpers.truncate_text(sections['compensation'], 200)}")
    return parts


def discover_jobvite_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    html = http.fetch_text(source.url, timeout_seconds)
    candidates_by_url: dict[str, Candidate] = {}
    enumerated = 0
    for match in JOBVITE_JOB_ROW_RE.finditer(html):
        enumerated += 1
        href = match.group("href")
        title = helpers.normalize_whitespace(unescape(match.group("title") or "")) or "unknown"
        reqid = helpers.normalize_whitespace(unescape(match.group("reqid") or ""))
        location = helpers.normalize_whitespace(
            unescape(re.sub(r"<[^>]+>", " ", match.group("location") or ""))
        ) or "unknown"
        absolute_url = helpers.normalize_url_without_fragment(urljoin(source.url, href))
        searchable_text = " ".join(part for part in (title, reqid, location, absolute_url) if part)
        matched_terms = sorted(set(helpers.match_terms(searchable_text, terms)))
        if not helpers.should_keep_candidate(title, matched_terms, searchable_text):
            continue
        note_parts = ["Enumerated through Jobvite careers listing HTML"]
        if reqid:
            note_parts.append(reqid)
        helpers.merge_candidate(
            candidates_by_url,
            Candidate(
                employer=source.source,
                title=title,
                url=absolute_url,
                source_url=source.url,
                location=location,
                matched_terms=matched_terms,
                notes="; ".join(note_parts),
            ),
        )
    limitations: list[str] = []
    if enumerated == 0:
        limitations.append("No Jobvite job rows matched the standard listing markup.")
    direct_job_pages_opened = 0
    for candidate_url, candidate in candidates_by_url.items():
        try:
            detail_html = http.fetch_text(candidate_url, timeout_seconds)
        except Exception:
            limitations.append(f"Detail fetch failed for {candidate_url}")
            continue
        direct_job_pages_opened += 1
        sections = extract_jobvite_detail_sections(detail_html)
        detail_parts = build_jobvite_detail_note_parts(sections)
        if detail_parts:
            candidate.notes = "; ".join(part for part in [candidate.notes, *detail_parts] if part)
    return Coverage(
        source=source.source,
        source_url=source.url,
        discovery_mode=source.discovery_mode,
        cadence_group=source.cadence_group,
        last_checked=source.last_checked,
        due_today=False,
        status="partial" if limitations else "complete",
        listing_pages_scanned=1,
        search_terms_tried=terms,
        result_pages_scanned="local_filter=1",
        direct_job_pages_opened=direct_job_pages_opened,
        enumerated_jobs=enumerated,
        matched_jobs=len(candidates_by_url),
        limitations=limitations,
        candidates=list(candidates_by_url.values()),
    )


def _demant_split_title_location(raw_title: str) -> tuple[str, str]:
    text = helpers.normalize_whitespace(unescape(raw_title or ""))
    match = DEMANT_TITLE_LOCATION_RE.search(text)
    if not match:
        return text or "unknown", "unknown"
    location = helpers.normalize_whitespace(match.group(1)) or "unknown"
    title = helpers.normalize_whitespace(text[: match.start()]) or "unknown"
    return title, location


def discover_demant_successfactors(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    candidates_by_url: dict[str, Candidate] = {}
    seen_item_links: set[str] = set()
    enumerated = 0
    listing_pages_scanned = 0
    limitations: list[str] = []

    for term in terms:
        feed_url = f"{DEMANT_RSS_ENDPOINT}?{urlencode({'locale': 'en_GB', 'keywords': term})}"
        try:
            xml_text = http.fetch_text(feed_url, timeout_seconds)
            listing_pages_scanned += 1
        except Exception as exc:
            limitations.append(f"RSS fetch failed for {term!r}: {type(exc).__name__}: {exc}")
            continue
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            limitations.append(f"RSS parse failed for {term!r}: {exc}")
            continue
        for item in root.findall(".//item"):
            link_elem = item.find("link")
            title_elem = item.find("title")
            description_elem = item.find("description")
            raw_link = (link_elem.text or "").strip() if link_elem is not None else ""
            raw_title = (title_elem.text or "") if title_elem is not None else ""
            raw_description = (description_elem.text or "") if description_elem is not None else ""
            if not raw_link or not raw_title:
                continue
            absolute_url = helpers.normalize_url_without_fragment(raw_link)
            if absolute_url in seen_item_links:
                continue
            seen_item_links.add(absolute_url)
            enumerated += 1
            title, location = _demant_split_title_location(raw_title)
            description_text = " ".join(helpers.extract_visible_text_lines_from_html(raw_description))
            searchable_text = " ".join(part for part in (title, location, description_text) if part)
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
                    location=location,
                    matched_terms=matched_terms,
                    notes="Enumerated through Demant SAP SuccessFactors RSS search",
                ),
            )

    status = "complete" if listing_pages_scanned > 0 else "failed"
    return Coverage(
        source=source.source,
        source_url=source.url,
        discovery_mode=source.discovery_mode,
        cadence_group=source.cadence_group,
        last_checked=source.last_checked,
        due_today=False,
        status=status,
        listing_pages_scanned=listing_pages_scanned,
        search_terms_tried=terms,
        result_pages_scanned=f"rss_search={listing_pages_scanned}",
        direct_job_pages_opened=0,
        enumerated_jobs=enumerated,
        matched_jobs=len(candidates_by_url),
        limitations=limitations,
        candidates=list(candidates_by_url.values()),
    )


def _teamtailor_location(job_posting: dict) -> str:
    raw_locations = job_posting.get("jobLocation") if isinstance(job_posting, dict) else None
    if isinstance(raw_locations, dict):
        raw_locations = [raw_locations]
    if not isinstance(raw_locations, list):
        return "unknown"
    parts: list[str] = []
    for entry in raw_locations:
        if not isinstance(entry, dict):
            continue
        address = entry.get("address") if isinstance(entry.get("address"), dict) else {}
        locality = unescape(str(address.get("addressLocality") or "")).strip()
        region = unescape(str(address.get("addressRegion") or "")).strip()
        country = unescape(str(address.get("addressCountry") or "")).strip()
        components = [component for component in (locality, region, country) if component]
        if components:
            parts.append(", ".join(components))
    return "; ".join(parts) or "unknown"


def discover_teamtailor_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    feed_url = urljoin(source.url, TEAMTAILOR_FEED_PATH)
    payload = http.fetch_json(feed_url, timeout_seconds)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    candidates_by_url: dict[str, Candidate] = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        url = helpers.normalize_whitespace(str(item.get("url") or ""))
        if not url:
            continue
        title = helpers.normalize_whitespace(unescape(str(item.get("title") or ""))) or "unknown"
        job_posting = item.get("_jobposting") if isinstance(item.get("_jobposting"), dict) else {}
        location = _teamtailor_location(job_posting)
        description_html = item.get("content_html") or (
            job_posting.get("description") if isinstance(job_posting, dict) else ""
        ) or ""
        description_text = " ".join(helpers.extract_visible_text_lines_from_html(description_html))
        searchable_text = " ".join(part for part in (title, location, description_text) if part)
        matched_terms = sorted(set(helpers.match_terms(searchable_text, terms)))
        if not helpers.should_keep_candidate(title, matched_terms, searchable_text):
            continue
        note_parts = ["Enumerated through Teamtailor jobs.json feed"]
        if description_text:
            note_parts.append(f"Description: {helpers.truncate_text(description_text, 260)}")
        helpers.merge_candidate(
            candidates_by_url,
            Candidate(
                employer=source.source,
                title=title,
                url=helpers.normalize_url_without_fragment(url),
                source_url=source.url,
                location=location,
                matched_terms=matched_terms,
                notes="; ".join(note_parts),
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
        direct_job_pages_opened=0,
        enumerated_jobs=len(items),
        matched_jobs=len(candidates_by_url),
        limitations=[],
        candidates=list(candidates_by_url.values()),
    )


def _krisp_clean_title(detail_html: str, fallback: str) -> str:
    match = KRISP_TITLE_RE.search(detail_html or "")
    if not match:
        return fallback or "unknown"
    raw = helpers.normalize_whitespace(unescape(match.group(1)))
    if "|" in raw:
        raw = raw.split("|", 1)[0].strip()
    return raw or (fallback or "unknown")


def _krisp_location_and_remote(listing_text: str, clean_title: str) -> tuple[str, str]:
    text = helpers.normalize_whitespace(listing_text or "")
    title = helpers.normalize_whitespace(clean_title or "")
    if title and text.startswith(title):
        remainder = text[len(title):].strip()
    else:
        remainder = text
    if not remainder:
        return "unknown", "unknown"
    for token in KRISP_REMOTE_TOKENS:
        if remainder.endswith(" " + token):
            location = remainder[: -len(token)].strip()
            return location or "unknown", token
        if remainder == token:
            return "unknown", token
    return remainder, "unknown"


def extract_krisp_detail_sections(detail_html: str) -> dict[str, str]:
    detail_text = "\n".join(helpers.extract_visible_text_lines_from_html(detail_html or ""))
    tasks = helpers.extract_visible_text_section(
        detail_text,
        KRISP_TASK_HEADINGS,
        KRISP_DETAIL_STOP_HEADINGS,
    )
    qualifications = helpers.extract_visible_text_section(
        detail_text,
        KRISP_QUALIFICATION_HEADINGS,
        KRISP_DETAIL_STOP_HEADINGS,
    )
    return {"tasks": tasks, "qualifications": qualifications}


def build_krisp_detail_note_parts(sections: dict[str, str]) -> list[str]:
    parts: list[str] = []
    if sections.get("tasks"):
        parts.append(f"Tasks: {helpers.truncate_text(sections['tasks'], 260)}")
    if sections.get("qualifications"):
        parts.append(f"Qualifications: {helpers.truncate_text(sections['qualifications'], 260)}")
    return parts


def discover_krisp_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    careers_html = http.fetch_text(source.url, timeout_seconds)
    parser = helpers.LinkCollector()
    parser.feed(careers_html)

    job_link_texts: dict[str, str] = {}
    for link in parser.links:
        absolute_url = helpers.normalize_url_without_fragment(urljoin(source.url, link["href"]))
        parsed = urlparse(absolute_url)
        if (parsed.hostname or "").lower() != KRISP_HOST:
            continue
        path = parsed.path if parsed.path.endswith("/") else parsed.path + "/"
        if not KRISP_JOB_PATH_RE.match(path):
            continue
        if absolute_url in job_link_texts:
            continue
        job_link_texts[absolute_url] = helpers.normalize_whitespace(link["text"])

    candidates_by_url: dict[str, Candidate] = {}
    direct_job_pages_opened = 0
    limitations: list[str] = []

    for absolute_url, listing_text in job_link_texts.items():
        clean_title = listing_text or "unknown"
        location = "unknown"
        remote = "unknown"
        note_parts: list[str] = ["Enumerated through krisp.ai careers HTML"]
        try:
            detail_html = http.fetch_text(absolute_url, timeout_seconds)
        except Exception as exc:
            limitations.append(f"Could not fetch detail for {absolute_url}: {type(exc).__name__}")
            detail_html = ""
        if detail_html:
            direct_job_pages_opened += 1
            clean_title = _krisp_clean_title(detail_html, listing_text)
            location, remote = _krisp_location_and_remote(listing_text, clean_title)
            sections = extract_krisp_detail_sections(detail_html)
            note_parts.extend(build_krisp_detail_note_parts(sections))
        searchable_text = " ".join(part for part in (clean_title, listing_text, absolute_url) if part)
        matched_terms = sorted(set(helpers.match_terms(searchable_text, terms)))
        helpers.merge_candidate(
            candidates_by_url,
            Candidate(
                employer=source.source,
                title=clean_title,
                url=absolute_url,
                source_url=source.url,
                location=location,
                remote=remote,
                matched_terms=matched_terms,
                notes="; ".join(part for part in note_parts if part),
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
        enumerated_jobs=len(job_link_texts),
        matched_jobs=len(candidates_by_url),
        limitations=limitations,
        candidates=list(candidates_by_url.values()),
    )


def _sennheiser_split_title_location(raw_title: str) -> tuple[str, str]:
    text = helpers.normalize_whitespace(unescape(raw_title or ""))
    match = SENNHEISER_TITLE_LOCATION_RE.search(text)
    if not match:
        return text or "unknown", "unknown"
    location = helpers.normalize_whitespace(match.group(1)) or "unknown"
    title = helpers.normalize_whitespace(text[: match.start()]) or "unknown"
    return title, location


def discover_sennheiser_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    candidates_by_url: dict[str, Candidate] = {}
    seen_item_links: set[str] = set()
    enumerated = 0
    listing_pages_scanned = 0
    limitations: list[str] = []

    feed_url = f"{SENNHEISER_RSS_ENDPOINT}?{urlencode({'locale': 'en_US'})}"
    try:
        xml_text = http.fetch_text(feed_url, timeout_seconds)
        listing_pages_scanned += 1
    except Exception as exc:
        limitations.append(f"RSS fetch failed: {type(exc).__name__}: {exc}")
        xml_text = ""
    root = None
    if xml_text:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            limitations.append(f"RSS parse failed: {exc}")
    if root is not None:
        for item in root.findall(".//item"):
            link_elem = item.find("link")
            title_elem = item.find("title")
            description_elem = item.find("description")
            raw_link = (link_elem.text or "").strip() if link_elem is not None else ""
            raw_title = (title_elem.text or "") if title_elem is not None else ""
            raw_description = (description_elem.text or "") if description_elem is not None else ""
            if not raw_link or not raw_title:
                continue
            absolute_url = helpers.normalize_url_without_fragment(raw_link)
            if absolute_url in seen_item_links:
                continue
            seen_item_links.add(absolute_url)
            enumerated += 1
            title, location = _sennheiser_split_title_location(raw_title)
            description_text = " ".join(helpers.extract_visible_text_lines_from_html(raw_description))
            searchable_text = " ".join(part for part in (title, location, description_text) if part)
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
                    location=location,
                    matched_terms=matched_terms,
                    notes="Enumerated through Sennheiser SAP/Jobs2Web RSS feed",
                ),
            )

    status = "complete" if listing_pages_scanned > 0 else "failed"
    return Coverage(
        source=source.source,
        source_url=source.url,
        discovery_mode=source.discovery_mode,
        cadence_group=source.cadence_group,
        last_checked=source.last_checked,
        due_today=False,
        status=status,
        listing_pages_scanned=listing_pages_scanned,
        search_terms_tried=terms,
        result_pages_scanned=f"rss_feed={listing_pages_scanned}",
        direct_job_pages_opened=0,
        enumerated_jobs=enumerated,
        matched_jobs=len(candidates_by_url),
        limitations=limitations,
        candidates=list(candidates_by_url.values()),
    )


def _ultipro_board_ids(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    if (parsed.hostname or "").lower() != ULTIPRO_HOST:
        return None
    match = ULTIPRO_BOARD_PATH_RE.match(parsed.path or "")
    if not match:
        return None
    return match.group("tenant"), match.group("board")


def _ultipro_location(opportunity: dict) -> str:
    parts: list[str] = []
    for entry in opportunity.get("Locations") or []:
        if not isinstance(entry, dict):
            continue
        name = helpers.normalize_whitespace(unescape(str(entry.get("LocalizedName") or "")))
        address = entry.get("Address") if isinstance(entry.get("Address"), dict) else None
        city = ""
        state = ""
        country = ""
        if address:
            city = helpers.normalize_whitespace(unescape(str(address.get("City") or "")))
            state_obj = address.get("State") if isinstance(address.get("State"), dict) else None
            country_obj = address.get("Country") if isinstance(address.get("Country"), dict) else None
            if state_obj:
                state = helpers.normalize_whitespace(unescape(str(state_obj.get("Code") or state_obj.get("Name") or "")))
            if country_obj:
                country = helpers.normalize_whitespace(unescape(str(country_obj.get("Code") or country_obj.get("Name") or "")))
        address_parts = ", ".join(part for part in (city, state, country) if part)
        if name and address_parts and name != address_parts:
            parts.append(f"{name} ({address_parts})")
        elif address_parts:
            parts.append(address_parts)
        elif name:
            parts.append(name)
    return "; ".join(parts) or "unknown"


def _ultipro_notes(opportunity: dict) -> str:
    note_parts = ["Enumerated through UltiPro/UKG recruiting JSON API"]
    requisition = helpers.normalize_whitespace(unescape(str(opportunity.get("RequisitionNumber") or "")))
    if requisition:
        note_parts.append(f"Requisition: {requisition}")
    category = helpers.normalize_whitespace(unescape(str(opportunity.get("JobCategoryName") or "")))
    if category:
        note_parts.append(f"Category: {category}")
    full_time = opportunity.get("FullTime")
    if isinstance(full_time, bool):
        note_parts.append("Employment type: Full-time" if full_time else "Employment type: Part-time")
    posted = helpers.normalize_whitespace(str(opportunity.get("PostedDate") or ""))
    if posted:
        note_parts.append(f"Posted: {posted}")
    brief = helpers.normalize_whitespace(unescape(str(opportunity.get("BriefDescription") or "")))
    if brief:
        note_parts.append(f"Description: {helpers.truncate_text(brief, 320)}")
    return "; ".join(note_parts)


def discover_ultipro_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    board_ids = _ultipro_board_ids(source.url)
    if not board_ids:
        return Coverage(
            source=source.source,
            source_url=source.url,
            discovery_mode=source.discovery_mode,
            cadence_group=source.cadence_group,
            last_checked=source.last_checked,
            due_today=False,
            status="failed",
            listing_pages_scanned="unknown",
            search_terms_tried=terms,
            result_pages_scanned="unknown",
            direct_job_pages_opened=0,
            enumerated_jobs=0,
            matched_jobs=0,
            limitations=[f"Could not parse UltiPro tenant/board from URL: {source.url}"],
            candidates=[],
        )
    tenant, board = board_ids
    base = f"https://{ULTIPRO_HOST}/{tenant}/JobBoard/{board}"
    search_endpoint = f"{base}/JobBoardView/LoadSearchResults"
    detail_root = f"{base}/OpportunityDetail"

    candidates_by_url: dict[str, Candidate] = {}
    enumerated = 0
    pages_scanned = 0
    limitations: list[str] = []

    for page_index in range(ULTIPRO_MAX_PAGES):
        payload = {
            "opportunitySearch": {
                "Top": ULTIPRO_PAGE_SIZE,
                "Skip": page_index * ULTIPRO_PAGE_SIZE,
                "QueryString": "",
                "OrderBy": [{"Value": "postedDateDesc"}],
            }
        }
        try:
            response = http.post_json(search_endpoint, payload, timeout_seconds)
            pages_scanned += 1
        except Exception as exc:
            limitations.append(f"LoadSearchResults failed at skip={page_index * ULTIPRO_PAGE_SIZE}: {type(exc).__name__}: {exc}")
            break
        opportunities = response.get("opportunities") if isinstance(response, dict) else None
        if not isinstance(opportunities, list) or not opportunities:
            break
        enumerated += len(opportunities)
        for opportunity in opportunities:
            if not isinstance(opportunity, dict):
                continue
            job_id = str(opportunity.get("Id") or "").strip()
            if not job_id:
                continue
            title = helpers.normalize_whitespace(unescape(str(opportunity.get("Title") or ""))) or "unknown"
            location = _ultipro_location(opportunity)
            brief = helpers.normalize_whitespace(unescape(str(opportunity.get("BriefDescription") or "")))
            category = helpers.normalize_whitespace(unescape(str(opportunity.get("JobCategoryName") or "")))
            searchable_text = " ".join(part for part in (title, location, category, brief) if part)
            matched_terms = sorted(set(helpers.match_terms(searchable_text, terms)))
            if not helpers.should_keep_candidate(title, matched_terms, searchable_text):
                continue
            detail_url = f"{detail_root}?opportunityId={job_id}"
            helpers.merge_candidate(
                candidates_by_url,
                Candidate(
                    employer=source.source,
                    title=title,
                    url=detail_url,
                    source_url=source.url,
                    location=location,
                    remote=helpers.infer_remote_status(title, location, brief),
                    matched_terms=matched_terms,
                    notes=_ultipro_notes(opportunity),
                ),
            )
        total_count = response.get("totalCount") if isinstance(response, dict) else None
        if isinstance(total_count, int) and (page_index + 1) * ULTIPRO_PAGE_SIZE >= total_count:
            break
        if len(opportunities) < ULTIPRO_PAGE_SIZE:
            break

    status = "complete" if pages_scanned > 0 else "failed"
    return Coverage(
        source=source.source,
        source_url=source.url,
        discovery_mode=source.discovery_mode,
        cadence_group=source.cadence_group,
        last_checked=source.last_checked,
        due_today=False,
        status=status,
        listing_pages_scanned=pages_scanned,
        search_terms_tried=terms,
        result_pages_scanned=f"ultipro_pages={pages_scanned}",
        direct_job_pages_opened=0,
        enumerated_jobs=enumerated,
        matched_jobs=len(candidates_by_url),
        limitations=limitations,
        candidates=list(candidates_by_url.values()),
    )



def _bamboohr_tenant(source_url: str) -> str:
    host = (urlparse(source_url).hostname or "").lower()
    if not host.endswith(BAMBOOHR_HOST_SUFFIX):
        return ""
    return host[: -len(BAMBOOHR_HOST_SUFFIX)]


def _bamboohr_format_location(job: dict) -> str:
    parts: list[str] = []
    ats_location = job.get("atsLocation") if isinstance(job, dict) else None
    if isinstance(ats_location, dict):
        for key in ("city", "state", "province", "country"):
            value = ats_location.get(key)
            if isinstance(value, str):
                cleaned = helpers.normalize_whitespace(unescape(value))
                if cleaned and cleaned not in parts:
                    parts.append(cleaned)
    if not parts:
        legacy_location = job.get("location") if isinstance(job, dict) else None
        if isinstance(legacy_location, dict):
            for key in ("city", "state", "addressCountry"):
                value = legacy_location.get(key)
                if isinstance(value, str):
                    cleaned = helpers.normalize_whitespace(unescape(value))
                    if cleaned and cleaned not in parts:
                        parts.append(cleaned)
    return ", ".join(parts) or "unknown"


def extract_bamboohr_detail_sections(description_html: str) -> dict[str, str]:
    detail_text = "\n".join(helpers.extract_visible_text_lines_from_html(description_html or ""))
    tasks = helpers.extract_visible_text_section(
        detail_text,
        BAMBOOHR_TASK_HEADINGS,
        BAMBOOHR_DETAIL_STOP_HEADINGS,
    )
    qualifications = helpers.extract_visible_text_section(
        detail_text,
        BAMBOOHR_QUALIFICATION_HEADINGS,
        BAMBOOHR_DETAIL_STOP_HEADINGS,
    )
    compensation = helpers.extract_visible_text_section(
        detail_text,
        BAMBOOHR_COMPENSATION_HEADINGS,
        BAMBOOHR_DETAIL_STOP_HEADINGS,
    ) or helpers.extract_visible_text_marker_snippet(
        detail_text,
        BAMBOOHR_COMPENSATION_MARKERS,
        BAMBOOHR_DETAIL_STOP_HEADINGS,
    )
    description_fallback = ""
    if not tasks and not qualifications:
        description_fallback = " ".join(helpers.split_visible_lines(detail_text))
    return {
        "tasks": tasks,
        "qualifications": qualifications,
        "compensation": compensation,
        "description": description_fallback,
    }


def build_bamboohr_detail_note_parts(sections: dict[str, str], department: str, employment_status: str) -> list[str]:
    parts: list[str] = []
    if department:
        parts.append(f"Department: {department}")
    if employment_status:
        parts.append(f"Employment: {employment_status}")
    if sections.get("tasks"):
        parts.append(f"Tasks: {helpers.truncate_text(sections['tasks'], 260)}")
    if sections.get("qualifications"):
        parts.append(f"Qualifications: {helpers.truncate_text(sections['qualifications'], 260)}")
    if sections.get("compensation"):
        parts.append(f"Compensation: {helpers.truncate_text(sections['compensation'], 200)}")
    if sections.get("description") and not sections.get("tasks") and not sections.get("qualifications"):
        parts.append(f"Description: {helpers.truncate_text(sections['description'], 260)}")
    return parts


def discover_bamboohr_jobs(source: SourceConfig, terms: list[str], timeout_seconds: int) -> Coverage:
    tenant = _bamboohr_tenant(source.url)
    if not tenant:
        return Coverage(
            source=source.source,
            source_url=source.url,
            discovery_mode=source.discovery_mode,
            cadence_group=source.cadence_group,
            last_checked=source.last_checked,
            due_today=False,
            status="failed",
            listing_pages_scanned="unknown",
            search_terms_tried=terms,
            result_pages_scanned="unknown",
            direct_job_pages_opened=0,
            enumerated_jobs=0,
            matched_jobs=0,
            limitations=[f"Could not derive BambooHR tenant from URL: {source.url}"],
            candidates=[],
        )

    list_endpoint = f"https://{tenant}{BAMBOOHR_HOST_SUFFIX}/careers/list"
    detail_root = f"https://{tenant}{BAMBOOHR_HOST_SUFFIX}/careers"
    payload = http.fetch_json(list_endpoint, timeout_seconds)
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
        title = helpers.normalize_whitespace(unescape(str(job.get("jobOpeningName") or ""))) or "unknown"
        department = helpers.normalize_whitespace(unescape(str(job.get("departmentLabel") or "")))
        employment_status = helpers.normalize_whitespace(unescape(str(job.get("employmentStatusLabel") or "")))
        location = _bamboohr_format_location(job)
        share_url = helpers.normalize_url_without_fragment(f"{detail_root}/{job_id}")

        detail_url = f"{detail_root}/{job_id}/detail"
        description_html = ""
        try:
            detail_payload = http.fetch_json(detail_url, timeout_seconds)
            direct_job_pages_opened += 1
        except Exception as exc:
            limitations.append(f"Could not fetch detail for {share_url}: {type(exc).__name__}: {exc}")
            detail_payload = None
        if isinstance(detail_payload, dict):
            job_opening = (detail_payload.get("result") or {}).get("jobOpening") if isinstance(detail_payload.get("result"), dict) else None
            if isinstance(job_opening, dict):
                description_html = str(job_opening.get("description") or "")
                detail_location = _bamboohr_format_location(job_opening)
                if detail_location and detail_location != "unknown":
                    location = detail_location
                detail_title = helpers.normalize_whitespace(unescape(str(job_opening.get("jobOpeningName") or "")))
                if detail_title:
                    title = detail_title
                if not department:
                    department = helpers.normalize_whitespace(unescape(str(job_opening.get("departmentLabel") or "")))
                if not employment_status:
                    employment_status = helpers.normalize_whitespace(unescape(str(job_opening.get("employmentStatusLabel") or "")))

        description_text = " ".join(helpers.extract_visible_text_lines_from_html(description_html))
        searchable_text = " ".join(part for part in (title, department, employment_status, location, description_text, share_url) if part)
        matched_terms = sorted(set(helpers.match_terms(searchable_text, terms)))

        sections = extract_bamboohr_detail_sections(description_html)
        note_parts = ["Enumerated through BambooHR careers API"]
        note_parts.extend(build_bamboohr_detail_note_parts(sections, department, employment_status))

        helpers.merge_candidate(
            candidates_by_url,
            Candidate(
                employer=source.source,
                title=title,
                url=share_url,
                source_url=source.url,
                location=location,
                matched_terms=matched_terms,
                notes="; ".join(part for part in note_parts if part),
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


SOURCES = [
    SourceAdapter(modes=("html", "icims_html"), discover=discover_html),
    SourceAdapter(modes=("cybernetica_teamdash",), discover=discover_cybernetica_teamdash),
    SourceAdapter(modes=("secunet_jobboard",), discover=discover_secunet_jobboard),
]
