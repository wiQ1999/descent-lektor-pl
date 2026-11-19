using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;
using UnityEngine.UI;

namespace LektorPL.Core
{
    /// <summary>
    /// Nakładka lektora w grze (próba): skróty klawiszowe, krótkie komunikaty, menu lektora i zgłoszenia błędów.
    ///
    /// Plugin nie trzyma ustawień: polecenia idą do companiona (zdarzenia <c>control</c> i <c>report</c> w dzienniku),
    /// a companion odsyła stan (tempo, wyciszenie, bieżąca kwestia, historia, kategorie, skróty), który nakładka rysuje.
    /// Menu i okno zgłoszenia to IMGUI; pod nimi leży przezroczysty obraz uGUI, żeby kliknięcia nie trafiały w planszę
    /// (gra sprawdza EventSystem.IsPointerOverGameObject). Gra ignoruje sterowanie kamerą przy wciśniętym Ctrl/Alt,
    /// więc domyślne skróty to Ctrl+klawisz.
    /// </summary>
    internal sealed class Overlay
    {
        private const float ToastSeconds = 2.5f;
        private const float VolumeSendGap = 0.25f;
        private static readonly string[] DefaultKeys =
        {
            "szybciej", "Ctrl+Equals, Ctrl+KeypadPlus", "wolniej", "Ctrl+Minus, Ctrl+KeypadMinus", "wycisz", "Ctrl+M",
            "powtorz", "Ctrl+R", "utnij", "Ctrl+S", "zglos", "Ctrl+B", "menu", "Ctrl+L",
        };
        private static readonly string[] Categories = { "glos", "zły głos", "wymowa", "zła wymowa", "cisza", "cisza (brak lektora)",
                                                        "uciecie", "ucięta kwestia", "mowca", "zły mówca", "inne", "inne" };
        private static readonly Dictionary<string, string> ToggleLabels = new Dictionary<string, string>
        {
            { "narracja", "Narracja" }, { "dialogi", "Dialogi postaci" }, { "komunikaty_questu", "Komunikaty zadania" },
            { "walka_teren", "Walka i teren" }, { "ui", "Interfejs i samouczek" }, { "okna_wyboru", "Odpowiedź po wyborze" },
            { "nagrody", "Nagrody" }, { "aktywacje", "Aktywacje wrogów" }, { "cele", "Cele misji" }, { "podroze", "Podróże" },
            { "miasto", "Miasto" }, { "opis_misji", "Opis misji na mapie" }, { "zdolnosci", "Okno ataku" },
        };

        private readonly EventLog _log;
        private readonly Sender _sender;
        private readonly string _reportsRoot;
        private readonly Dictionary<string, List<Hotkey>> _keys = new Dictionary<string, List<Hotkey>>();
        private readonly BarButton _bar;
        private Blocker _blocker;

        private object _state;
        private float _stateAt;
        private long _noticeSeen = -1;
        private string _toast;
        private float _toastUntil;

        private bool _menu;
        private Vector2 _scroll;
        private float _volume = -1f, _volumeSentAt, _volumeTouchedAt = -10f;

        // Zgłoszenie: zrzut w klatce _captureFrame (po zamknięciu menu), potem wybór kategorii.
        private int _captureFrame = -1;
        private long _reportToken;
        private string _reportDir, _reportShot;

        private GUIStyle _panel, _title, _text, _small, _button, _toastStyle, _section;
        private Texture2D _bg, _bar1, _bar2;

