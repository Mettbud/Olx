#!/usr/bin/env python3
"""OLX search monitor — polls a list of OLX search-result URLs and pushes
new listings to a Telegram chat."""

import json
import logging
import os
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SEEN_FILE = BASE_DIR / "seen_ads.json"

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "200"))

SEARCH_URLS = [
    url.strip()
    for url in os.environ.get("SEARCH_URLS", "").split(",")
    if url.strip()
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("olx_monitor")


def load_seen() -> set:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            log.warning("Nie udało się wczytać %s, zaczynam od pustej listy", SEEN_FILE)
    return set()


def save_seen(seen: set) -> None:
    SEEN_FILE.write_text(json.dumps(sorted(seen)), encoding="utf-8")


def parse_listings(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    listings = []

    for card in soup.select("div[data-cy='l-card']"):
        ad_id = card.get("id") or card.get("data-id")
        if not ad_id:
            continue

        link_tag = card.select_one("a")
        href = link_tag.get("href") if link_tag else None
        if not href:
            continue
        url = href if href.startswith("http") else f"https://www.olx.pl{href}"

        title_tag = card.select_one("h4, h6")
        title = title_tag.get_text(strip=True) if title_tag else "(brak tytułu)"

        price_tag = card.select_one("p[data-testid='ad-price']")
        price = price_tag.get_text(strip=True) if price_tag else "brak ceny"

        location_tag = card.select_one("p[data-testid='location-date']")
        location = location_tag.get_text(strip=True) if location_tag else "brak lokalizacji"

        listings.append(
            {
                "id": str(ad_id),
                "title": title,
                "price": price,
                "location": location,
                "url": url,
            }
        )

    return listings


def fetch_listings(search_url: str) -> list[dict]:
    response = requests.get(search_url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return parse_listings(response.text)


def send_telegram_message(text: str) -> None:
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    response = requests.post(api_url, data=payload, timeout=20)
    if not response.ok:
        log.error("Błąd wysyłki Telegrama: %s %s", response.status_code, response.text)


def format_message(ad: dict) -> str:
    return (
        f"🆕 <b>{ad['title']}</b>\n"
        f"💰 {ad['price']}\n"
        f"📍 {ad['location']}\n"
        f"🔗 {ad['url']}"
    )


def check_all_urls(seen: set, notify: bool) -> set:
    for search_url in SEARCH_URLS:
        try:
            listings = fetch_listings(search_url)
        except requests.RequestException as exc:
            log.warning("Nie udało się pobrać %s: %s", search_url, exc)
            continue

        new_ads = [ad for ad in listings if ad["id"] not in seen]
        for ad in new_ads:
            if notify:
                log.info("Nowe ogłoszenie: %s", ad["title"])
                send_telegram_message(format_message(ad))
            seen.add(ad["id"])

    return seen


def main() -> None:
    if not SEARCH_URLS:
        raise SystemExit("Brak zdefiniowanych linków w SEARCH_URLS (plik .env)")

    seen = load_seen()
    is_first_run = not seen
    log.info("Start monitorowania %d linków, interwał %ds", len(SEARCH_URLS), CHECK_INTERVAL)

    while True:
        try:
            # Przy pierwszym uruchomieniu (pusty seen_ads.json) tylko zapisujemy
            # istniejące ogłoszenia jako znane, bez wysyłania powiadomień —
            # inaczej bot zalałby czat wszystkimi aktualnymi wynikami.
            seen = check_all_urls(seen, notify=not is_first_run)
            save_seen(seen)
            if is_first_run:
                log.info("Pierwsze przejście zakończone — zapisano %d ogłoszeń jako znane", len(seen))
                is_first_run = False
        except Exception:
            log.exception("Nieoczekiwany błąd w pętli głównej")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
