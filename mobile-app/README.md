# OLX Monitor — apka (Expo Go)

Prosta apka React Native/Expo, która pobiera listę ogłoszeń z API bota
(`api_server.py`) i pokazuje je na liście. Nie zastępuje powiadomień
Telegram — to dodatkowy podgląd.

## Uruchomienie lokalnie (na komputerze)

Wymaga Node.js (LTS) zainstalowanego na komputerze — **nie** na Mikrusie.

```bash
cd mobile-app
npm install
```

1. Otwórz `config.js` i ustaw:
   - `API_URL` — publiczny adres Twojego API, np.
     `https://sandra278.mikrus.xyz:PORT_API/ads` (patrz główny README,
     sekcja o wystawieniu API na Mikrusie),
   - `API_TOKEN` — ten sam token, co `API_TOKEN` w `.env` bota.
2. Uruchom serwer deweloperski Expo:
   ```bash
   npx expo start
   ```
3. Zainstaluj na telefonie aplikację **Expo Go** (App Store / Google Play).
4. Zeskanuj kod QR wyświetlony w terminalu/przeglądarce aplikacją Expo Go
   (na Androidzie wprost z aplikacji Expo Go, na iOS aparatem telefonu).
5. Apka otworzy się w Expo Go i pobierze bieżącą listę ogłoszeń z Twojego
   API na Mikrusie. Pociągnięcie listy w dół odświeża ją ręcznie, dodatkowo
   apka odpytuje API automatycznie co `POLL_INTERVAL_SECONDS` (domyślnie 30 s).

Telefon i komputer nie muszą być w tej samej sieci — apka łączy się
bezpośrednio do publicznego adresu API na Mikrusie, a nie do komputera.
