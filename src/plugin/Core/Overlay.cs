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
    /// Menu lektora to uGUI w stylu podmenu gry (PlMenu). Okno zgłoszenia to IMGUI; pod nim leży przezroczysty obraz uGUI, żeby kliknięcia nie trafiały w planszę
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

        private readonly EventLog _log;
        private readonly Sender _sender;
        private readonly string _reportsRoot;
        private readonly Dictionary<string, List<Hotkey>> _keys = new Dictionary<string, List<Hotkey>>();
        private readonly PlMenu _menuUi;
        private Blocker _blocker;

        private object _state;
        private float _stateAt;
        private long _noticeSeen = -1;
        private string _toast;
        private float _toastUntil;

        private bool _menu;

        // Zgłoszenie: zrzut w klatce _captureFrame (po zamknięciu menu), potem wybór kategorii.
        private int _captureFrame = -1;
        private long _reportToken;
        private string _reportDir, _reportShot;

        private GUIStyle _panel, _title, _small, _button, _toastStyle;
        private Texture2D _bg;

        public Overlay(EventLog log, Sender sender, string logDirectory)
        {
            _log = log;
            _sender = sender;
            _reportsRoot = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(logDirectory)) ?? ".", "zgloszenia");
            for (int i = 0; i < DefaultKeys.Length; i += 2)
                _keys[DefaultKeys[i]] = Hotkey.ParseList(DefaultKeys[i + 1]);
            sender.OnLine = OnLine;
            _menuUi = new PlMenu(log, this);
        }

        public bool MenuOpen => _menu;
        internal object State => _state;
        internal float StateAge => Time.unscaledTime - _stateAt;
        internal EventLog Log => _log;
        internal bool Connected => _sender.Connected && _state != null && Time.unscaledTime - _stateAt < 5f;
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

        internal bool Send(JsonLine line)
        {
            if (!_sender.Connected)
            {
                Toast("Lektor nie jest połączony");
                return false;
            }
            _log.Write(line);
            return true;
        }

        internal void Control(string cmd) { Send(_log.New("control").Str("cmd", cmd)); }

        internal void ToggleMenu()
        {
            if (!_menu && !_menuUi.Available)
            {
                Toast("Menu lektora jest na dolnym pasku w trakcie gry");
                return;
            }
            _menu = !_menu;
            if (_menu) _menuUi.CloseGameSubmenus();
            _log.Write(_log.New("overlay").Str("menu", _menu ? "open" : "close"));
        }

        internal void StartReport(long token)
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
                _menuUi.SnapClosed();                     // zrzut bez menu
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
                _menuUi.Update(_menu);
                if (_menu && (_menuUi.GameSubmenuOpened || !_menuUi.Available)) _menu = false;
                if (_blocker == null) _blocker = new Blocker();
                _blocker.Set(Choosing ? new Rect(0, 0, Screen.width, Screen.height) : Rect.zero);
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

        public void OnGUI()
        {
            try
            {
                if (_toast == null && !Choosing) return;
                Styles();
                Matrix4x4 old = GUI.matrix;
                GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(Scale, Scale, 1f));
                if (Choosing) DrawChooser();
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

        internal string KeyLabel(string action)
        {
            if (!_keys.TryGetValue(action, out List<Hotkey> list) || list.Count == 0) return "-";
            var parts = new List<string>();
            foreach (Hotkey k in list) parts.Add(k.ToString());
            return string.Join(" lub ", parts.ToArray());
        }

        private void Styles()
        {
            if (_panel != null) return;
            _bg = Solid(new Color(0.07f, 0.06f, 0.05f, 0.94f));
            _panel = new GUIStyle(GUI.skin.box) { padding = new RectOffset(16, 16, 12, 12) };
            _panel.normal.background = _bg;
            _title = new GUIStyle(GUI.skin.label) { fontSize = 24, fontStyle = FontStyle.Bold, richText = true };
            _title.normal.textColor = new Color(0.86f, 0.70f, 0.38f);
            _small = new GUIStyle(GUI.skin.label) { fontSize = 16, wordWrap = true, richText = true };
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
            var k = new Hotkey();
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
            string key = _key == KeyCode.Equals ? "=" : _key == KeyCode.Minus ? "–" : _key == KeyCode.KeypadPlus ? "+ (num.)"
                : _key == KeyCode.KeypadMinus ? "– (num.)" : _key.ToString();
            var sb = new System.Text.StringBuilder();
            if (_ctrl) sb.Append("Ctrl + ");
            if (_alt) sb.Append("Alt + ");
            if (_shift) sb.Append("Shift + ");
            if (_cmd) sb.Append("Cmd + ");
            return sb.Append(key).ToString();
        }
    }
}
