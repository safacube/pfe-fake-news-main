from typing import Tuple, Dict
import requests
from bs4 import BeautifulSoup
from readability import Document

try:  # optional but helpful extractor
    import trafilatura
except Exception:  # noqa: BLE001
    trafilatura = None

HEADERS = {
    'User-Agent': 'FakeNewsLab/1.0 (+https://example.com)',
    'Accept-Language': 'en-US,en;q=0.9',
}


def _clean_paragraphs(paragraphs):
    seen = set()
    cleaned = []
    for p in paragraphs:
        text = p.get_text(strip=True) if hasattr(p, 'get_text') else str(p).strip()
        if not text or len(text) < 40:  # skip tiny/snippet lines
            continue
        if text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


def _extract_readability(html):
    doc = Document(html)
    summary_html = doc.summary(html_partial=True)
    soup = BeautifulSoup(summary_html, 'html.parser')
    return _clean_paragraphs(soup.find_all('p'))


def _extract_semantic(html):
    soup = BeautifulSoup(html, 'html.parser')
    candidates = soup.select('article p, main p, div[itemprop="articleBody"] p')
    cleaned = _clean_paragraphs(candidates)
    if cleaned:
        return cleaned
    return _clean_paragraphs(soup.find_all('p'))


def _extract_trafilatura(html, url: str) -> str:
    if not trafilatura:
        return ''
    try:
        text = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            with_metadata=False,
        )
        return (text or '').strip()
    except Exception:  # noqa: BLE001
        return ''


def fetch_article_text(url: str) -> Tuple[str, Dict]:
    meta: Dict = {'url': url}
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        meta['status_code'] = resp.status_code
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        meta['error'] = f'HTTP error: {exc}'
        return '', meta

    html = resp.text
    try:
        meta['title'] = Document(html).short_title()
    except Exception:
        meta['title'] = None

    # Try multiple extraction strategies
    paragraphs = _extract_readability(html)
    if paragraphs:
        return '\n\n'.join(paragraphs), meta

    trafil_text = _extract_trafilatura(html, url)
    if trafil_text:
        return trafil_text, meta

    paragraphs = _extract_semantic(html)
    if paragraphs:
        return '\n\n'.join(paragraphs), meta

    meta['error'] = meta.get('error') or 'No readable paragraphs found; site may be script-heavy or blocked.'
    return '', meta
