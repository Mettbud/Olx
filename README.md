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

## 6. Działanie 24/7 na Mikrusie

Mikrus to zwykły VPS (KVM, Debian) z dostępem `root` przez SSH, więc całość
stawiamy standardowo przez `systemd` — żaden port nie musi być otwierany,
bot tylko łączy się *wychodząco* do olx.pl i api.telegram.org.

1. **Połącz się przez SSH** — dane (adres, port, hasło/klucz) znajdziesz w
   panelu Mikrusa:
   ```bash
   ssh -p <TWÓJ_PORT> root@<numer>.mikrus.xyz
   ```

2. **Zainstaluj zależności systemowe** (Mikrus bazuje na Debianie):
   ```bash
   apt update && apt install -y python3-venv python3-pip git
   ```

3. **Wgraj projekt** — np. sklonuj repo albo prześlij plikami przez `scp`:
   ```bash
   cd /root
   git clone <adres-twojego-repo> Olx
   cd Olx
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   nano .env   # wklej token, chat_id i 4 linki wyszukiwania
   deactivate
   ```

4. **Utwórz usługę systemd:**
   ```bash
   cat > /etc/systemd/system/olx-monitor.service <<'EOF'
   [Unit]
   Description=OLX Telegram Monitor
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/root/Olx
   ExecStart=/root/Olx/venv/bin/python3 /root/Olx/olx_monitor.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF
   ```
   (zmienne z `.env` skrypt wczyta sam przez `python-dotenv` — nie trzeba
   dodawać `EnvironmentFile`, wystarczy że plik `.env` leży w
   `WorkingDirectory`).

5. **Włącz i wystartuj:**
   ```bash
   systemctl daemon-reload
   systemctl enable --now olx-monitor
   systemctl status olx-monitor
   journalctl -u olx-monitor -f   # podgląd logów na żywo
   ```

Usługa wystartuje automatycznie po restarcie serwera (również po restarcie
Mikrusa z panelu) i sama podniesie się po ewentualnym błędzie
(`Restart=always`). 1 GB RAM-u dostępny na najtańszych planach Mikrusa jest
całkowicie wystarczający — skrypt zajmuje przy pracy ok. 30-80 MB.

### Uwaga dot. limitów Mikrusa

Na niektórych (zwłaszcza najtańszych) planach Mikrusa obowiązuje limit
transferu/czasu CPU oraz możliwe okresowe „usypianie” słabo wykorzystanych
usług widocznych w panelu — ale dotyczy to głównie usług sieciowych
wystawionych na porty. Proces w tle działający przez `systemd` i korzystający
tylko z wychodzących połączeń HTTPS zwykle nie jest tym ograniczany. Jeśli
zauważysz, że bot przestaje odpowiadać, sprawdź `systemctl status
olx-monitor` i limity w panelu Mikrusa.

## 7. Podgląd ogłoszeń w apce mobilnej (Expo Go)

Oprócz powiadomień na Telegramie, bot może wystawić proste REST API
(`api_server.py`), z którego korzysta apka w `mobile-app/` uruchamiana w
**Expo Go** na telefonie. Expo Go nie hostuje backendu — apka tylko łączy
się do API działającego na Mikrusie.

### 7.1. Wystaw API na Mikrusie

1. Dopisz w swoim `.env` na serwerze losowy `API_TOKEN` (patrz
   `.env.example`) — zabezpiecza listę ogłoszeń przed dostępem osób z
   zewnątrz.
2. W panelu Mikrusa, w zakładce **Porty**, przydziel sobie jeden publiczny
   port (np. `20278`) przekierowany na port lokalny, na którym postawisz
   API (np. `8000`). Zanotuj przydzielony publiczny port — to on trafi do
   `API_URL` w apce.
3. Dodaj drugą usługę systemd, obok `olx-monitor`:
   ```bash
   cat > /etc/systemd/system/olx-api.service <<'EOF'
   [Unit]
   Description=OLX Monitor API
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/root/Olx
   ExecStart=/root/Olx/venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF

   systemctl daemon-reload
   systemctl enable --now olx-api
   systemctl status olx-api
   ```
4. Sprawdź, czy działa (z dowolnego komputera):
   ```
   https://sandra278.mikrus.xyz:<PUBLICZNY_PORT_Z_PANELU>/health
   ```
   powinno zwrócić `{"status":"ok"}`.

### 7.2. Uruchom apkę w Expo Go

Pełna instrukcja: [`mobile-app/README.md`](mobile-app/README.md). W skrócie:
na komputerze (nie na Mikrusie) `cd mobile-app && npm install`, wpisz w
`config.js` adres z kroku 7.1 i ten sam `API_TOKEN`, uruchom `npx expo
start`, a na telefonie w aplikacji **Expo Go** zeskanuj kod QR.

## Uwagi

- Interwał 200 s jest ustawiony tak, by nie prowokować blokad IP / Cloudflare
  ze strony OLX. Zmniejszanie go zwiększa ryzyko bana.
- OLX może zmienić strukturę HTML swojej strony — jeśli selektory w
  `parse_listings()` przestaną działać, trzeba je zaktualizować (sprawdź
  aktualne atrybuty `data-cy`/`data-testid` w narzędziach deweloperskich
  przeglądarki).
- Pełne dane ogłoszeń (dla Telegrama i dla API/apki) są trzymane w
  `ads_store.json` — nie commituj tego pliku (jest w `.gitignore`).
- API (`api_server.py`) i apka w Expo Go są opcjonalne — bot działa (i
  wysyła Telegram) samodzielnie, bez nich.
