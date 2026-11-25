using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using FFG.Core;
using FFG.D3;
using FFG.D3.UI;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace LektorPL.Core
{
    /// <summary>
    /// Panel statystyk w oknie podsumowania misji gry (E20, D114). Okno gry (<c>Panel_QuestSummary</c>) ma stały rozmiar
    /// 1250×920 (<c>Image_ScrollBG</c>), a łup przewija się w środku, więc panele stoją po bokach okna:
    /// po lewej wykresy bohaterów (ataki bohaterów i wyzwania malejąco, postawy jako proporcja; portret i nazwa),
    /// po prawej balans gry (walka/interakcje), przebieg misji i łup (ikona, nazwa, wartość), nad przyciskiem „Dalej”.
    /// Płótno gry ma wysokość 1080 i szerokość zależną od proporcji ekranu; gdy na panel boczny zostaje mniej niż
    /// <see cref="SideMin"/>, zmniejszamy okno gry skalą i przywracamy ją po zamknięciu.
    ///
    /// Panel jest dzieckiem okna gry, więc znika i zanika razem z nim; przycisku „Dalej” nie dotykamy. Grafiki i czcionkę
    /// bierzemy z gry: czcionka nazwy misji z okna, ramka panelu wroga na półprzezroczystym przyciemnieniu, ornament nagłówka,
    /// ikony akcji i łupu z pakietu d3/uitextures oraz okrągłe portrety bohaterów jak w UIHeroProgress.
    /// Każda sekcja to nagłówek i wiersze z jedną wielkością tekstu (<see cref="Section"/>).
    ///
    /// Włączanie: <c>[podsumowanie] statystyki</c> w ustawieniach na start, potem przełącznik w menu lektora (<see cref="Enabled"/>).
    /// Podgląd (<c>[podsumowanie] podglad</c>, skrót Ctrl+P w misji): ten sam panel nad planszą, z ramką
    /// w miejscu okna gry, bez otwierania okna gry. Drugie naciśnięcie zamyka podgląd.
    /// </summary>
    internal sealed class SummaryPanel
    {
        private const float WindowW = 1250f, WindowH = 920f, WindowY = 30f;
        private const float SideMin = 280f, SideMax = 380f, Gap = 16f, Edge = 16f, ContinueClear = 140f, MinScale = 0.72f;
        private const float PadX = 22f, PadTop = 36f, PadBottom = 26f, FrameScale = 1.3f;
        // Wykresy: wiersz (nazwa nad paskiem), okrągły portret, początek tekstu i paska, kolumna wartości, odstęp sekcji.
        private const float BarH = 42f, IconW = 30f, LabelX = IconW + 8f, ValueW = 44f, SectionGap = 10f;
        // Teksty wierszy: wielkość bazowa i najmniejsza po dopasowaniu (jedna w całej sekcji, Section).
        private const float RowSize = 17f, RowMin = 11f;
        private const string UiBundle = "d3/uitextures", UiPath = "assets/d3/textures/ui/";
        private static readonly Color Light = new Color(0.93f, 0.91f, 0.86f);
        private static readonly Color Dim = new Color(0.70f, 0.67f, 0.62f);
        private static readonly Color Gold = new Color(0.86f, 0.70f, 0.38f);
        private static readonly Color CombatColor = new Color(0.72f, 0.30f, 0.24f);
        private static readonly Color InteractColor = new Color(0.30f, 0.52f, 0.76f);
        private static readonly Color Track = new Color(0f, 0f, 0f, 0.45f);
        private static readonly Color FrameTint = new Color(0.82f, 0.70f, 0.48f, 1f);
        private static readonly Color PanelShade = new Color(0.04f, 0.03f, 0.03f, 0.72f);   // przyciemnienie: plansza prześwituje
        private static readonly CultureInfo Pl = CultureInfo.GetCultureInfo("pl-PL");

        private readonly EventLog _log;
        private readonly bool _previewEnabled;
        private readonly List<Hotkey> _previewKeys = Hotkey.ParseList("Ctrl+P");

        private QuestStats _shown;
        private bool _preview;
        private readonly List<GameObject> _built = new List<GameObject>();
        private List<TMP_Text> _rows;                 // teksty wierszy bieżącej sekcji (Section)
        private RectTransform _scaledWindow;
        private Vector3 _windowScale;

        // Styl z okna gry.
        private TMP_FontAsset _font;
        private readonly Dictionary<string, Sprite> _sprites = new Dictionary<string, Sprite>();

        public SummaryPanel(EventLog log, bool enabled, bool previewEnabled)
        {
            _log = log;
            Enabled = enabled;
            _previewEnabled = previewEnabled;
        }

        /// <summary>Panele włączone; wyłączenie zdejmuje widoczny panel w następnej klatce.</summary>
        public bool Enabled { get; set; }

        public void Update(Tracker tracker)
        {
            if (tracker == null) return;
            try
            {
                if (!Enabled)
                {
                    if (_built.Count > 0) Teardown();
                    return;
                }
                var dialog = Dialog();
                var stats = tracker.Summary;
                bool real = stats != null && dialog != null && dialog.IsVisible;
                if (_previewEnabled && Pressed() && !real)
                {
                    if (_preview) Teardown();
                    else ShowPreview(dialog, tracker);
                    return;
                }
                if (real)
                {
                    if (_preview || !ReferenceEquals(_shown, stats)) { Teardown(); Build(dialog, stats, false); }
                }
                else if (_shown != null && !_preview) Teardown();
                else if (_preview && (dialog == null || !SingletonBehaviour<GameData>.IsInitialized)) Teardown();
            }
            catch (Exception e)
            {
                _log.Error("summary_panel", e);
                try { Teardown(); } catch (Exception) { }
            }
        }

        private static UIQuestSummary Dialog()
        {
            return SingletonBehaviour<UIGame>.IsInitialized ? SingletonBehaviour<UIGame>.Instance.QuestSummaryDialog : null;
        }

        private bool Pressed()
        {
            foreach (var k in _previewKeys)
                if (k.Down()) return true;
            return false;
        }

        private void ShowPreview(UIQuestSummary dialog, Tracker tracker)
        {
            var gd = SingletonBehaviour<GameData>.IsInitialized ? SingletonBehaviour<GameData>.Instance.Data : null;
            if (dialog == null || gd == null || string.IsNullOrEmpty(gd.QuestId)) return;   // tylko w misji
            var stats = QuestStats.Read(gd, gd.QuestId);
            if (stats == null) return;
            // Czas misji do tej chwili, jak SetQuestTime przy zapisie gry, ale bez zmiany stanu gry.
            stats.Seconds += Mathf.Max(0f, Time.timeSinceLevelLoad - gd.QuestSummary.TimeSinceLastSave);
            _log.Write(stats.Describe(_log.New("quest_summary_preview").Str("kind", "quest_summary")));
            Build(dialog, stats, true);
        }

        // ---------- budowa ----------

        private void Build(UIQuestSummary dialog, QuestStats s, bool preview)
        {
            if (dialog.TextQuestName != null) _font = dialog.TextQuestName.font;
            var dialogRt = (RectTransform)dialog.transform;
            RectTransform root, window;
            if (preview) root = PreviewRoot(dialogRt, out window);
            else
            {
                root = dialogRt;
                window = dialogRt.Find("Image_ScrollBG") as RectTransform;
                if (window == null) { _log.Write(_log.New("summary_panel").Str("error", "no_window")); return; }
            }

            float w = root.rect.width, h = root.rect.height;
            if (w <= 0f || h <= 0f) { w = 1920f; h = 1080f; }
            float winW = window.rect.width > 0f ? window.rect.width : WindowW;
            float winH = window.rect.height > 0f ? window.rect.height : WindowH;
            float scale = 1f, side = (w - winW) / 2f - Gap - Edge;
            if (side < SideMin)
            {
                scale = Mathf.Clamp((w - 2f * (SideMin + Gap + Edge)) / winW, MinScale, 1f);
                side = (w - winW * scale) / 2f - Gap - Edge;
            }
            side = Mathf.Min(side, SideMax);
            if (!preview && scale < 0.999f)
            {
                _scaledWindow = window;
                _windowScale = window.localScale;
                window.localScale = new Vector3(scale, scale, 1f);
            }
            else if (preview) window.localScale = new Vector3(scale, scale, 1f);

            float winY = window.anchoredPosition.y;
            float top = winY + winH * scale / 2f, bottom = winY - winH * scale / 2f;
            float halfW = winW * scale / 2f;

            var left = Box("LektorPL.SummaryLeft", root, new Vector2(1f, 1f), new Vector2(-halfW - Gap, top), new Vector2(side, top - bottom));
            float rightBottom = Mathf.Max(bottom, -h / 2f + ContinueClear);
            var right = Box("LektorPL.SummaryRight", root, new Vector2(0f, 1f), new Vector2(halfW + Gap, top), new Vector2(side, top - rightBottom));

            // Lewy panel: wykresy bohaterów (ataki, wyzwania, postawy).
            HeroAttacks(left, s);
            Spacer(left, SectionGap);
            Feats(left, s);
            Spacer(left, SectionGap);
            Virtues(left, s);
            // Prawy panel: balans gry (walka/interakcje), przebieg misji i łup.
            Balance(right, s);
            Spacer(right, SectionGap);
            Mission(right, s);
            Spacer(right, SectionGap);
            Loot(right, s);

            _shown = s;
            _preview = preview;
            _log.Write(_log.New("summary_panel").Bool("preview", preview).Num("canvas_w", w).Num("scale", scale).Num("side", side));
        }

        private void Teardown()
        {
            foreach (var go in _built)
                if (go != null) UnityEngine.Object.Destroy(go);
            _built.Clear();
            if (_scaledWindow != null) _scaledWindow.localScale = _windowScale;
            _scaledWindow = null;
            _shown = null;
            _preview = false;
        }

        /// <summary>Podgląd: przyciemnienie nad planszą (łapie kliknięcia) i ramka w miejscu okna podsumowania gry.</summary>
        private RectTransform PreviewRoot(RectTransform dialogRt, out RectTransform window)
        {
            var root = NewRect("LektorPL.SummaryPreview", dialogRt.parent);
            Stretch(root);
            root.SetAsLastSibling();
            _built.Add(root.gameObject);
            AddImage(root, new Color(0f, 0f, 0f, 0.6f)).raycastTarget = true;   // kliknięcia nie trafiają w planszę
            window = NewRect("WindowFrame", root);
            window.anchoredPosition = new Vector2(0f, WindowY);
            window.sizeDelta = new Vector2(WindowW, WindowH);
            AddImage(window, new Color(1f, 1f, 1f, 0.06f));
            var note = AddText(window, "Podgląd panelu lektora (E20)\nTu stoi okno podsumowania gry.\nCtrl+P zamyka podgląd.",
                26f, Dim, TextAlignmentOptions.Center, false);
            Place(note.rectTransform, 0f, 120f, 900f, 160f);
            return root;
        }

        // ---------- sekcje: lewy panel (wykresy bohaterów) ----------

        /// <summary>Ataki: suma klas bohatera i runy, malejąco (OrderBy jest stabilne: remis w kolejności graczy).</summary>
        private void HeroAttacks(RectTransform panel, QuestStats s)
        {
            int max = Mathf.Max(1, s.Heroes.Count > 0 ? s.Heroes.Max(h => h.Attacks) : 0);
            Section(panel, "Ataki", () =>
            {
                foreach (var h in s.Heroes.OrderByDescending(x => x.Attacks))
                    ChartRow(panel, h, HeroName(h), h.Attacks.ToString(Pl), (float)h.Attacks / max);
            });
        }

        /// <summary>Wyzwania: przyrost postępu w misji (jak pasek w oknie gry), malejąco; przy imieniu liczba ukończonych.</summary>
        private void Feats(RectTransform panel, QuestStats s)
        {
            float max = Mathf.Max(1f, s.Heroes.Count > 0 ? s.Heroes.Max(h => h.FeatGained) : 0f);
            Section(panel, "Wyzwania", () =>
            {
                foreach (var h in s.Heroes.OrderByDescending(x => x.FeatGained))
                {
                    float gained = Mathf.Max(0f, h.FeatGained);
                    string name = HeroName(h);
                    if (h.FeatsCompleted > 0)
                        name += "  <size=13><color=#" + ColorUtility.ToHtmlStringRGB(Gold) + ">ukończone: " + h.FeatsCompleted.ToString(Pl) + "</color></size>";
                    ChartRow(panel, h, name, "+" + gained.ToString("0.#", Pl), gained / max);
                }
            });
        }

        /// <summary>Postawy: bieżące wartości obu postaw bohatera z zapisu gry (bez śledzenia wyborów w misji).</summary>
        private void Virtues(RectTransform panel, QuestStats s)
        {
            Section(panel, Loc("UI_VIRTUES") ?? "Postawy", () =>
            {
                foreach (var h in s.Heroes) VirtueRow(panel, h);
            });
        }

        /// <summary>Wiersz wykresu: portret, nad paskiem imię i wartość, pasek od lewej w kolorze bohatera.</summary>
        private void ChartRow(RectTransform panel, QuestStats.HeroRow hero, string name, string value, float frac)
        {
            var row = HeroRow(panel, hero, out RectTransform track);
            var label = RowText(row, name, TextAlignmentOptions.Left, false);
            Anchor(label.rectTransform, 0f, 1f, 1f, 1f, LabelX, -22f, -ValueW, 0f);
            var v = RowText(row, value, TextAlignmentOptions.Right, true);
            Anchor(v.rectTransform, 1f, 1f, 1f, 1f, -ValueW, -22f, 0f, 0f);
            Fill(track, 0f, Mathf.Clamp01(frac), hero.ColorLight);
        }

        /// <summary>
        /// Wiersz postawy: portret, nad paskiem postawa 1 po lewej i postawa 2 po prawej. Nazwy dzielą szerokość według
        /// swojej długości (krótka nie zabiera miejsca długiej). Pasek rośnie od środka (50/50) w stronę przeważającej
        /// postawy o nadwyżkę jej udziału ponad połowę; znacznik na środku pokazuje równowagę.
        /// </summary>
        private void VirtueRow(RectTransform panel, QuestStats.HeroRow hero)
        {
            var row = HeroRow(panel, hero, out RectTransform track);
            var a = RowText(row, Loc(hero.VirtueOneKey) ?? hero.VirtueOneKey, TextAlignmentOptions.Left, false);
            var b = RowText(row, Loc(hero.VirtueTwoKey) ?? hero.VirtueTwoKey, TextAlignmentOptions.Right, false);
            float wa = a.GetPreferredValues(a.text).x, wb = b.GetPreferredValues(b.text).x;
            float f = wa + wb > 0f ? Mathf.Clamp(wa / (wa + wb), 0.2f, 0.8f) : 0.5f;
            // Granica nazw w ułamku f szerokości paska (pasek zaczyna się przy LabelX): f·W + LabelX·(1 − f).
            Anchor(a.rectTransform, 0f, 1f, f, 1f, LabelX, -22f, LabelX * (1f - f) - 3f, 0f);
            Anchor(b.rectTransform, f, 1f, 1f, 1f, LabelX * (1f - f) + 3f, -22f, 0f, 0f);
            int total = hero.VirtueOne + hero.VirtueTwo;
            float lean = total > 0 ? (float)hero.VirtueOne / total - 0.5f : 0f;      // > 0: przeważa postawa 1
            if (lean > 0f) Fill(track, 0.5f - lean, 0.5f, hero.ColorLight);
            else Fill(track, 0.5f, 0.5f - lean, hero.ColorLight);
            var mid = NewRect("Mid", track);                                      // znacznik równowagi 50/50
            mid.anchorMin = new Vector2(0.5f, -0.25f);
            mid.anchorMax = new Vector2(0.5f, 1.25f);
            mid.sizeDelta = new Vector2(2f, 0f);
            AddImage(mid, new Color(0f, 0f, 0f, 0.8f));
        }

        /// <summary>Szkielet wiersza bohatera: okrągły portret przy lewej krawędzi i pusty pasek pod miejscem na tekst.</summary>
        private RectTransform HeroRow(RectTransform panel, QuestStats.HeroRow hero, out RectTransform track)
        {
            var row = NewRect("HeroRow", panel);
            Fixed(row, BarH - 4f);
            var icon = NewRect("HeroIcon", row);
            icon.anchorMin = icon.anchorMax = icon.pivot = new Vector2(0f, 0.5f);
            icon.anchoredPosition = Vector2.zero;
            icon.sizeDelta = new Vector2(IconW, IconW);
            var sprite = PortraitSprite(hero.PortraitPath);
            var img = AddImage(icon, sprite != null ? Color.white : hero.ColorLight);   // bez portretu: kółko w kolorze bohatera
            img.sprite = sprite ?? Ui("generic_circle_sprite");
            img.preserveAspect = true;
            track = NewRect("Track", row);
            Anchor(track, 0f, 0f, 1f, 0f, LabelX, 3f, 0f, 14f);
            AddImage(track, Track);
            return row;
        }

        // ---------- sekcje: prawy panel (balans gry, przebieg misji, łup) ----------

        /// <summary>Balans gry: legenda z ikonami i procentami nad paskiem walka/interakcje całej drużyny.</summary>
        private void Balance(RectTransform panel, QuestStats s)
        {
            int total = s.CombatActions + s.Interactions;
            float p = total > 0 ? (float)s.CombatActions / total : 0f;
            Section(panel, "Balans gry", () =>
            {
                var legend = NewRect("Legend", panel);
                Fixed(legend, 26f);
                if (total == 0)
                {
                    Stretch(RowText(legend, "brak akcji", TextAlignmentOptions.Left, false).rectTransform);
                    return;
                }
                int pc = Mathf.RoundToInt(p * 100f);
                Icon(legend, "icon_action_combat", Color.white, 0f, 22f, true);
                Icon(legend, "icon_action_interact", Color.white, 1f, 22f, true);
                var a = RowText(legend, "walka " + pc + "%", TextAlignmentOptions.Left, false);
                Anchor(a.rectTransform, 0f, 0f, 0.5f, 1f, 28f, 0f, 0f, 0f);
                var b = RowText(legend, "interakcje " + (100 - pc) + "%", TextAlignmentOptions.Right, false);
                Anchor(b.rectTransform, 0.5f, 0f, 1f, 1f, 0f, 0f, -28f, 0f);
            });
            var bar = NewRect("Ratio", panel);
            Fixed(bar, 14f);
            AddImage(bar, Track);
            Fill(bar, 0f, p, CombatColor);
            if (total > 0) Fill(bar, p, 1f, InteractColor);
        }

        /// <summary>Przebieg misji: wartości jedna pod drugą, każda z ikoną gry.</summary>
        private void Mission(RectTransform panel, QuestStats s)
        {
            Section(panel, "Przebieg misji", () =>
            {
                StatRow(panel, "icon_movement", "rundy", s.Rounds.ToString(Pl));
                StatRow(panel, "generic/generic_loadingindicator", "śr. czas rundy", Clock(s.SecondsPerRound));
                StatRow(panel, "icon_action_combat", "ataki", s.Attacks.ToString(Pl), white: true);
                StatRow(panel, "icon_action_interact", "interakcje", s.Interactions.ToString(Pl), white: true);
                StatRow(panel, "icon_coins", "złoto na rundę", s.GoldPerRound.ToString(s.GoldPerRound < 10f ? "0.#" : "0", Pl));
            });
        }

        private void Loot(RectTransform panel, QuestStats s)
        {
            Section(panel, "Łup", () =>
            {
                StatRow(panel, "icon_coins", "złoto", s.Gold.ToString(Pl));
                StatRow(panel, "icon_trinket", "przedmioty", s.LootItems.ToString(Pl), tint: Light);
                StatRow(panel, "icon_materials", "materiały", s.LootMaterials.ToString(Pl), tint: Light);
                StatRow(panel, "miniviewrecipe_bg", "przepisy", s.LootRecipes.ToString(Pl));
                StatRow(panel, "icon_consumables", "mikstury", s.LootConsumables.ToString(Pl), tint: Light);
            });
        }

        /// <summary>
        /// Wiersz „ikona, nazwa … wartość”, wszystkie w jednym kolorze, także przy zerze.
        /// <paramref name="white"/>: czarna ikona akcji z HUD w odwróconych kolorach; <paramref name="tint"/>: kolor ikony.
        /// </summary>
        private void StatRow(RectTransform panel, string icon, string label, string value, bool white = false, Color? tint = null)
        {
            var row = NewRect("StatRow", panel);
            Fixed(row, 28f);
            Icon(row, icon, tint ?? Color.white, 0f, 24f, white);
            var l = RowText(row, label, TextAlignmentOptions.Left, false);
            Anchor(l.rectTransform, 0f, 0f, 1f, 1f, 32f, 0f, -110f, 0f);
            var v = RowText(row, value, TextAlignmentOptions.Right, true);
            Anchor(v.rectTransform, 1f, 0f, 1f, 1f, -110f, 0f, 0f, 0f);
        }

        private static string HeroName(QuestStats.HeroRow h)
        {
            return Loc(h.NameKey) ?? h.HeroId;
        }

        // ---------- klocki ----------

        /// <summary>Panel boczny: półprzezroczyste przyciemnienie i ozdobna ramka z panelu wroga gry.</summary>
        private RectTransform Box(string name, RectTransform root, Vector2 pivot, Vector2 pos, Vector2 size)
        {
            var rt = NewRect(name, root);
            _built.Add(rt.gameObject);
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.pivot = pivot;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            AddImage(rt, PanelShade);
            var frameSprite = Ui("enemytab_frame");
            if (frameSprite != null)
            {
                var fr = NewRect("Frame", rt);
                Stretch(fr);
                fr.gameObject.AddComponent<LayoutElement>().ignoreLayout = true;
                var fi = AddImage(fr, FrameTint);
                fi.sprite = frameSprite;
                fi.type = Image.Type.Sliced;
                fi.pixelsPerUnitMultiplier = FrameScale;              // mniejsze narożniki ramki niż w panelu wroga
            }
            var col = rt.gameObject.AddComponent<VerticalLayoutGroup>();
            col.padding = new RectOffset((int)PadX, (int)PadX, (int)PadTop, (int)PadBottom);   // narożniki ramki nad nagłówkiem
            col.spacing = 4f;
            col.childAlignment = TextAnchor.UpperLeft;
            col.childControlWidth = col.childControlHeight = true;
            col.childForceExpandWidth = true;
            col.childForceExpandHeight = false;
            return rt;
        }

        private static void Fixed(RectTransform rt, float height)
        {
            var le = rt.gameObject.AddComponent<LayoutElement>();
            le.minHeight = le.preferredHeight = height;
            le.flexibleHeight = 0f;
        }

        private static void Spacer(RectTransform parent, float height)
        {
            Fixed(NewRect("Spacer", parent), height);
        }

        /// <summary>Nagłówek sekcji jak w oknach gry: złoty tekst na środku i ornament pod spodem.</summary>
        private void Header(RectTransform parent, string text)
        {
            var t = AddText(parent, text, 24f, Gold, TextAlignmentOptions.Center, true);
            Fit(t, 17f);
            Fixed(t.rectTransform, 30f);
            var line = Ui("underline");
            if (line == null) { Spacer(parent, 4f); return; }
            var rt = NewRect("Underline", parent);
            Fixed(rt, 18f);
            var img = AddImage(rt, Gold);
            img.sprite = line;
            img.preserveAspect = true;
        }

        /// <summary>Sekcja: nagłówek, potem wiersze z <paramref name="rows"/>; teksty wierszy dostają jedną wielkość.</summary>
        private void Section(RectTransform panel, string title, Action rows)
        {
            Header(panel, title);
            var previous = _rows;
            _rows = new List<TMP_Text>();
            try { rows(); }
            finally
            {
                var texts = _rows;
                _rows = previous;
                UniformSize(panel, texts);
            }
        }

        /// <summary>
        /// Ikona z grafik gry przy lewej (side 0) albo prawej (side 1) krawędzi wiersza; null, gdy jej brak.
        /// <paramref name="white"/>: kolory odwrócone (czarne ikony akcji z HUD stają się białe z ciemną poświatą).
        /// </summary>
        private Image Icon(RectTransform row, string sprite, Color tint, float side, float size, bool white = false)
        {
            var sp = white ? Inverted(sprite) : Ui(sprite);
            if (sp == null) return null;
            var rt = NewRect("Icon", row);
            rt.anchorMin = rt.anchorMax = new Vector2(side, 0.5f);
            rt.pivot = new Vector2(side, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = new Vector2(size, size);
            var img = AddImage(rt, tint);
            img.sprite = sp;
            img.preserveAspect = true;
            return img;
        }

        /// <summary>Tekst wiersza sekcji: jedna wielkość bazowa, zapamiętany do wyrównania w <see cref="UniformSize"/>.</summary>
        private TMP_Text RowText(Transform row, string text, TextAlignmentOptions align, bool bold)
        {
            var t = AddText(row, text, RowSize, Light, align, bold);
            Fit(t, RowMin);
            if (_rows != null) _rows.Add(t);
            return t;
        }

        /// <summary>
        /// Wszystkie teksty wierszy sekcji dostają jedną wielkość: najmniejszą, jaką wybrało dopasowanie
        /// któregokolwiek z nich (długie nazwy nie wyglądają wtedy na mniejsze od krótkich).
        /// </summary>
        private void UniformSize(RectTransform panel, List<TMP_Text> rows)
        {
            if (rows == null || rows.Count == 0 || !panel.gameObject.activeInHierarchy) return;   // nieaktywny: zostaje auto-size
            try
            {
                LayoutRebuilder.ForceRebuildLayoutImmediate(panel);         // szerokości wierszy przed pomiarem tekstu
                float size = RowSize;
                foreach (var t in rows)
                {
                    t.ForceMeshUpdate();
                    size = Mathf.Min(size, t.fontSize);                     // przy auto-size fontSize to wielkość dobrana
                }
                foreach (var t in rows)
                {
                    t.enableAutoSizing = false;
                    t.fontSize = size;
                }
            }
            catch (Exception e) { _log.Error("summary_rows", e); }
        }

        /// <summary>Tekst w jednym wierszu: najpierw zmniejsza czcionkę do <paramref name="min"/>, dopiero potem skraca.</summary>
        private static void Fit(TMP_Text t, float min)
        {
            t.enableWordWrapping = false;
            t.enableAutoSizing = true;
            t.fontSizeMax = t.fontSize;
            t.fontSizeMin = Mathf.Min(min, t.fontSize);
            t.overflowMode = TextOverflowModes.Ellipsis;
        }

        private static void Fill(RectTransform track, float from, float to, Color color)
        {
            if (to - from <= 0.0001f) return;
            var f = NewRect("Fill", track);
            f.anchorMin = new Vector2(from, 0f);
            f.anchorMax = new Vector2(to, 1f);
            f.offsetMin = f.offsetMax = Vector2.zero;
            AddImage(f, color);
        }

        private static Image AddImage(RectTransform rt, Color color)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.color = color;
            img.raycastTarget = false;
            return img;
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

        private static RectTransform NewRect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = parent.gameObject.layer;
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        private static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        private static void Anchor(RectTransform rt, float minX, float minY, float maxX, float maxY, float l, float b, float r, float t)
        {
            rt.anchorMin = new Vector2(minX, minY);
            rt.anchorMax = new Vector2(maxX, maxY);
            rt.offsetMin = new Vector2(l, b);
            rt.offsetMax = new Vector2(r, t);
        }

        private static void Place(RectTransform rt, float x, float y, float w, float h)
        {
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = new Vector2(x, y);
            rt.sizeDelta = new Vector2(w, h);
        }

        /// <summary>
        /// Kopia grafiki gry z odwróconymi kolorami (przezroczystość bez zmian). Tekstury gry nie są do odczytu,
        /// więc kopiujemy przez RenderTexture; przy błędzie zostaje oryginał.
        /// </summary>
        private Sprite Inverted(string name)
        {
            string key = name + "#white";
            if (_sprites.TryGetValue(key, out Sprite cached)) return cached;
            var src = Ui(name);
            Sprite result = null;
            if (src != null)
            {
                RenderTexture rt = null;
                var active = RenderTexture.active;
                try
                {
                    var tex = src.texture;
                    var r = src.textureRect;
                    int w = Mathf.RoundToInt(r.width), h = Mathf.RoundToInt(r.height);
                    rt = RenderTexture.GetTemporary(tex.width, tex.height, 0, RenderTextureFormat.ARGB32);
                    Graphics.Blit(tex, rt);
                    RenderTexture.active = rt;
                    var copy = new Texture2D(w, h, TextureFormat.RGBA32, false);
                    copy.ReadPixels(new Rect(r.x, r.y, w, h), 0, 0);
                    var px = copy.GetPixels32();
                    for (int i = 0; i < px.Length; i++)
                    {
                        px[i].r = (byte)(255 - px[i].r);
                        px[i].g = (byte)(255 - px[i].g);
                        px[i].b = (byte)(255 - px[i].b);
                    }
                    copy.SetPixels32(px);
                    copy.Apply(false, true);
                    result = Sprite.Create(copy, new Rect(0f, 0f, w, h), new Vector2(0.5f, 0.5f), src.pixelsPerUnit);
                }
                catch (Exception e) { _log.Error("summary_icon", e); }
                finally
                {
                    RenderTexture.active = active;
                    if (rt != null) RenderTexture.ReleaseTemporary(rt);
                }
            }
            _sprites[key] = result ?? src;
            return _sprites[key];
        }

        /// <summary>Grafika z pakietu interfejsu gry (<c>d3/uitextures</c>, wczytany przy starcie gry); null, gdy jej nie ma.</summary>
        private Sprite Ui(string name)
        {
            if (_sprites.TryGetValue(name, out Sprite s)) return s;
            s = null;
            try
            {
                if (SingletonBehaviour<PersistentGameObject>.IsInitialized)
                {
                    var bundle = SingletonBehaviour<PersistentGameObject>.Instance.ABLoader.GetBundle(UiBundle);
                    if (bundle != null) s = bundle.LoadAsset<Sprite>(UiPath + name + ".png");
                }
            }
            catch (Exception e) { _log.Error("summary_sprite", e); }
            if (s == null) _log.Write(_log.New("summary_sprite").Str("missing", name));
            _sprites[name] = s;
            return s;
        }

        // ---------- teksty ----------

        private static string Loc(string key)
        {
            if (string.IsNullOrEmpty(key)) return null;
            string s = FFGLocalization.Get(key, returnKeyOnMissing: false);
            return string.IsNullOrEmpty(s) ? null : s;
        }

        private static string Clock(float seconds)
        {
            int total = Mathf.RoundToInt(seconds);
            return total >= 3600 ? (total / 3600) + ":" + (total / 60 % 60).ToString("00") + ":" + (total % 60).ToString("00")
                                 : (total / 60) + ":" + (total % 60).ToString("00");
        }

        private Sprite PortraitSprite(string path)
        {
            if (string.IsNullOrEmpty(path) || !SingletonBehaviour<PersistentGameObject>.IsInitialized) return null;
            if (_sprites.TryGetValue(path, out Sprite cached)) return cached;   // portret stoi przy trzech wykresach
            Sprite s = null;
            try { s = SingletonBehaviour<PersistentGameObject>.Instance.ABLoader.LoadAsset<Sprite>(path); }
            catch (Exception e) { _log.Error("summary_portrait", e); }
            _sprites[path] = s;
            return s;
        }
    }
}
