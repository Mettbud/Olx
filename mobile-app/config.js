// Ustawienia połączenia z API bota OLX (api_server.py działającego na Mikrusie).
// Podmień na swoje wartości — adres serwera i ten sam API_TOKEN, co w pliku .env.
export const API_URL = "https://sandra278.mikrus.xyz:PORT_API/ads";
export const API_TOKEN = "wymysl-dlugi-losowy-ciag-znakow";

// Co ile sekund apka odświeża listę w tle (podczas gdy ekran jest otwarty).
// Ustawione na 200 s, tak samo jak CHECK_INTERVAL bota — częstsze odpytywanie
// nie ma sensu, bo dane na serwerze i tak nie zmienią się szybciej.
export const POLL_INTERVAL_SECONDS = 200;
