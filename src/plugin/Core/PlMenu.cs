using System;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using System.Text;
using FFG.D3.UI;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace LektorPL.Core
{
    /// <summary>
    /// Przycisk „PL” i menu lektora na dolnym pasku gry (próba), w stylu podmenu zębatki i drużyny.
    ///
    /// Kopiujemy całe podmenu drużyny (<c>Submenu_Party</c>: czarny panel z przyciskiem na górze) pod nieaktywnym
    /// rodzicem, więc skrypty gry w kopii nie startują; usuwamy je i przyciski drużyny, a jeden niebieski przycisk
    /// zostaje jako wzór dla naszych. Kopia stoi obok drużyny, ostatnia wśród rodzeństwa (zasłania przyciski gry,
    /// gdy menu jest otwarte). Panel zaczyna się przy lewej krawędzi jak panele gry i sięga za przycisk „PL”.
    /// Ruch jak w grze: otwarcie wysuwa panel o jego wysokość, a gdy gra otworzy swoje podmenu, „PL” chowa się pod
    /// krawędź ekranu. Treść to uGUI z czcionką gry, przewijana, gdy nie mieści się na ekranie.
    /// </summary>
    internal sealed class PlMenu
    {
        private const BindingFlags Private = BindingFlags.NonPublic | BindingFlags.Instance;
        private static readonly FieldInfo OptionsVisible = typeof(UIGame).GetField("_isSubMenuOptionsVisible", Private);
        private static readonly FieldInfo PartyVisible = typeof(UIGame).GetField("_isSubMenuPartyVisible", Private);
        private static readonly FieldInfo PartyStart = typeof(UIGame).GetField("_subMenuPartyStartingLocation", Private);

        private const int HistoryShown = 3;              // ostatnie kwestie w menu (companion pamięta 10)
        private const float MinWidth = 400f, Gap = 8f, HideDistance = 120f, TweenSeconds = 0.3f, TopMargin = 330f;
        private static readonly Color Gold = new Color(0.86f, 0.70f, 0.38f);
        private static readonly Color Light = new Color(0.93f, 0.91f, 0.86f);
        private static readonly Color Dim = new Color(0.66f, 0.63f, 0.58f);

        private static readonly string[] ToggleOrder =
        {
            "narracja", "Narracja (opisy narratora)", "dialogi", "Dialogi postaci", "komunikaty_questu", "Komunikaty zadania",
            "cele", "Cele misji", "walka_teren", "Walka i teren", "aktywacje", "Aktywacje wrogów",
            "zdolnosci", "Okno ataku i obrona wroga", "nagrody", "Nagrody", "okna_wyboru", "Odpowiedź po wyborze",
            "ui", "Interfejs i samouczek", "miasto", "Teksty w mieście", "podroze", "Wydarzenia w podróży",
            "opis_misji", "Opis misji na mapie",
        };
        private static readonly string[] KeyOrder =
        {
            "menu", "Menu lektora", "szybciej", "Szybciej", "wolniej", "Wolniej", "wycisz", "Wycisz / włącz",
            "powtorz", "Powtórz ostatnią kwestię", "utnij", "Utnij bieżącą kwestię", "zglos", "Zgłoś błąd",
        };

        private readonly EventLog _log;
        private readonly Overlay _host;
        private UIGame _ui;
        private bool _failed, _gameMenuWasOpen;

        private RectTransform _holder, _panel, _partyHolder, _partyPanel, _body, _content;
        private CanvasGroup _group, _partyGroup;
        private Button _button, _partyButton;
        private Graphic _label;                                       // logo (Image) albo zapasowy napis „PL”
        private static Sprite _logo;
        private static bool _logoTried;

        /// <summary>Białe logo z zasobu LektorPL.Core.dll (PNG 128 px z assets/logo).</summary>
        private static Sprite LogoSprite()
        {
            if (_logoTried) return _logo;
            _logoTried = true;
            try
            {
                using (var s = typeof(PlMenu).Assembly.GetManifestResourceStream("LektorPL.Core.logo-bialy.png"))
                {
                    if (s == null) return null;
                    var bytes = new byte[s.Length];
                    int read = 0;
                    while (read < bytes.Length) { int n = s.Read(bytes, read, bytes.Length - read); if (n <= 0) break; read += n; }
                    var tex = new Texture2D(2, 2, TextureFormat.RGBA32, true) { name = "LektorPL.Logo", hideFlags = HideFlags.HideAndDontSave };
                    if (!ImageConversion.LoadImage(tex, bytes, true)) return null;
                    tex.wrapMode = TextureWrapMode.Clamp;
                    tex.filterMode = FilterMode.Trilinear;
                    _logo = Sprite.Create(tex, new Rect(0f, 0f, tex.width, tex.height), new Vector2(0.5f, 0.5f), 100f);
                    _logo.name = "LektorPL.Logo";
                    _logo.hideFlags = HideFlags.HideAndDontSave;
                }
            }
            catch (Exception) { _logo = null; }
            return _logo;
        }
        private GameObject _buttonTemplate, _toggleTemplate;
        private TMP_FontAsset _font;
        private Vector3 _restPos;
        private float _offset, _from, _to, _t0 = -10f, _maxBody = 600f;

        private string _signature;
        private readonly List<Action> _refresh = new List<Action>();

        public PlMenu(EventLog log, Overlay host)
        {
            _log = log;
            _host = host;
        }

        public bool Available => _holder != null && _holder.gameObject.activeInHierarchy;

        /// <summary>Gra otworzyła właśnie swoje podmenu (zębatka albo drużyna): menu lektora się zwija.</summary>
        public bool GameSubmenuOpened { get; private set; }

        public void CloseGameSubmenus()
        {
            try
            {
                if (_ui != null) _ui.OnCloseSubmenus(true, true);
            }
            catch (Exception e) { _log.Error("bar_close", e); }
        }

        /// <summary>Menu schowane od razu, bez animacji (przed zrzutem ekranu do zgłoszenia).</summary>
        public void SnapClosed()
        {
            _from = _to = _offset = 0f;
            _t0 = -10f;
            if (_panel != null) _panel.localPosition = _restPos;
        }

        public void Update(bool menuOpen)
        {
            GameSubmenuOpened = false;
            if (!SingletonBehaviour<UIGame>.IsInitialized) { _ui = null; _holder = null; return; }
            var ui = SingletonBehaviour<UIGame>.Instance;
            if (ui != _ui) { _ui = ui; _holder = null; _failed = false; }
            bool gameMenu = IsTrue(OptionsVisible) || IsTrue(PartyVisible);
            GameSubmenuOpened = gameMenu && !_gameMenuWasOpen;
            _gameMenuWasOpen = gameMenu;
            if (_failed) return;
            try
            {
                if (_holder == null) Create(ui);
                if (_holder == null) return;
                if (menuOpen) Refresh();
                Follow(menuOpen, gameMenu);
            }
            catch (Exception e)
            {
                _failed = true;
                _log.Error("pl_menu", e);
            }
        }

        private bool IsTrue(FieldInfo f)
        {
            return f != null && _ui != null && f.GetValue(_ui) is bool b && b;
        }

        // ---------- budowa przycisku i panelu ----------

        private static float ButtonCenter(RectTransform holder, RectTransform panel, RectTransform button)
        {
            // Uchwyt: kotwica w lewym dolnym rogu rodzica; panel: kotwica (0.5, 1) uchwytu, oś w lewym górnym rogu;
            // przycisk: kotwica (0.5, 1) panelu. Wynik: środek przycisku od lewej krawędzi rodzica.
            return holder.anchoredPosition.x + panel.anchoredPosition.x + panel.rect.width / 2f + button.anchoredPosition.x;
        }

        private void Create(UIGame ui)
        {
            if (ui.SubMenuParty == null || ui.SubmenuOptions == null || ui.SubmenuPartyButton == null || ui.SubmenuOptionsButton == null) return;
            _partyPanel = (RectTransform)ui.SubMenuParty.transform;
            _partyHolder = (RectTransform)_partyPanel.parent;
            var optPanel = (RectTransform)ui.SubmenuOptions.transform;
            var optHolder = (RectTransform)optPanel.parent;
            _partyButton = ui.SubmenuPartyButton;
            var partyBtn = (RectTransform)_partyButton.transform;
            var optBtn = (RectTransform)ui.SubmenuOptionsButton.transform;
            if (_partyHolder == null || optHolder == null || _partyHolder.parent == null) return;

            float spacing = ButtonCenter(_partyHolder, _partyPanel, partyBtn) - ButtonCenter(optHolder, optPanel, optBtn);
            if (spacing < 60f || spacing > 300f) spacing = 135f;

            var temp = new GameObject("LektorPL.Temp");
            temp.SetActive(false);
            temp.transform.SetParent(_partyHolder.parent, false);
            GameObject copy = UnityEngine.Object.Instantiate(_partyHolder.gameObject, temp.transform, false);
            copy.name = "LektorPL.Submenu";
            var dump = new StringBuilder();
            Strip(copy, dump);

            var holder = (RectTransform)copy.transform;
            var panel = holder.Find(_partyPanel.name) as RectTransform;
            var btn = panel != null ? panel.Find(partyBtn.name) as RectTransform : null;
            if (panel == null || btn == null) { UnityEngine.Object.Destroy(temp); _failed = true; return; }
            for (int i = holder.childCount - 1; i >= 0; i--)
                if (holder.GetChild(i) != panel) UnityEngine.Object.DestroyImmediate(holder.GetChild(i).gameObject);

            // Wzór przycisku: niebieski przycisk wprost w panelu (pomarańczowe są w Content_QuestOnly); reszta panelu znika.
            var templates = new GameObject("LektorPL.Templates", typeof(RectTransform));
            templates.SetActive(false);
            templates.transform.SetParent(holder, false);
            foreach (Button b in panel.GetComponentsInChildren<Button>(true))
                if (b.transform != btn && b.transform.parent == panel) { b.transform.SetParent(templates.transform, false); _buttonTemplate = b.gameObject; break; }
            for (int i = panel.childCount - 1; i >= 0; i--)
                if (panel.GetChild(i) != btn) UnityEngine.Object.DestroyImmediate(panel.GetChild(i).gameObject);
            if (_buttonTemplate == null) { UnityEngine.Object.Destroy(temp); _failed = true; return; }
            TMP_Text sample = _buttonTemplate.GetComponentInChildren<TMP_Text>(true);
            _font = sample != null ? sample.font : null;
            _toggleTemplate = ToggleTemplate(templates.transform, panel, dump);
            DescribeTemplate(dump);

            // Położenie: uchwyt o „spacing” w prawo od drużyny, lewa krawędź panelu jak w grze, przycisk nad prawym końcem.
            holder.anchoredPosition = _partyHolder.anchoredPosition + new Vector2(spacing, 0f);
            float btnFromLeft = _partyPanel.rect.width / 2f + partyBtn.anchoredPosition.x + spacing;
            float width = Mathf.Max(MinWidth, btnFromLeft + btn.rect.width / 2f + Gap);
            panel.anchoredPosition = new Vector2(_partyPanel.anchoredPosition.x - spacing, panel.anchoredPosition.y);
            panel.sizeDelta = new Vector2(width, panel.sizeDelta.y);
            btn.anchoredPosition = new Vector2(btnFromLeft - width / 2f, btn.anchoredPosition.y);
            var ble = btn.GetComponent<LayoutElement>() ?? btn.gameObject.AddComponent<LayoutElement>();
            ble.ignoreLayout = true;

            _restPos = panel.localPosition;
            if (PartyStart != null && PartyStart.GetValue(ui) is Vector2 start) _restPos.y = start.y;
            panel.localPosition = _restPos;

            var vg = panel.GetComponent<VerticalLayoutGroup>() ?? panel.gameObject.AddComponent<VerticalLayoutGroup>();
            vg.padding = new RectOffset(14, 14, 12, 12);
            vg.spacing = 6f;
            vg.childAlignment = TextAnchor.UpperCenter;
            vg.childControlWidth = vg.childControlHeight = true;
            vg.childForceExpandWidth = true;
            vg.childForceExpandHeight = false;
            var fit = panel.GetComponent<ContentSizeFitter>() ?? panel.gameObject.AddComponent<ContentSizeFitter>();
            fit.horizontalFit = ContentSizeFitter.FitMode.Unconstrained;
            fit.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            _group = panel.GetComponent<CanvasGroup>() ?? panel.gameObject.AddComponent<CanvasGroup>();
            _group.alpha = 1f;
            _group.interactable = _group.blocksRaycasts = true;
            _partyGroup = _partyPanel.GetComponent<CanvasGroup>();

            _button = btn.GetComponent<Button>();
            _button.onClick = new Button.ButtonClickedEvent();
            _button.onClick.AddListener(() => _host.ToggleMenu());
            // Ikona: białe logo lektora w miejscu ikony drużyny (ten sam rozmiar i położenie); bez logo napis „PL”.
            Image icon = null;
            foreach (Image img in btn.GetComponentsInChildren<Image>(true))
            {
                if (img.transform == btn) continue;
                if (icon == null && LogoSprite() != null) icon = img;
                else img.enabled = false;
            }
            if (icon != null)
            {
                icon.sprite = LogoSprite();
                icon.type = Image.Type.Simple;
                icon.preserveAspect = true;
                icon.overrideSprite = null;
                icon.material = null;
                icon.color = Light;
                icon.enabled = true;
                _label = icon;
            }
            else
            {
                var text = AddText(btn, "PL", Mathf.Max(20f, btn.rect.height * 0.3f), Light, TextAlignmentOptions.Center, true);
                var lrt = text.rectTransform;
                lrt.anchorMin = Vector2.zero;
                lrt.anchorMax = Vector2.one;
                lrt.offsetMin = new Vector2(0f, btn.rect.height * 0.22f);   // jak ikona drużyny: nad środkiem (dół przycisku jest pod ekranem)
                lrt.offsetMax = Vector2.zero;
                _label = text;
            }

            BuildBody(panel);

            holder.SetParent(_partyHolder.parent, false);
            holder.SetAsLastSibling();
            UnityEngine.Object.Destroy(temp);
            _holder = holder;
            _panel = panel;
            _signature = null;
            SnapClosed();
            var root = _partyHolder.parent as RectTransform;
            if (root != null) _maxBody = Mathf.Max(240f, root.rect.height - TopMargin);
            _log.Write(_log.New("overlay_button").Str("parent", _partyHolder.parent.name).Num("spacing", spacing).Num("width", width)
                .Num("rest_y", _restPos.y).Str("tree", dump.ToString()));
        }

        /// <summary>Usuwa z kopii skrypty gry (Assembly-CSharp i inne spoza Unity), zostawia grafikę, przyciski i układ.</summary>
        private static void Strip(GameObject go, StringBuilder dump)
        {
            foreach (Component c in go.GetComponentsInChildren<Component>(true))
            {
                if (c == null || c is Transform) continue;
                string asm = c.GetType().Assembly.GetName().Name;
                bool unity = asm.StartsWith("UnityEngine", StringComparison.Ordinal) || asm.StartsWith("Unity.TextMeshPro", StringComparison.Ordinal);
                if (!unity)
                {
                    dump.Append(c.gameObject.name).Append(':').Append(c.GetType().Name).Append("(usunięty); ");
                    UnityEngine.Object.DestroyImmediate(c);
                }
            }
        }

        /// <summary>
        /// Checkbox gry: kopia przełącznika z okna opcji (Toggle_AutoContinue i podobne: Background/Checkmark + Label_Settings).
        /// Gdy okna opcji nie ma w pamięci, składamy podobny z tła panelu (UISprite) i znaku z czcionki gry.
        /// </summary>
        private GameObject ToggleTemplate(Transform templates, RectTransform panel, StringBuilder dump)
        {
            Toggle source = null;
            foreach (Toggle t in Resources.FindObjectsOfTypeAll<Toggle>())
            {
                if (t == null || !t.gameObject.scene.IsValid()) continue;
                if (t.transform.Find("Background/Checkmark") == null || t.GetComponentInChildren<TMP_Text>(true) == null) continue;
                if (source == null || t.name == "Toggle_AutoContinue") source = t;
                if (t.name == "Toggle_AutoContinue") break;
            }
            GameObject go;
            if (source != null)
            {
                go = UnityEngine.Object.Instantiate(source.gameObject, templates, false);
                Strip(go, dump);
                dump.Append("checkbox z ").Append(source.name).Append("; ");
            }
            else
            {
                go = new GameObject("Toggle", typeof(RectTransform));
                go.transform.SetParent(templates, false);
                var bg = NewRect("Background", go.transform);
                bg.anchorMin = bg.anchorMax = new Vector2(0f, 0.5f);
                bg.pivot = new Vector2(0f, 0.5f);
                bg.sizeDelta = new Vector2(40f, 40f);
                var bimg = bg.gameObject.AddComponent<Image>();
                var pimg = panel.GetComponent<Image>();
                if (pimg != null) { bimg.sprite = pimg.sprite; bimg.type = Image.Type.Sliced; }
                bimg.color = new Color(0.55f, 0.55f, 0.55f, 1f);
                var mark = AddText(bg, "X", 28f, Gold, TextAlignmentOptions.Center, true);
                Stretch(mark.rectTransform);
                mark.name = "Checkmark";
                var label = AddText(go.transform, "", 20f, Light, TextAlignmentOptions.Left, false);
                Stretch(label.rectTransform);
                label.rectTransform.offsetMin = new Vector2(54f, 0f);
                var tg = go.AddComponent<Toggle>();
                tg.targetGraphic = bimg;
                tg.graphic = mark;
                dump.Append("checkbox własny; ");
            }
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0f, 1f);
            return go;
        }

        private void DescribeTemplate(StringBuilder dump)
        {
            var img = _buttonTemplate.GetComponent<Image>();
            var b = _buttonTemplate.GetComponent<Button>();
            dump.Append("wzór ").Append(_buttonTemplate.name);
            if (img != null)
                dump.Append(" sprite=").Append(img.sprite != null ? img.sprite.name : "-").Append(" type=").Append(img.type)
                    .Append(" border=").Append(img.sprite != null ? img.sprite.border.ToString() : "-");
            if (b != null) dump.Append(" transition=").Append(b.transition);
            dump.Append(" font=").Append(_font != null ? _font.name : "-").Append("; ");
        }

        private void BuildBody(RectTransform panel)
        {
            var body = NewRect("LektorPL.Body", panel);
            var le = body.gameObject.AddComponent<LayoutElement>();
            le.preferredHeight = 200f;
            var scroll = body.gameObject.AddComponent<ScrollRect>();
            scroll.horizontal = false;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 40f;

            var viewport = NewRect("Viewport", body);
            Stretch(viewport);
            viewport.offsetMax = new Vector2(-10f, 0f);
            var vimg = viewport.gameObject.AddComponent<Image>();
            vimg.color = new Color(0f, 0f, 0f, 0f);                 // łapie kółko myszy w pustych miejscach
            viewport.gameObject.AddComponent<RectMask2D>();

            var content = NewRect("Content", viewport);
            content.anchorMin = new Vector2(0f, 1f);
            content.anchorMax = new Vector2(1f, 1f);
            content.pivot = new Vector2(0.5f, 1f);
            content.offsetMin = content.offsetMax = Vector2.zero;
            var cvg = content.gameObject.AddComponent<VerticalLayoutGroup>();
            cvg.spacing = 6f;
            cvg.padding = new RectOffset(0, 4, 0, 4);
            cvg.childControlWidth = cvg.childControlHeight = true;
            cvg.childForceExpandWidth = true;
            cvg.childForceExpandHeight = false;
            var cfit = content.gameObject.AddComponent<ContentSizeFitter>();
            cfit.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            var bar = NewRect("Scrollbar", body);
            bar.anchorMin = new Vector2(1f, 0f);
            bar.anchorMax = new Vector2(1f, 1f);
            bar.pivot = new Vector2(1f, 0.5f);
            bar.sizeDelta = new Vector2(6f, 0f);
            bar.anchoredPosition = Vector2.zero;
            bar.gameObject.AddComponent<Image>().color = new Color(1f, 1f, 1f, 0.08f);
            var area = NewRect("Area", bar);
            Stretch(area);
            var handle = NewRect("Handle", area);
            Stretch(handle);
            var himg = handle.gameObject.AddComponent<Image>();
            himg.color = new Color(Gold.r, Gold.g, Gold.b, 0.7f);
            var sb = bar.gameObject.AddComponent<Scrollbar>();
            sb.direction = Scrollbar.Direction.BottomToTop;
            sb.handleRect = handle;
            sb.targetGraphic = himg;

            scroll.viewport = viewport;
            scroll.content = content;
            scroll.verticalScrollbar = sb;
            scroll.verticalScrollbarVisibility = ScrollRect.ScrollbarVisibility.AutoHide;
            _body = body;
            _content = content;
        }

        // ---------- ruch i widoczność ----------

        private void Follow(bool menuOpen, bool gameMenu)
        {
            bool visible = _partyPanel.gameObject.activeInHierarchy;
            if (_holder.gameObject.activeSelf != _partyHolder.gameObject.activeSelf) _holder.gameObject.SetActive(_partyHolder.gameObject.activeSelf);
            if (_panel.gameObject.activeSelf != _partyPanel.gameObject.activeSelf) _panel.gameObject.SetActive(_partyPanel.gameObject.activeSelf);
            if (!visible) { SnapClosed(); return; }

            float target = menuOpen ? _panel.rect.height : gameMenu ? -HideDistance : 0f;
            bool settled = Time.unscaledTime - _t0 >= TweenSeconds;
            if (Mathf.Abs(target - _to) > 0.5f)
            {
                if (menuOpen && settled && _to > 0f) { _from = _to = _offset = target; }      // wysokość treści się zmieniła
                else { _from = _offset; _to = target; _t0 = Time.unscaledTime; }
            }
            float k = Mathf.Clamp01((Time.unscaledTime - _t0) / TweenSeconds);
            k = k < 0.5f ? 4f * k * k * k : 1f - Mathf.Pow(-2f * k + 2f, 3f) / 2f;           // easeInOutCubic jak LeanTween w grze
            _offset = Mathf.Lerp(_from, _to, k);
            _panel.localPosition = _restPos + new Vector3(0f, _offset, 0f);

            if (_partyGroup != null)
            {
                _group.alpha = _partyGroup.alpha;
                _group.blocksRaycasts = _partyGroup.blocksRaycasts || menuOpen;
            }
            _button.interactable = _partyButton.interactable || menuOpen;
            _label.color = menuOpen ? Gold : Light;
        }

        // ---------- treść ----------

        private void Refresh()
        {
            object state = _host.State;
            bool connected = _host.Connected;
            string sig = Signature(state, connected);
            if (sig != _signature)
            {
                _signature = sig;
                Rebuild(state, connected);
            }
            foreach (Action a in _refresh) a();
            float h = LayoutUtility.GetPreferredHeight(_content);
            _body.GetComponent<LayoutElement>().preferredHeight = Mathf.Min(h, _maxBody);
        }

        private static string Signature(object state, bool connected)
        {
            if (!connected || state == null) return "x";
            var sb = new StringBuilder();
            sb.Append(Json.Bool(state, "muted")).Append('|').Append(Json.Obj(state, "now") != null).Append('|').Append(Json.Bool(state, "stats"));
            var toggles = Json.Obj(state, "toggles");
            if (toggles != null) foreach (var kv in toggles) sb.Append('|').Append(kv.Key).Append(kv.Value is bool b && b);
            var history = Json.List(state, "history");
            if (history != null) foreach (object h in history.GetRange(0, Math.Min(HistoryShown, history.Count))) sb.Append('|').Append(Json.Num(h, "token")).Append(Json.Bool(h, "muted"));
            return sb.ToString();
        }

        private void Rebuild(object state, bool connected)
        {
            for (int i = _content.childCount - 1; i >= 0; i--) UnityEngine.Object.Destroy(_content.GetChild(i).gameObject);
            _refresh.Clear();

            var head = Row(_content);
            AddText(head, "Lektor PL", 26f, Gold, TextAlignmentOptions.Left, true).gameObject.AddComponent<LayoutElement>().flexibleWidth = 1f;
            var status = AddText(head, "", 16f, Dim, TextAlignmentOptions.Right, false);
            _refresh.Add(() => status.text = _host.Connected ? "połączony" : "brak połączenia");

            if (!connected || state == null)
            {
                AddText(_content, "Lektor nie odpowiada. Menu zadziała po połączeniu.", 18f, Light, TextAlignmentOptions.Left, false);
                return;
            }
            BuildNow(state);
            BuildSettings(state);
            BuildToggles(state);
            BuildHistory(state);
            BuildReports();
        }

        private void BuildNow(object state)
        {
            Section("Teraz");
            var now = AddText(_content, "", 18f, Light, TextAlignmentOptions.Left, false);
            var track = NewRect("Postep", _content);
            track.gameObject.AddComponent<LayoutElement>().preferredHeight = 6f;
            track.gameObject.AddComponent<Image>().color = new Color(1f, 1f, 1f, 0.12f);
            var fill = NewRect("Fill", track);
            fill.anchorMin = Vector2.zero;
            fill.anchorMax = new Vector2(0f, 1f);
            fill.offsetMin = fill.offsetMax = Vector2.zero;
            fill.gameObject.AddComponent<Image>().color = Gold;
            _refresh.Add(() =>
            {
                object s = _host.State;
                var n = Json.Obj(s, "now");
                int queue = (int)Json.Num(s, "queue");
                if (n == null) now.text = Json.Bool(s, "muted") ? "Lektor wyciszony." : "Cisza.";
                else now.text = "<b>" + Json.Str(n, "speaker", "?") + "</b>  " + Json.Str(n, "text", "");
                if (queue > 0) now.text += "\n<size=80%><color=#A8A194>W kolejce: " + queue + "</color></size>";
                double total = Json.Num(n, "seconds", 0), elapsed = Json.Num(n, "elapsed", 0) + _host.StateAge;
                fill.anchorMax = new Vector2(n != null && total > 0 ? Mathf.Clamp01((float)(elapsed / total)) : 0f, 1f);
            });
            var row = Row(_content);
            Btn(row, "Powtórz", 0f, () => _host.Control("powtorz"));
            Btn(row, "Utnij", 0f, () => _host.Control("utnij"));
            Btn(row, Json.Bool(state, "muted") ? "Włącz" : "Wycisz", 0f, () => _host.Control("wycisz"));
        }

        private void BuildSettings(object state)
        {
            Section("Ustawienia");
            var tempo = Row(_content);
            Label(tempo, "Tempo");
            Btn(tempo, "–", 64f, () => _host.Control("wolniej"));
            var tv = Value(tempo);
            Btn(tempo, "+", 64f, () => _host.Control("szybciej"));
            _refresh.Add(() => tv.text = Json.Num(_host.State, "tempo", 1.0).ToString("0.0", CultureInfo.InvariantCulture).Replace('.', ',') + "x");

            var vol = Row(_content);
            Label(vol, "Głośność");
            Btn(vol, "–", 64f, () => Volume(-0.1));
            var vv = Value(vol);
            Btn(vol, "+", 64f, () => Volume(0.1));
            _refresh.Add(() => vv.text = Mathf.RoundToInt((float)Json.Num(_host.State, "volume", 1.0) * 100f) + "%");

            if (Json.Get(state, "stats") is bool stats)         // panele statystyk przy oknie podsumowania misji (E20)
                Check("Statystyki na koniec misji", stats, on =>
                    _host.Send(_host.Log.New("control").Str("cmd", "statystyki").Bool("value", on)));
        }

        private void Volume(double step)
        {
            double v = Math.Round(Math.Max(0.0, Math.Min(1.0, Json.Num(_host.State, "volume", 1.0) + step)) * 10.0) / 10.0;
            _host.Send(_host.Log.New("control").Str("cmd", "glosnosc").Num("value", v));
        }

        private void BuildToggles(object state)
        {
            var toggles = Json.Obj(state, "toggles");
            if (toggles == null) return;
            Section("Co czyta lektor");
            var names = new List<KeyValuePair<string, string>>();
            for (int i = 0; i < ToggleOrder.Length; i += 2)
                if (toggles.ContainsKey(ToggleOrder[i])) names.Add(new KeyValuePair<string, string>(ToggleOrder[i], ToggleOrder[i + 1]));
            foreach (var kv in toggles)
                if (names.FindIndex(p => p.Key == kv.Key) < 0) names.Add(new KeyValuePair<string, string>(kv.Key, kv.Key));
            foreach (var n in names)
            {
                string key = n.Key;
                Check(n.Value, toggles[key] is bool b && b, on =>
                    _host.Send(_host.Log.New("control").Str("cmd", "przelacznik")
                        .Raw("value", new JsonLine().Str("name", key).Bool("on", on).ToString())));
            }
        }

        /// <summary>Checkbox gry w osobnym wierszu.</summary>
        private void Check(string text, bool on, Action<bool> changed)
        {
            GameObject go = UnityEngine.Object.Instantiate(_toggleTemplate, _content, false);
            go.name = "Check";
            go.SetActive(true);
            var le = go.GetComponent<LayoutElement>() ?? go.AddComponent<LayoutElement>();
            le.ignoreLayout = false;
            le.minHeight = le.preferredHeight = 44f;
            le.preferredWidth = -1f;
            le.flexibleWidth = 1f;
            foreach (TMP_Text t in go.GetComponentsInChildren<TMP_Text>(true))
            {
                if (t.name == "Checkmark") continue;
                t.text = text;
                t.fontSize = 18f;
                t.enableAutoSizing = false;
                t.enableWordWrapping = false;
                t.overflowMode = TextOverflowModes.Ellipsis;
                t.alignment = TextAlignmentOptions.Left;
                t.color = on ? Light : Dim;
            }
            var tg = go.GetComponent<Toggle>();
            tg.group = null;
            tg.SetIsOnWithoutNotify(on);
            tg.onValueChanged = new Toggle.ToggleEvent();
            tg.onValueChanged.AddListener(v =>
            {
                try { changed(v); }
                catch (Exception e) { _log.Error("pl_menu_check", e); }
            });
            tg.interactable = true;
        }

        private void BuildHistory(object state)
        {
            var history = Json.List(state, "history");
            Section("Ostatnie kwestie");
            if (history == null || history.Count == 0)
            {
                AddText(_content, "Jeszcze nic nie zagrało.", 16f, Dim, TextAlignmentOptions.Left, false);
                return;
            }
            float age0 = Time.unscaledTime;
            foreach (object h in history.GetRange(0, Math.Min(HistoryShown, history.Count)))
            {
                long token = (long)Json.Num(h, "token");
                string speaker = Json.Str(h, "speaker", "?");
                bool muted = Json.Bool(h, "muted");
                double ago = Json.Num(h, "ago");
                var row = Row(_content);
                var head = AddText(row, "", 15f, Dim, TextAlignmentOptions.Left, false);
                head.gameObject.AddComponent<LayoutElement>().flexibleWidth = 1f;
                _refresh.Add(() => head.text = "<color=#DBB361>" + speaker + "</color> · " + Ago(ago + (Time.unscaledTime - age0)) + (muted ? " · wyciszona" : ""));
                Btn(row, "Graj", 76f, () => _host.Send(_host.Log.New("control").Str("cmd", "powtorz").Int("value", token)), 17f, 40f);
                Btn(row, "Zgłoś", 84f, () => _host.StartReport(token), 17f, 40f);
                AddText(_content, Json.Str(h, "text", ""), 17f, Light, TextAlignmentOptions.Left, false);
            }
        }

        private void BuildReports()
        {
            Section("Zgłoszenia");
            var row = Row(_content);
            Btn(row, "Zgłoś błąd", 0f, () => _host.StartReport(0));

            Section("Skróty klawiszowe");
            string sep = "<color=#EDE8DB> + </color>";             // „+” między klawiszami biały, klawisze złote
            for (int i = 0; i < KeyOrder.Length; i += 2)
            {
                string action = KeyOrder[i];
                Pair(KeyOrder[i + 1], () => _host.KeyLabel(action, sep), 92f);
            }
            var note = AddText(_content, "Pozostałe ustawienia znajdują się w pliku ustawienia.toml w folderze lektora.",
                15f, Dim, TextAlignmentOptions.Left, false);
            note.margin = new Vector4(0f, 10f, 0f, 0f);
        }

        /// <summary>Wiersz „opis – wartość”: opis jasny po lewej, wartość złota po prawej.</summary>
        private void Pair(string label, Func<string> value, float valueWidth)
        {
            var row = Row(_content);
            var l = AddText(row, label, 17f, Light, TextAlignmentOptions.Left, false);
            l.gameObject.AddComponent<LayoutElement>().flexibleWidth = 1f;
            var v = AddText(row, "", 17f, Gold, TextAlignmentOptions.Left, true);   // kolumna o stałej szerokości: „Ctrl” równo pod sobą
            v.enableWordWrapping = false;
            v.gameObject.AddComponent<LayoutElement>().preferredWidth = valueWidth;
            _refresh.Add(() => v.text = value());
        }

        private static string Ago(double s)
        {
            return s < 60 ? (int)s + " s temu" : (int)(s / 60) + " min temu";
        }

        // ---------- klocki uGUI ----------

        private static RectTransform NewRect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        private static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        private TMP_Text AddText(Transform parent, string text, float size, Color color, TextAlignmentOptions align, bool bold)
        {
            var rt = NewRect("Text", parent);
            var t = rt.gameObject.AddComponent<TextMeshProUGUI>();
            if (_font != null) t.font = _font;
            t.text = text;
            t.fontSize = size;
            t.color = color;
            t.alignment = align;
            t.richText = true;
            t.enableWordWrapping = true;
            t.raycastTarget = false;
            if (bold) t.fontStyle = FontStyles.Bold;
            return t;
        }

        private void Section(string title)
        {
            var t = AddText(_content, title, 21f, Gold, TextAlignmentOptions.Left, true);
            t.margin = new Vector4(0f, 18f, 0f, 4f);
        }

        private RectTransform Row(Transform parent)
        {
            var rt = NewRect("Row", parent);
            var h = rt.gameObject.AddComponent<HorizontalLayoutGroup>();
            h.spacing = 6f;
            h.childAlignment = TextAnchor.MiddleLeft;
            h.childControlWidth = h.childControlHeight = true;
            h.childForceExpandWidth = h.childForceExpandHeight = false;
            return rt;
        }

        private void Label(Transform row, string text)
        {
            var t = AddText(row, text, 18f, Light, TextAlignmentOptions.Left, false);
            var le = t.gameObject.AddComponent<LayoutElement>();
            le.preferredWidth = 120f;
        }

        private TMP_Text Value(Transform row)
        {
            var t = AddText(row, "", 22f, Gold, TextAlignmentOptions.Center, true);
            var le = t.gameObject.AddComponent<LayoutElement>();
            le.preferredWidth = 90f;
            return t;
        }

        private static void Spacer(Transform row)
        {
            var rt = NewRect("Spacer", row);
            rt.gameObject.AddComponent<LayoutElement>().flexibleWidth = 1f;
        }

        /// <summary>Niebieski przycisk gry; szerokość 0 = dzieli wiersz po równo z innymi.</summary>
        private Button Btn(Transform parent, string text, float width, Action onClick, float fontSize = 20f, float height = 52f)
        {
            GameObject go = UnityEngine.Object.Instantiate(_buttonTemplate, parent, false);
            go.name = "Button";
            go.SetActive(true);
            var img = go.GetComponent<Image>();
            if (img != null && img.sprite != null && img.sprite.border != Vector4.zero && img.type == Image.Type.Simple) img.type = Image.Type.Sliced;
            var le = go.GetComponent<LayoutElement>() ?? go.AddComponent<LayoutElement>();
            le.ignoreLayout = false;
            le.minWidth = le.preferredWidth = width > 0f ? width : -1f;
            le.flexibleWidth = width > 0f ? 0f : 1f;
            le.minHeight = le.preferredHeight = height;
            le.flexibleHeight = 0f;
            foreach (TMP_Text t in go.GetComponentsInChildren<TMP_Text>(true))
            {
                t.text = text;
                t.fontSize = fontSize;
                t.enableAutoSizing = false;
                t.richText = true;
                t.enableWordWrapping = false;
                t.overflowMode = TextOverflowModes.Ellipsis;
                var trt = t.rectTransform;
                trt.anchorMin = Vector2.zero;
                trt.anchorMax = Vector2.one;
                trt.offsetMin = new Vector2(8f, 0f);
                trt.offsetMax = new Vector2(-8f, 0f);
                t.alignment = TextAlignmentOptions.Center;
            }
            var b = go.GetComponent<Button>();
            b.onClick = new Button.ButtonClickedEvent();
            b.onClick.AddListener(() =>
            {
                try { onClick(); }
                catch (Exception e) { _log.Error("pl_menu_click", e); }
            });
            b.interactable = true;
            return b;
        }
    }
}