        public Overlay(EventLog log, Sender sender, string logDirectory)
        {
            _log = log;
            _sender = sender;
            _reportsRoot = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(logDirectory)) ?? ".", "zgloszenia");
            for (int i = 0; i < DefaultKeys.Length; i += 2)
                _keys[DefaultKeys[i]] = Hotkey.ParseList(DefaultKeys[i + 1]);
            sender.OnLine = OnLine;
            _bar = new BarButton(log, ToggleMenu);
        }

        public bool MenuOpen => _menu;
        private bool Connected => _sender.Connected && _state != null && Time.unscaledTime - _stateAt < 5f;
        private bool Choosing => _reportDir != null && _captureFrame >= 0 && Time.frameCount > _captureFrame;

        // ---------- stan od companiona ----------

        private void OnLine(string line)
        {
            object o = Json.Parse(line);
            if (Json.Str(o, "ev") != "state") return;
            _state = o;
            _stateAt = Time.unscaledTime;
            var keys = Json.Obj(o, "keys");
            if (keys != null)
                foreach (var kv in keys)
                    if (kv.Value is string s) _keys[kv.Key] = Hotkey.ParseList(s);
            var notice = Json.Obj(o, "notice");
            long id = (long)Json.Num(notice, "id", -1);
            if (_noticeSeen < 0)
                _noticeSeen = Math.Max(0, id);          // pierwszy stan po starcie: komunikat sprzed połączenia pomijamy
            else if (notice != null && id != _noticeSeen)
            {
                Toast(Json.Str(notice, "text"));
                _noticeSeen = id;
            }
        }

        private void Toast(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            _toast = text;
            _toastUntil = Time.unscaledTime + ToastSeconds;
        }

        // ---------- polecenia ----------

        private bool Send(JsonLine line)
        {
            if (!_sender.Connected)
            {
                Toast("Lektor nie jest połączony");
                return false;
            }
            _log.Write(line);
            return true;
        }

        private void Control(string cmd) { Send(_log.New("control").Str("cmd", cmd)); }

        private void ToggleMenu()
        {
            _menu = !_menu;
            if (_menu) _bar.CloseGameSubmenus();
            _log.Write(_log.New("overlay").Str("menu", _menu ? "open" : "close"));
        }

        private void StartReport(long token)
        {
            if (_reportDir != null) return;
            try
            {
                string dir = Path.Combine(_reportsRoot, DateTime.Now.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture));
                Directory.CreateDirectory(dir);
                _reportDir = dir;
                _reportShot = Path.Combine(dir, "ekran.png");
                _reportToken = token;
                _menu = false;
                _captureFrame = Time.frameCount + 1;      // zrzut w następnej klatce, już bez menu
            }
            catch (Exception e)
            {
                _log.Error("report_dir", e);
                Toast("Nie udało się utworzyć folderu zgłoszenia");
            }
        }

        private void FinishReport(string category)
        {
            var line = _log.New("report").Str("category", category).Str("dir", _reportDir).Str("shot", _reportShot)
                .Str("plugin", Bootstrap.Version);
            if (_reportToken > 0) line.Int("token", _reportToken);
            if (!Send(line)) Toast("Zgłoszenie: zapisany sam zrzut ekranu");
            ResetReport();
        }

        private void CancelReport()
        {
            try { if (_reportDir != null) Directory.Delete(_reportDir, true); } catch (Exception) { }
            ResetReport();
            Toast("Anulowano zgłoszenie");
        }

        private void ResetReport()
        {
            _reportDir = _reportShot = null;
            _reportToken = 0;
            _captureFrame = -1;
        }

        // ---------- klatka ----------

        public void Update()
        {
            try
            {
                if (_captureFrame >= 0 && Time.frameCount == _captureFrame)
                    ScreenCapture.CaptureScreenshot(_reportShot);
                if (Choosing) ChooseKeys();
                else Hotkeys();
                _bar.Update(_menu);
                if (_menu && _bar.GameSubmenuOpened) _menu = false;
                if (_blocker == null) _blocker = new Blocker();
                _blocker.Set(Choosing ? new Rect(0, 0, Screen.width, Screen.height) : _menu ? Scaled(MenuRect()) : Rect.zero);
            }
            catch (Exception e)
            {
                _log.Error("overlay", e);
            }
        }

        private void Hotkeys()
        {
            if (Pressed("menu")) ToggleMenu();
            else if (Pressed("szybciej")) Control("szybciej");
            else if (Pressed("wolniej")) Control("wolniej");
            else if (Pressed("wycisz")) Control("wycisz");
            else if (Pressed("powtorz")) Control("powtorz");
            else if (Pressed("utnij")) Control("utnij");
            else if (Pressed("zglos")) StartReport(0);
        }

        private void ChooseKeys()
        {
            for (int i = 0; i < Categories.Length / 2; i++)
                if (Input.GetKeyDown(KeyCode.Alpha1 + i) || Input.GetKeyDown(KeyCode.Keypad1 + i))
                {
                    FinishReport(Categories[2 * i]);
                    return;
                }
            if (Input.GetKeyDown(KeyCode.Alpha0) || Input.GetKeyDown(KeyCode.Keypad0) || Input.GetKeyDown(KeyCode.Backspace))
                CancelReport();
        }

        private bool Pressed(string action)
        {
            if (!_keys.TryGetValue(action, out List<Hotkey> list)) return false;
            foreach (Hotkey k in list)
                if (k.Down()) return true;
            return false;
        }

        // ---------- rysowanie (IMGUI) ----------

        private static float Scale => Mathf.Max(0.5f, Screen.height / 1080f);
        private static float W => Screen.width / Scale;
        private static float H => Screen.height / Scale;

        private static Rect MenuRect()
        {
            float h = Mathf.Min(780f, H - 200f);
            return new Rect(20f, H - 150f - h, 560f, h);
        }

        private static Rect Scaled(Rect r)
        {
            float s = Scale;
            return new Rect(r.x * s, r.y * s, r.width * s, r.height * s);
        }

        public void OnGUI()
        {
            try
            {
                if (_toast == null && !_menu && !Choosing) return;
                Styles();
                Matrix4x4 old = GUI.matrix;
                GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(Scale, Scale, 1f));
                if (Choosing) DrawChooser();
                else if (_menu) DrawMenu();
                DrawToast();
                GUI.matrix = old;
            }
            catch (Exception e)
            {
                _log.Error("overlay_gui", e);
            }
        }

        private void DrawToast()
        {
            if (_toast == null) return;
            if (Time.unscaledTime > _toastUntil) { _toast = null; return; }
            var size = _toastStyle.CalcSize(new GUIContent(_toast));
            var r = new Rect((W - size.x) / 2f - 20f, H * 0.12f, size.x + 40f, size.y + 16f);
            GUI.Box(r, _toast, _toastStyle);
        }

        private void DrawChooser()
        {
            var r = new Rect((W - 520f) / 2f, (H - 420f) / 2f, 520f, 420f);
            GUILayout.BeginArea(r, _panel);
            GUILayout.Label("Zgłoszenie błędu lektora", _title);
            GUILayout.Label(_reportToken > 0 ? "Kwestia z historii. Zrzut ekranu zapisany." : "Zrzut ekranu zapisany. Co się stało?", _small);
            GUILayout.Space(8f);
            for (int i = 0; i < Categories.Length / 2; i++)
                if (GUILayout.Button((i + 1) + ".  " + Categories[2 * i + 1], _button))
                    FinishReport(Categories[2 * i]);
            GUILayout.Space(6f);
            if (GUILayout.Button("0.  Anuluj", _button)) CancelReport();
            GUILayout.EndArea();
        }

        private void DrawMenu()
        {
            Rect r = MenuRect();
            GUILayout.BeginArea(r, _panel);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Lektor PL", _title);
            GUILayout.FlexibleSpace();
            GUILayout.Label(Connected ? "połączony" : "brak połączenia", _small);
            if (GUILayout.Button("✕", _button, GUILayout.Width(40f))) _menu = false;
            GUILayout.EndHorizontal();
            _scroll = GUILayout.BeginScrollView(_scroll);
            if (!Connected)
                GUILayout.Label("Companion lektora nie odpowiada. Skróty i menu zadziałają po połączeniu.", _text);
            else
            {
                DrawNow();
                DrawSettings();
                DrawHistory();
                DrawToggles();
                DrawStatus();
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        private void DrawNow()
        {
            GUILayout.Label("Teraz", _section);
            var now = Json.Obj(_state, "now");
            int queue = (int)Json.Num(_state, "queue");
            if (now == null)
                GUILayout.Label(Json.Bool(_state, "muted") ? "Lektor wyciszony." : "Cisza.", _text);
            else
            {
                GUILayout.Label("<b>" + Json.Str(now, "speaker", "?") + "</b>  " + Json.Str(now, "text", ""), _text);
                double total = Json.Num(now, "seconds", 0), elapsed = Json.Num(now, "elapsed", 0) + (Time.unscaledTime - _stateAt);
                Rect bar = GUILayoutUtility.GetRect(10f, 8f, GUILayout.ExpandWidth(true));
                GUI.DrawTexture(bar, _bar1);
                if (total > 0) GUI.DrawTexture(new Rect(bar.x, bar.y, bar.width * Mathf.Clamp01((float)(elapsed / total)), bar.height), _bar2);
            }
            if (queue > 0) GUILayout.Label("W kolejce: " + queue, _small);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Powtórz ostatnią", _button)) Control("powtorz");
            if (GUILayout.Button("Utnij", _button)) Control("utnij");
            if (GUILayout.Button(Json.Bool(_state, "muted") ? "Włącz lektora" : "Wycisz", _button)) Control("wycisz");
            GUILayout.EndHorizontal();
        }

        private void DrawSettings()
        {
            GUILayout.Label("Ustawienia", _section);
            double tempo = Json.Num(_state, "tempo", 1.0);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Tempo", _text, GUILayout.Width(110f));
            if (GUILayout.Button("–", _button, GUILayout.Width(44f))) Control("wolniej");
            GUILayout.Label(tempo.ToString("0.0", CultureInfo.InvariantCulture).Replace('.', ',') + "×", _title, GUILayout.Width(70f));
            if (GUILayout.Button("+", _button, GUILayout.Width(44f))) Control("szybciej");
            GUILayout.FlexibleSpace();
            GUILayout.EndHorizontal();

            float remote = (float)Json.Num(_state, "volume", 1.0);
            if (_volume < 0f || Time.unscaledTime - _volumeTouchedAt > 1.5f) _volume = remote;
            GUILayout.BeginHorizontal();
            GUILayout.Label("Głośność", _text, GUILayout.Width(110f));
            float v = GUILayout.HorizontalSlider(_volume, 0f, 1f, GUILayout.ExpandWidth(true));
            GUILayout.Label(Mathf.RoundToInt(v * 100f) + "%", _text, GUILayout.Width(60f));
            GUILayout.EndHorizontal();
            if (Mathf.Abs(v - _volume) > 0.001f) { _volume = Mathf.Round(v * 20f) / 20f; _volumeTouchedAt = Time.unscaledTime; }
            if (Mathf.Abs(_volume - remote) > 0.001f && Time.unscaledTime - _volumeSentAt > VolumeSendGap)
            {
                _volumeSentAt = Time.unscaledTime;
                Send(_log.New("control").Str("cmd", "glosnosc").Num("value", _volume));
            }
        }

        private void DrawHistory()
        {
            var history = Json.List(_state, "history");
            GUILayout.Label("Ostatnie kwestie", _section);
            if (history == null || history.Count == 0) { GUILayout.Label("Jeszcze nic nie zagrało.", _small); return; }
            foreach (object h in history)
            {
                long token = (long)Json.Num(h, "token");
                string head = "<b>" + Json.Str(h, "speaker", "?") + "</b> · " + Ago(Json.Num(h, "ago")) + (Json.Bool(h, "muted") ? " · wyciszona" : "");
                GUILayout.BeginHorizontal();
                GUILayout.BeginVertical();
                GUILayout.Label(head, _small);
                GUILayout.Label(Json.Str(h, "text", ""), _text);
                GUILayout.EndVertical();
                if (GUILayout.Button("▶", _button, GUILayout.Width(44f)))
                    Send(_log.New("control").Str("cmd", "powtorz").Int("value", token));
                if (GUILayout.Button("Zgłoś", _button, GUILayout.Width(80f))) StartReport(token);
                GUILayout.EndHorizontal();
            }
        }

        private void DrawToggles()
        {
            var toggles = Json.Obj(_state, "toggles");
            if (toggles == null) return;
            GUILayout.Label("Co czyta lektor", _section);
            int col = 0;
            GUILayout.BeginHorizontal();
            foreach (var kv in toggles)
            {
                bool on = kv.Value is bool b && b;
                string label = ToggleLabels.TryGetValue(kv.Key, out string l) ? l : kv.Key;
                bool next = GUILayout.Toggle(on, " " + label, _text, GUILayout.Width(250f));
                if (next != on)
                    Send(_log.New("control").Str("cmd", "przelacznik")
                        .Raw("value", new JsonLine().Str("name", kv.Key).Bool("on", next).ToString()));
                if (++col % 2 == 0) { GUILayout.EndHorizontal(); GUILayout.BeginHorizontal(); }
            }
            GUILayout.EndHorizontal();
        }

        private void DrawStatus()
        {
            GUILayout.Label("Zgłoszenia i stan", _section);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Zgłoś błąd (" + KeyLabel("zglos") + ")", _button)) StartReport(0);
            GUILayout.FlexibleSpace();
            GUILayout.EndHorizontal();
            GUILayout.Label("Zgłoszenia w tej sesji: " + (int)Json.Num(_state, "reports") + ". Folder: " + _reportsRoot, _small);
            GUILayout.Label("Okna bez nagrania w tej sesji: " + (int)Json.Num(_state, "missing") + ". Nagrania: " + Json.Str(_state, "model", "?")
                            + ". Plugin " + Bootstrap.Version + ".", _small);
            GUILayout.Label("Skróty: menu " + KeyLabel("menu") + ", tempo " + KeyLabel("szybciej") + " / " + KeyLabel("wolniej")
                            + ", wycisz " + KeyLabel("wycisz") + ", powtórz " + KeyLabel("powtorz") + ", utnij " + KeyLabel("utnij"), _small);
        }

        private string KeyLabel(string action)
        {
            return _keys.TryGetValue(action, out List<Hotkey> list) && list.Count > 0 ? list[0].ToString() : "-";
        }

        private static string Ago(double s)
        {
            if (s < 60) return (int)s + " s temu";
            return (int)(s / 60) + " min temu";
        }

        private void Styles()
        {
            if (_panel != null) return;
            _bg = Solid(new Color(0.07f, 0.06f, 0.05f, 0.94f));
            _bar1 = Solid(new Color(1f, 1f, 1f, 0.15f));
            _bar2 = Solid(new Color(0.86f, 0.70f, 0.38f, 1f));
            _panel = new GUIStyle(GUI.skin.box) { padding = new RectOffset(16, 16, 12, 12) };
            _panel.normal.background = _bg;
            _title = new GUIStyle(GUI.skin.label) { fontSize = 24, fontStyle = FontStyle.Bold, richText = true };
            _title.normal.textColor = new Color(0.86f, 0.70f, 0.38f);
            _section = new GUIStyle(_title) { fontSize = 19, margin = new RectOffset(4, 4, 14, 4) };
            _text = new GUIStyle(GUI.skin.label) { fontSize = 17, wordWrap = true, richText = true };
            _text.normal.textColor = new Color(0.93f, 0.91f, 0.86f);
            _small = new GUIStyle(_text) { fontSize = 14 };
            _small.normal.textColor = new Color(0.75f, 0.72f, 0.66f);
            _button = new GUIStyle(GUI.skin.button) { fontSize = 17, padding = new RectOffset(10, 10, 6, 6) };
            _toastStyle = new GUIStyle(GUI.skin.box) { fontSize = 22, alignment = TextAnchor.MiddleCenter, padding = new RectOffset(16, 16, 8, 8) };
            _toastStyle.normal.background = _bg;
            _toastStyle.normal.textColor = new Color(0.93f, 0.91f, 0.86f);
        }

        private static Texture2D Solid(Color c)
        {
            var t = new Texture2D(1, 1) { hideFlags = HideFlags.HideAndDontSave };
            t.SetPixel(0, 0, c);
            t.Apply();
            return t;
        }

        /// <summary>Przezroczysty obraz uGUI pod menu: gra widzi wskaźnik nad UI i nie klika w planszę.</summary>
        private sealed class Blocker
        {
            private readonly GameObject _root;
            private readonly RectTransform _rect;
            private Rect _last = new Rect(-1, -1, -1, -1);

            public Blocker()
            {
                _root = new GameObject("LektorPL.Blocker") { hideFlags = HideFlags.HideAndDontSave };
                UnityEngine.Object.DontDestroyOnLoad(_root);
                var canvas = _root.AddComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                canvas.sortingOrder = 32000;
                _root.AddComponent<GraphicRaycaster>();
                var child = new GameObject("Area");
                child.transform.SetParent(_root.transform, false);
                var img = child.AddComponent<Image>();
                img.color = new Color(0f, 0f, 0f, 0f);
                _rect = img.rectTransform;
                _rect.anchorMin = _rect.anchorMax = _rect.pivot = Vector2.zero;
                _root.SetActive(false);
            }

            /// <summary>Prostokąt w pikselach ekranu, oś y od góry (jak IMGUI); pusty wyłącza blokadę.</summary>
            public void Set(Rect r)
            {
                if (r == _last) return;
                _last = r;
                if (r.width <= 0f) { _root.SetActive(false); return; }
                _rect.anchoredPosition = new Vector2(r.x, Screen.height - r.y - r.height);
                _rect.sizeDelta = new Vector2(r.width, r.height);
                _root.SetActive(true);
            }
        }
    }

    /// <summary>Skrót: klawisz Unity (KeyCode) z modyfikatorami, np. „Ctrl+Equals”.</summary>
    internal sealed class Hotkey
    {
        private KeyCode _key;
        private bool _ctrl, _alt, _shift, _cmd;
        private string _text;

        public static List<Hotkey> ParseList(string spec)
        {
            var list = new List<Hotkey>();
            foreach (string part in (spec ?? "").Split(','))
            {
                Hotkey k = Parse(part.Trim());
                if (k != null) list.Add(k);
            }
            return list;
        }

        private static Hotkey Parse(string s)
        {
            if (s.Length == 0) return null;
            var k = new Hotkey { _text = s };
            string[] parts = s.Split('+');
            for (int i = 0; i < parts.Length - 1; i++)
            {
                string m = parts[i].Trim().ToLowerInvariant();
                if (m == "ctrl" || m == "control") k._ctrl = true;
                else if (m == "alt" || m == "option") k._alt = true;
                else if (m == "shift") k._shift = true;
                else if (m == "cmd" || m == "command") k._cmd = true;
                else return null;
            }
            try { k._key = (KeyCode)Enum.Parse(typeof(KeyCode), parts[parts.Length - 1].Trim(), true); }
            catch (Exception) { return null; }
            return k;
        }

        public bool Down()
        {
            if (!Input.GetKeyDown(_key)) return false;
            bool ctrl = Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl);
            bool alt = Input.GetKey(KeyCode.LeftAlt) || Input.GetKey(KeyCode.RightAlt);
            bool shift = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
            bool cmd = Input.GetKey(KeyCode.LeftCommand) || Input.GetKey(KeyCode.RightCommand);
            return ctrl == _ctrl && alt == _alt && shift == _shift && cmd == _cmd;
        }

        public override string ToString()
        {
            return _text.Replace("Equals", "=").Replace("Minus", "-");
        }
    }
}
