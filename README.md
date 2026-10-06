# OLX Monitor → Telegram

Skrypt sprawdza cyklicznie (domyślnie co 200 s) do 4 linków wyszukiwania OLX
i wysyła powiadomienie na Telegram, gdy pojawi się nowe ogłoszenie.

## 1. Instalacja

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. Utworzenie bota w Telegramie (@BotFather)

1. W Telegramie wyszukaj **@BotFather** i otwórz z nim czat.
2. Wyślij komendę `/newbot`.
3. Podaj nazwę bota (dowolna, widoczna w kontaktach) oraz unikalny login
   kończący się na `bot` (np. `moj_olx_monitor_bot`).
4. BotFather odpowie tokenem w formacie `123456789:ABC...` — wklej go jako
   `TELEGRAM_BOT_TOKEN` w pliku `.env`.

## 3. Pobranie CHAT_ID

1. Wyślij do swojego nowego bota jakąkolwiek wiadomość (np. „test”) — bot musi
   mieć z Tobą rozpoczętą rozmowę.
2. W przeglądarce otwórz:
   `https://api.telegram.org/bot<TWÓJ_TOKEN>/getUpdates`
3. W odpowiedzi JSON znajdź `"chat":{"id": 123456789, ...}` — ta liczba to
   Twój `TELEGRAM_CHAT_ID`. Wklej ją do `.env`.
   (Alternatywnie: napisz do bota **@userinfobot**, który natychmiast odpowie
   Twoim ID.)

## 4. Linki wyszukiwania OLX

1. Wejdź na olx.pl, wyszukaj to, co ma być monitorowane (kategoria, filtry,
   lokalizacja), posortuj po „Najnowsze”.
2. Skopiuj adres URL z przeglądarki.
3. Powtórz dla pozostałych wyszukiwań (do 4 sztuk) i wklej wszystkie,
   oddzielone przecinkami, jako `SEARCH_URLS` w `.env`.

## 5. Uruchomienie

```bash
python3 olx_monitor.py
```

Przy pierwszym uruchomieniu bot **nie** wysyła powiadomień o ogłoszeniach,
które już istnieją — zapisuje je jako znane (plik `seen_ads.json`). Od
kolejnego przejścia (po ~200 s) powiadomienia dostaniesz tylko o faktycznie
nowych ogłoszeniach.

## 6. Działanie 24/7 na VPS (systemd)

Na serwerze (Hetzner, Mikrus, AWS Free Tier itd.) po wgraniu projektu i
instalacji zależności utwórz usługę systemd:

```ini
# /etc/systemd/system/olx-monitor.service
[Unit]
Description=OLX Telegram Monitor
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/user/Olx
ExecStart=/home/user/Olx/venv/bin/python3 /home/user/Olx/olx_monitor.py
Restart=always
RestartSec=10
EnvironmentFile=/home/user/Olx/.env

[Install]
WantedBy=multi-user.target
```

Następnie:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now olx-monitor
sudo systemctl status olx-monitor
journalctl -u olx-monitor -f   # podgląd logów na żywo
```

Usługa wystartuje przy każdym restarcie serwera i sama się podniesie po
ewentualnym błędzie (`Restart=always`).

## Uwagi

- Interwał 200 s jest ustawiony tak, by nie prowokować blokad IP / Cloudflare
  ze strony OLX. Zmniejszanie go zwiększa ryzyko bana.
- OLX może zmienić strukturę HTML swojej strony — jeśli selektory w
  `parse_listings()` przestaną działać, trzeba je zaktualizować (sprawdź
  aktualne atrybuty `data-cy`/`data-testid` w narzędziach deweloperskich
  przeglądarki).
- Stan „widzianych” ogłoszeń jest trzymany w `seen_ads.json` — nie commituj
  tego pliku (jest w `.gitignore`).
