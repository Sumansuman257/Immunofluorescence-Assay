from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests


EUROPE_PMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "ThePipetteSolutionBloggerAgent/0.1 (+https://thepipettesolution.blogspot.com)"


@dataclass(frozen=True)
class LiteratureResult:
    title: str
    authors: str
    year: str
    journal: str
    doi: str | None
    pmid: str | None
    abstract: str
    url: str

    @property
    def citation(self) -> str:
        authors = self.authors or "Unknown authors"
        year = self.year or "n.d."
        journal = self.journal or "Unknown source"
        title = self.title.rstrip(".")
        suffix = f" https://doi.org/{self.doi}" if self.doi else f" {self.url}"
        return f"{authors} ({year}). {title}. {journal}.{suffix}"


@dataclass(frozen=True)
class ImageResult:
    title: str
    url: str
    page_url: str
    license_name: str
    artist: str

    @property
    def attribution_html(self) -> str:
        title = html.escape(self.title.replace("File:", ""))
        artist = html.escape(_strip_tags(self.artist) or "Wikimedia Commons contributor")
        license_name = html.escape(_strip_tags(self.license_name) or "license listed on source page")
        page_url = html.escape(self.page_url, quote=True)
        return f'{title}. Credit: {artist}, <a href="{page_url}">{license_name}</a>.'


def search_literature(topic: str, max_results: int = 7) -> list[LiteratureResult]:
    """Search Europe PMC for literature relevant to a blog topic."""

    terms = _topic_terms(topic)
    seen: set[str] = set()
    candidates: list[tuple[int, LiteratureResult]] = []

    for query in _candidate_queries(topic):
        for item in _fetch_results(query, page_size=max_results * 3):
            paper = _result_to_literature(item)
            if not paper:
                continue
            keys = _dedupe_keys(paper)
            if keys & seen:
                continue
            seen.update(keys)
            score = _score_paper(paper, terms)
            if score <= 0:
                continue
            candidates.append((score, paper))
        if len(candidates) >= max_results:
            break

    candidates.sort(key=lambda scored: scored[0], reverse=True)
    return [paper for _, paper in candidates[:max_results]]


def search_images(topic: str, max_results: int = 2) -> list[ImageResult]:
    """Search Wikimedia Commons for embeddable illustrative images."""

    params: dict[str, Any] = {
        "action": "query",
        "generator": "search",
        "gsrnamespace": "6",
        "gsrsearch": f"{topic} molecular biology",
        "gsrlimit": str(max_results * 3),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "format": "json",
    }
    response = requests.get(
        WIKIMEDIA_API_URL,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})

    images: list[ImageResult] = []
    for page in pages.values():
        imageinfo = (page.get("imageinfo") or [{}])[0]
        url = imageinfo.get("url")
        if not url or not _is_supported_image(url):
            continue
        metadata = imageinfo.get("extmetadata", {})
        images.append(
            ImageResult(
                title=page.get("title", "Wikimedia Commons image"),
                url=url,
                page_url=imageinfo.get("descriptionurl", url),
                license_name=_metadata_value(metadata, "LicenseShortName"),
                artist=_metadata_value(metadata, "Artist"),
            )
        )
        if len(images) >= max_results:
            break
    return images


