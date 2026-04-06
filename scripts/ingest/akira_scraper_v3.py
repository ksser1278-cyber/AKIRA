"""
AKIRA Engine v3.0 - Multi-Source Scraper (Fixed)
Target: 10,000 unique songs
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import hashlib
import os
import sys
import unicodedata
import re
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force unbuffered output
def log(msg):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)


def normalize_name(name: str) -> str:
    """
    아티스트명 비교용 정규화:
    - 전각 → 반각 변환
    - 소문자로 통일
    - 공백·특수문자 제거
    """
    name = unicodedata.normalize('NFKC', name)   # 전각→반각
    name = name.lower()
    name = re.sub(r'[\s\-_\.\'\"\(\)&!?/\\]', '', name)
    return name


def is_artist_match(scraped_artist: str, target_name: str, target_name_jp: str = '') -> bool:
    """
    스크래핑된 아티스트명이 타겟 아티스트와 일치하는지 검증.
    정규화 후 부분 포함 여부까지 체크해 오탐을 최소화.
    """
    s = normalize_name(scraped_artist)
    t_en = normalize_name(target_name)
    t_jp = normalize_name(target_name_jp) if target_name_jp else ''

    if not s:
        return False

    # 완전 일치 or 한쪽이 다른 쪽을 포함 (그룹명 vs 솔로 활동명 등 대응)
    for target in filter(None, [t_en, t_jp]):
        if s == target or target in s or s in target:
            return True

    return False


class URLRegistry:
    """Persistent URL deduplication registry"""

    def __init__(self, path="data/url_registry.json"):
        self.path = path
        self.seen_urls = set()
        self.seen_hashes = set()
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seen_urls = set(data.get('urls', []))
                    self.seen_hashes = set(data.get('hashes', []))
                log(f"[*] Loaded registry: {len(self.seen_urls)} URLs, {len(self.seen_hashes)} hashes")
            except Exception:
                log("[*] Starting fresh registry")

    def save(self):
        os.makedirs(os.path.dirname(self.path) if os.path.dirname(self.path) else '.', exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump({
                'urls': list(self.seen_urls),
                'hashes': list(self.seen_hashes)
            }, f)

    def is_seen(self, url=None, lyrics=None):
        if url and url in self.seen_urls:
            return True
        if lyrics:
            h = self._hash(lyrics)
            if h in self.seen_hashes:
                return True
        return False

    def add(self, url, lyrics):
        self.seen_urls.add(url)
        self.seen_hashes.add(self._hash(lyrics))

    def _hash(self, text):
        normalized = text.replace('\n', '').replace(' ', '').strip()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    @property
    def count(self):
        return len(self.seen_urls)


class UtaNetScraper:
    """Scraper for uta-net.com"""

    BASE_URL = "https://www.uta-net.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en;q=0.9",
    }

    def __init__(self, registry: URLRegistry):
        self.registry = registry
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get_artist_songs(self, artist_name: str, strict_artist_filter: bool = True):
        """
        Search for artist and get all song URLs.

        strict_artist_filter=True 이면 검색 결과 행에서
        아티스트명이 일치하는 곡만 수집한다.
        """
        search_url = (
            f"{self.BASE_URL}/search/"
            f"?Keyword={requests.utils.quote(artist_name)}&Aession=1&x=0&y=0"
        )

        try:
            log(f"    Searching: {search_url[:80]}...")
            resp = self.session.get(search_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            song_urls = []

            if strict_artist_filter:
                # ── 방법 A: 검색 결과 테이블의 각 행에서
                #            아티스트 셀을 확인한 뒤 song 링크 수집 ──
                for row in soup.select('table tr, ul.song-list li, div.song-list-item'):
                    # 행 안에 아티스트명이 있는지 확인
                    row_text = row.get_text()
                    if not is_artist_match(row_text, artist_name):
                        continue
                    for link in row.select('a[href*="/song/"]'):
                        href = link.get('href', '')
                        if '/song/' in href:
                            full_url = f"{self.BASE_URL}{href}" if href.startswith('/') else href
                            if not self.registry.is_seen(url=full_url):
                                song_urls.append(full_url)

                # ── 방법 B: 방법 A로 아무것도 못 찾은 경우
                #            전체 song 링크 수집 후 나중에 가사 페이지에서 재검증 ──
                if not song_urls:
                    log(f"    [*] Row-level filter yielded 0 results, falling back to full scan")
                    for link in soup.select('a[href*="/song/"]'):
                        href = link.get('href', '')
                        if '/song/' in href:
                            full_url = f"{self.BASE_URL}{href}" if href.startswith('/') else href
                            if not self.registry.is_seen(url=full_url):
                                song_urls.append(full_url)
            else:
                # strict 필터 없이 전체 수집
                for link in soup.select('a[href*="/song/"]'):
                    href = link.get('href', '')
                    if '/song/' in href:
                        full_url = f"{self.BASE_URL}{href}" if href.startswith('/') else href
                        if not self.registry.is_seen(url=full_url):
                            song_urls.append(full_url)

            song_urls = list(set(song_urls))
            log(f"    Found {len(song_urls)} new song URLs")
            return song_urls

        except requests.exceptions.Timeout:
            log(f"    [!] Timeout on search")
            return []
        except Exception as e:
            log(f"    [!] Search error: {type(e).__name__}: {e}")
            return []

    def get_lyrics(self, url: str):
        """Fetch lyrics from a song page"""
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # ── 아티스트 파싱 (여러 셀렉터 시도) ──
            artist = ""
            for selector in [
                'h3.artist span[itemprop="name"]',
                'a[itemprop="byArtist"]',
                'a[href*="/artist/"]',
            ]:
                elem = soup.select_one(selector)
                if elem:
                    artist = elem.get_text(strip=True)
                    break
            if not artist:
                artist = "Unknown"

            # ── 제목 파싱 ──
            title = self._parse_title(soup, artist)

            # ── 가사 파싱 ──
            lyrics_elem = (
                soup.select_one('div#kashi_area')
                or soup.select_one('div.kashi_area')
                or soup.select_one('div.hiragana')
                or soup.select_one('[itemprop="lyrics"]')
            )
            if not lyrics_elem:
                return None

            lyrics = lyrics_elem.get_text('\n', strip=True)

            if len(lyrics) < 100:
                return None
            if self.registry.is_seen(lyrics=lyrics):
                return None

            return {
                'title': title or "Untitled",
                'artist': artist,
                'lyrics': lyrics,
                'url': url,
                'source': 'utanet',
                'scraped_at': datetime.now().isoformat()
            }

        except requests.exceptions.Timeout:
            return None
        except Exception:
            return None

    # ── 내부 헬퍼 ──────────────────────────────────────────────

    def _parse_title(self, soup: BeautifulSoup, artist: str) -> str:
        """
        제목 파싱을 별도 메서드로 분리.
        아티스트명을 알고 있으므로 더 정확하게 제거 가능.
        """
        # 1) <h2> 직접
        h2 = soup.select_one('h2')
        if h2:
            title = h2.get_text(strip=True)
            if title:
                return self._strip_artist_prefix(title, artist)

        # 2) <title> 태그
        page_title_elem = soup.select_one('title')
        if page_title_elem:
            raw = page_title_elem.get_text(strip=True)
            if '歌詞' in raw:
                # "アーティスト名 曲名 歌詞 - サイト名" 형식 대응
                title = raw.split('歌詞')[0].strip()
                return self._strip_artist_prefix(title, artist)

        # 3) og:title
        og = soup.select_one('meta[property="og:title"]')
        if og:
            raw = og.get('content', '')
            if '歌詞' in raw:
                title = raw.split('歌詞')[0].strip()
                return self._strip_artist_prefix(title, artist)

        return ""

    @staticmethod
    def _strip_artist_prefix(title: str, artist: str) -> str:
        """
        제목 앞에 아티스트명이 붙어 있으면 제거.
        단순 공백 split 대신 실제 아티스트명을 기준으로 제거.
        """
        if not artist or artist == "Unknown":
            return title

        # "아티스트명 " 으로 시작하면 제거
        prefix = artist + ' '
        if title.startswith(prefix):
            return title[len(prefix):].strip()

        # 정규화 비교로도 시도
        norm_title = normalize_name(title)
        norm_artist = normalize_name(artist)
        if norm_title.startswith(norm_artist):
            # 원본 title에서 artist 길이만큼 앞을 제거 (근사치)
            return title[len(artist):].strip()

        return title


class AkiraScraper:
    """Main scraper orchestrator"""

    def __init__(self, target_songs=10000):
        self.target = target_songs
        self.registry = URLRegistry()
        self.utanet = UtaNetScraper(self.registry)
        self.output_dir = "data/shards_v3"

    def run(self, artists):
        """Run scraping for all artists"""
        os.makedirs(self.output_dir, exist_ok=True)

        total_scraped = 0

        for idx, artist in enumerate(artists):
            if total_scraped >= self.target:
                log(f"\n[+] Target reached: {total_scraped} songs")
                break

            name = artist['name']
            log(f"\n[{idx+1}/{len(artists)}] Scraping: {name}")

            songs = self._scrape_artist_utanet(artist)

            if songs:
                safe_name = name.replace(' ', '_').replace('*', '').replace('/', '_')
                shard_path = os.path.join(self.output_dir, f"shard_{safe_name}.json")
                with open(shard_path, 'w', encoding='utf-8') as f:
                    json.dump(songs, f, ensure_ascii=False, indent=2)

                total_scraped += len(songs)
                log(f"    [+] Saved {len(songs)} songs (Total: {total_scraped})")

                if total_scraped % 100 == 0:
                    self.registry.save()

            time.sleep(2)

        self.registry.save()
        log(f"\n[+] Scraping complete. Total: {total_scraped} unique songs")
        return total_scraped

    def _scrape_artist_utanet(self, artist: dict):
        """
        아티스트 곡 스크래핑.
        가사 페이지에서 파싱한 아티스트명을 타겟과 비교해 무관한 곡 제거.
        """
        name = artist['name']
        name_jp = artist.get('name_jp', '')

        # URL 수집
        all_urls = list(self.utanet.get_artist_songs(name))

        # 영문명 결과가 부족할 때만 일본어명 재검색
        if name_jp and name_jp != name and len(all_urls) < 5:
            log(f"    Trying Japanese name: {name_jp}")
            all_urls += self.utanet.get_artist_songs(name_jp)

        all_urls = list(set(all_urls))

        songs = []
        skipped_mismatch = 0

        for i, url in enumerate(all_urls[:80]):
            data = self.utanet.get_lyrics(url)

            if data:
                # ── 핵심 수정: 가사 페이지의 아티스트명 검증 ──
                if not is_artist_match(data['artist'], name, name_jp):
                    skipped_mismatch += 1
                    log(f"    [skip] 아티스트 불일치: '{data['artist']}' ≠ '{name}'")
                    continue

                self.registry.add(url, data['lyrics'])
                songs.append(data)

                if (i + 1) % 10 == 0:
                    log(f"    Progress: {i+1}/{min(len(all_urls), 80)} "
                        f"({len(songs)} saved, {skipped_mismatch} skipped)")

            time.sleep(0.8)

        if skipped_mismatch:
            log(f"    [*] Total skipped (artist mismatch): {skipped_mismatch}")

        return songs


if __name__ == "__main__":
    from core.akira_artist_registry import get_all_artists

    artists = get_all_artists()
    log(f"[*] AKIRA v3 Scraper Starting")
    log(f"[*] Target: 10,000 songs")
    log(f"[*] Artists: {len(artists)}")
    log(f"[*] Output: data/shards_v3/")

    scraper = AkiraScraper(target_songs=10000)
    total = scraper.run(artists)

    log(f"\n{'='*40}")
    log(f"SCRAPING COMPLETE")
    log(f"Total Unique Songs: {total}")
    log(f"{'='*40}")
