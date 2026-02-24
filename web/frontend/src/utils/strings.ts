/** German UI strings */
export const UI = {
  app_title: 'BandWacht',
  app_subtitle: 'Bandüberwachung',

  // Navigation
  nav_dashboard: 'Dashboard',
  nav_config: 'Konfiguration',
  nav_history: 'Logbuch',

  // Dashboard
  dash_spectrum: 'Spektrum',
  dash_events: 'Letzte Erkennungen',
  dash_instances: 'SDR-Instanzen',
  dash_no_instances: 'Keine SDR-Instanzen konfiguriert.',
  dash_connected: 'Verbunden',
  dash_disconnected: 'Getrennt',
  dash_start: 'Starten',
  dash_stop: 'Stoppen',

  // Config
  cfg_instances: 'SDR-Instanzen',
  cfg_targets: 'Überwachungsziele',
  cfg_detection: 'Erkennungsparameter',
  cfg_notifications: 'Benachrichtigungen',
  cfg_add_instance: 'Instanz hinzufügen',
  cfg_add_target: 'Ziel hinzufügen',
  cfg_name: 'Name',
  cfg_url: 'URL',
  cfg_enabled: 'Aktiviert',
  cfg_freq: 'Frequenz (MHz)',
  cfg_bandwidth: 'Bandbreite (kHz)',
  cfg_label: 'Bezeichnung',
  cfg_threshold: 'Schwellwert (dB)',
  cfg_hysteresis: 'Hysterese (dB)',
  cfg_hold_time: 'Haltezeit (s)',
  cfg_cooldown: 'Abklingzeit (s)',
  cfg_record: 'Aufnahme aktiviert',
  cfg_scan_full: 'Vollband-Scan',
  cfg_save: 'Speichern',
  cfg_cancel: 'Abbrechen',
  cfg_delete: 'Löschen',
  cfg_edit: 'Bearbeiten',
  cfg_test: 'Test senden',
  cfg_profile: 'Profil',
  cfg_fetch_profiles: 'Profile laden',
  cfg_no_profiles: 'Keine Profile verfügbar',

  // History
  hist_title: 'Ereignis-Logbuch',
  hist_filters: 'Filter',
  hist_export_csv: 'CSV exportieren',
  hist_stats: 'Statistiken',
  hist_no_events: 'Keine Ereignisse gefunden.',
  hist_total: 'Gesamt',
  hist_today: 'Heute',
  hist_week: 'Diese Woche',
  hist_top_freq: 'Häufigste Frequenzen',
  hist_hourly: 'Stündliche Verteilung',

  // Auth
  auth_login: 'Anmelden',
  auth_username: 'Benutzername',
  auth_password: 'Passwort',
  auth_login_title: 'Anmeldung',
  auth_logout: 'Abmelden',
  auth_error: 'Falscher Benutzername oder Passwort',

  // Common
  loading: 'Laden...',
  error: 'Fehler',
  confirm_delete: 'Wirklich löschen?',
  yes: 'Ja',
  no: 'Nein',
  no_data: 'Keine Daten',
} as const