def _fallback_publication_url(item: dict[str, Any]) -> str:
    if item.get("pmid"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{item['pmid']}/"
    if item.get("pmcid"):
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{item['pmcid']}/"
    return "https://europepmc.org/"


def _candidate_queries(topic: str) -> list[str]:
    topic = _clean_text(topic)
    terms = _topic_terms(topic)
    domain = '("molecular cloning" OR cloning OR plasmid OR vector OR "viral vector" OR virology OR sequencing)'

    queries = [f'TITLE_ABS:"{topic}" AND {domain}']
    phrases = _topic_phrases(terms)
    if phrases:
        phrase_clauses = " OR ".join(f'TITLE_ABS:"{phrase}"' for phrase in phrases[:5])
        queries.append(f"({phrase_clauses}) AND {domain}")
    if len(terms) >= 3:
        queries.append("(" + " AND ".join(f"TITLE_ABS:{term}" for term in terms[:4]) + f") AND {domain}")
    if len(terms) >= 2:
        queries.append("(" + " AND ".join(terms[:3]) + f") AND {domain}")

    return queries


def _topic_terms(topic: str) -> list[str]:
    stopwords = {
        "about",
        "after",
        "before",
        "into",
        "from",
        "with",
        "that",
        "this",
        "these",
        "those",
        "and",
        "for",
        "the",
        "in",
        "of",
        "to",
        "a",
        "an",
    }
    terms = []
    for term in re.findall(r"[A-Za-z0-9-]+", topic.lower()):
        if len(term) < 3 or term in stopwords:
            continue
        terms.append(term)
    return terms


def _topic_phrases(terms: list[str]) -> list[str]:
    phrases: list[str] = []
    for size in (3, 2):
        for index in range(0, max(len(terms) - size + 1, 0)):
            phrases.append(" ".join(terms[index : index + size]))
    return phrases


def _fetch_results(query: str, page_size: int) -> list[dict[str, Any]]:
    params = {
        "query": query,
        "format": "json",
        "pageSize": str(page_size),
        "resultType": "core",
    }
    response = requests.get(
        EUROPE_PMC_SEARCH_URL,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    response.raise_for_status()
    return response.json().get("resultList", {}).get("result", [])


def _result_to_literature(item: dict[str, Any]) -> LiteratureResult | None:
    title = _clean_text(item.get("title"))
    abstract = _clean_text(item.get("abstractText"))
    if not title:
        return None
    doi = item.get("doi") or None
    pmid = item.get("pmid") or None
    url = f"https://doi.org/{doi}" if doi else _fallback_publication_url(item)
    return LiteratureResult(
        title=title,
        authors=_clean_text(item.get("authorString")),
        year=_clean_text(item.get("pubYear")),
        journal=_journal_title(item),
        doi=doi,
        pmid=pmid,
        abstract=abstract,
        url=url,
    )


def _score_paper(paper: LiteratureResult, terms: list[str]) -> int:
    title = paper.title.lower()
    abstract = paper.abstract.lower()
    score = 0
    for term in terms:
        if term in title:
            score += 4
        elif term in abstract:
            score += 1
    for domain_term in ("cloning", "plasmid", "vector", "sequencing", "virology", "virus"):
        if domain_term in title:
            score += 2
        elif domain_term in abstract:
            score += 1
    return score


def _dedupe_keys(paper: LiteratureResult) -> set[str]:
    keys = {_normalize_key(paper.title)}
    if paper.doi:
        keys.add(f"doi:{paper.doi.lower()}")
    if paper.pmid:
        keys.add(f"pmid:{paper.pmid.lower()}")
    return {key for key in keys if key}


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _journal_title(item: dict[str, Any]) -> str:
    journal = _clean_text(item.get("journalTitle"))
    if journal:
        return journal
    journal_info = item.get("journalInfo") or {}
    nested = journal_info.get("journal") or {}
    return _clean_text(nested.get("title") or journal_info.get("journalTitle"))


def _clean_text(value: Any) -> str:
    if not value:
        return ""
    text = _strip_tags(str(value))
    return re.sub(r"\s+", " ", text).strip()


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


def _metadata_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key, {})
    if isinstance(value, dict):
        return value.get("value", "") or ""
    return str(value or "")


def _is_supported_image(url: str) -> bool:
    extension = url.split("?")[0].rsplit(".", 1)[-1].lower()
    return extension in {"jpg", "jpeg", "png", "gif", "webp", "svg"}


def debug_search_url(topic: str) -> str:
    query = _candidate_queries(topic)[0]
    return f"{EUROPE_PMC_SEARCH_URL}?{urlencode({'query': query, 'format': 'json'})}"
