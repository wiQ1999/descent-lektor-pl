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
    /// po lewej wykresy bohaterów (ataki bohaterów, ataki broni, wyzwania; portret i nazwa, słupki malejąco),
    /// po prawej przebieg misji i łup (ikona, nazwa, wartość) oraz balans gry (walka/interakcje), nad przyciskiem „Dalej”.
    /// Płótno gry ma wysokość 1080 i szerokość zależną od proporcji ekranu; gdy na panel boczny zostaje mniej niż
    /// <see cref="SideMin"/>, zmniejszamy okno gry skalą i przywracamy ją po zamknięciu.
    ///
    /// Panel jest dzieckiem okna gry, więc znika i zanika razem z nim; przycisku „Dalej” nie dotykamy. Grafiki i czcionkę
    /// bierzemy z gry: tabliczka pola „Czas” i czcionka nazwy misji z okna, ramka panelu wroga na półprzezroczystym przyciemnieniu, ornament nagłówka,
    /// ikony akcji i łupu z pakietu d3/uitextures oraz okrągłe portrety bohaterów jak w UIHeroProgress.
    ///
    /// Podgląd (ustawienie <c>podsumowanie_podglad</c>, skrót Ctrl+P w misji): ten sam panel nad planszą, z ramką
    /// w miejscu okna gry, bez otwierania okna gry. Drugie naciśnięcie zamyka podgląd.
    /// </summary>
    internal sealed class SummaryPanel
    {
        private const float WindowW = 1250f, WindowH = 920f, WindowY = 30f;
        private const float SideMin = 280f, SideMax = 380f, Gap = 16f, Edge = 16f, ContinueClear = 140f, MinScale = 0.72f;
        private const int MaxBars = 8, MinBars = 3;
        private const float PadX = 22f, PadTop = 36f, PadBottom = 26f, FrameScale = 1.3f;
        // Wykresy: słupek broni (nazwa nad paskiem), słupek bohatera, okrągły portret i kolumna wartości.
        private const float BarH = 42f, IconW = 30f, ValueW = 44f;
        // Lewy panel bez słupków broni: marginesy, trzy nagłówki (tekst, ornament, odstępy) i dwa odstępy między sekcjami.
        private const float LeftFixed = 36f + 26f + 3f * 56f + 2f * 10f + 8f;
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
        private readonly bool _enabled, _previewEnabled;
        private readonly List<Hotkey> _previewKeys = Hotkey.ParseList("Ctrl+P");

        private QuestStats _shown;
        private bool _preview;
        private readonly List<GameObject> _built = new List<GameObject>();
        private RectTransform _scaledWindow;
        private Vector3 _windowScale;

        // Styl z okna gry.
        private TMP_FontAsset _font;
        private readonly Dictionary<string, Sprite> _sprites = new Dictionary<string, Sprite>();

        public SummaryPanel(EventLog log, bool enabled, bool previewEnabled)
        {
            _log = log;
            _enabled = enabled;
            _previewEnabled = previewEnabled;
        }

        public void Update(Tracker tracker)
        {
            if (!_enabled || tracker == null) return;
            try
            {
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
            CaptureStyle(dialog);
            var dialogRt = (RectTransform)dialog.transform;
            RectTransform root, window;
            if (preview)
            {
                root = NewRect("LektorPL.SummaryPreview", dialogRt.parent);
                Stretch(root);
                root.SetAsLastSibling();
                _built.Add(root.gameObject);
                var dim = root.gameObject.AddComponent<Image>();
                dim.color = new Color(0f, 0f, 0f, 0.6f);
                dim.raycastTarget = true;           // kliknięcia nie trafiają w planszę
                window = NewRect("WindowFrame", root);
                window.anchoredPosition = new Vector2(0f, WindowY);
                window.sizeDelta = new Vector2(WindowW, WindowH);
                var frame = window.gameObject.AddComponent<Image>();
                frame.color = new Color(1f, 1f, 1f, 0.06f);
                frame.raycastTarget = false;
                var note = AddText(window, "Podgląd panelu lektora (E20)\nTu stoi okno podsumowania gry.\nCtrl+P zamyka podgląd.",
                    26f, Dim, TextAlignmentOptions.Center, false);
                Place(note.rectTransform, 0f, 120f, 900f, 160f);
            }
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

            // Lewy panel: wykresy bohaterów; słupków broni tyle, ile zmieści wysokość panelu (reszta jako „inne”).
            float heroBars = 2f * s.Heroes.Count * BarH;
            int bars = Mathf.Clamp(Mathf.FloorToInt((top - bottom - LeftFixed - heroBars) / BarH), MinBars, MaxBars);
            HeroAttacks(left, s);
            Spacer(left, 10f);
            Weapons(left, s, bars);
            Spacer(left, 10f);
            Feats(left, s);
            // Prawy panel: przebieg misji, łup i balans gry (walka/interakcje).
            Mission(right, s);
            Loot(right, s);
            Balance(right, s);

            _shown = s;
            _preview = preview;
            _log.Write(_log.New("summary_panel").Bool("preview", preview).Num("canvas_w", w).Num("scale", scale).Num("side", side)
                .Int("bars", bars));
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

        private void CaptureStyle(UIQuestSummary dialog)
        {
            if (dialog.TextQuestName != null) _font = dialog.TextQuestName.font;
        }

        // ---------- sekcje: lewy panel (wykresy bohaterów) ----------

        /// <summary>Ataki bohaterów: suma klas bohatera i runy, malejąco.</summary>
        private void HeroAttacks(RectTransform panel, QuestStats s)
        {
            Header(panel, "Ataki bohaterów");
            int max = 1;
            foreach (var h in s.Heroes) max = Mathf.Max(max, h.Attacks);
            foreach (var h in s.Heroes.OrderByDescending(x => x.Attacks))   // OrderBy jest stabilne: remis w kolejności graczy
                ChartRow(panel, h, HeroName(h), h.Attacks.ToString(Pl), (float)h.Attacks / max);
        }

        private void Weapons(RectTransform panel, QuestStats s, int maxBars)
        {
            Header(panel, "Ataki broni");
            var rows = new List<WeaponBar>();
            foreach (var w in s.Weapons)
                rows.Add(new WeaponBar { Name = Loc(w.NameKey) ?? w.Class.ToString(), Attacks = w.Attacks,
                                         Hero = w.Heroes.Count > 0 ? s.Heroes[w.Heroes[0]] : null });
            foreach (var hero in s.Heroes)
                if (hero.RuneAttacks > 0)
                    rows.Add(new WeaponBar { Name = "Runa", Attacks = hero.RuneAttacks, Hero = hero });
            rows = rows.OrderByDescending(r => r.Attacks).ToList();
            if (rows.Count > maxBars)
            {
                int rest = 0;
                for (int i = maxBars - 1; i < rows.Count; i++) rest += rows[i].Attacks;
                rows.RemoveRange(maxBars - 1, rows.Count - maxBars + 1);
                rows.Add(new WeaponBar { Name = "inne", Attacks = rest });
            }
            if (rows.Count == 0)
                Line(panel, "W tej misji nikt nie atakował.", 17f, Dim);
            int max = 1;
            foreach (var r in rows) max = Mathf.Max(max, r.Attacks);
            foreach (var r in rows) ChartRow(panel, r.Hero, r.Name, r.Attacks.ToString(Pl), (float)r.Attacks / max);
        }

        private sealed class WeaponBar
        {
            public string Name;
            public int Attacks;
            public QuestStats.HeroRow Hero;   // null: „inne”
        }

        /// <summary>Wyzwania: przyrost postępu w misji (jak pasek w oknie gry), malejąco; przy imieniu liczba ukończonych.</summary>
        private void Feats(RectTransform panel, QuestStats s)
        {
            Header(panel, "Wyzwania");
            float max = 1f;
            foreach (var h in s.Heroes) max = Mathf.Max(max, h.FeatGained);
            foreach (var h in s.Heroes.OrderByDescending(x => x.FeatGained))
            {
                float gained = Mathf.Max(0f, h.FeatGained);
                string name = HeroName(h);
                if (h.FeatsCompleted > 0)
                    name += "  <size=13><color=#" + ColorUtility.ToHtmlStringRGB(Gold) + ">ukończone: " + h.FeatsCompleted.ToString(Pl) + "</color></size>";
                ChartRow(panel, h, name, "+" + gained.ToString("0.#", Pl), gained / max);
            }
        }

        /// <summary>
        /// Wiersz wykresu: okrągły portret bohatera, nad paskiem nazwa (imię albo broń) i wartość, pasek w kolorze bohatera.
        /// Bez bohatera („inne”) bez portretu i w szarym kolorze.
        /// </summary>
        private void ChartRow(RectTransform panel, QuestStats.HeroRow hero, string name, string value, float frac)
        {
            var row = NewRect("ChartRow", panel);
            Fixed(row, BarH - 4f);
            float x = 0f;
            if (hero != null) { HeroIcon(row, hero, 0f); x = IconW + 8f; }
            var label = AddText(row, name, 17f, Light, TextAlignmentOptions.Left, false);
            Fit(label, 12f);
            Anchor(label.rectTransform, 0f, 1f, 1f, 1f, x, -22f, -ValueW, 0f);
            var v = AddText(row, value, 17f, Light, TextAlignmentOptions.Right, true);
            Fit(v, 12f);
            Anchor(v.rectTransform, 1f, 1f, 1f, 1f, -ValueW, -22f, 0f, 0f);
            var track = NewRect("Track", row);
            Anchor(track, 0f, 0f, 1f, 0f, x, 3f, 0f, 14f);
            var ti = track.gameObject.AddComponent<Image>();
            ti.color = Track;
            ti.raycastTarget = false;
            Fill(track, 0f, Mathf.Clamp01(frac), hero != null ? hero.ColorLight : Dim);
        }

        /// <summary>Mały okrągły portret bohatera przy lewej krawędzi wiersza (bez portretu: kółko w kolorze bohatera).</summary>
        private void HeroIcon(RectTransform row, QuestStats.HeroRow hero, float side)
        {
            var rt = NewRect("HeroIcon", row);
            rt.anchorMin = rt.anchorMax = new Vector2(side, 0.5f);
            rt.pivot = new Vector2(side, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = new Vector2(IconW, IconW);
            var img = rt.gameObject.AddComponent<Image>();
            img.raycastTarget = false;
            var sprite = PortraitSprite(hero.PortraitPath);
            if (sprite != null) { img.sprite = sprite; img.preserveAspect = true; }
            else { img.sprite = Ui("generic_circle_sprite"); img.color = hero.ColorLight; }
        }

        // ---------- sekcje: prawy panel (przebieg misji, łup, balans gry) ----------

        /// <summary>Przebieg misji: wartości jedna pod drugą, każda z ikoną gry.</summary>
        private void Mission(RectTransform panel, QuestStats s)
        {
            Header(panel, "Przebieg misji");
            StatRow(panel, "icon_movement", false, "rundy", s.Rounds.ToString(Pl));
            StatRow(panel, "generic/generic_loadingindicator", false, "śr. czas rundy", Clock(s.SecondsPerRound));
            StatRow(panel, "icon_action_combat", true, "ataki", s.Attacks.ToString(Pl));
            StatRow(panel, "icon_action_interact", true, "interakcje", s.Interactions.ToString(Pl));
            StatRow(panel, "icon_coins", false, "złoto na rundę", s.GoldPerRound.ToString(s.GoldPerRound < 10f ? "0.#" : "0", Pl));
            StatRow(panel, "icon_damage", false, "trudność", Loc("UI_DIFFICULTY_" + s.Difficulty.ToString().ToUpperInvariant()) ?? s.Difficulty.ToString());
        }

        private void Loot(RectTransform panel, QuestStats s)
        {
            Spacer(panel, 10f);
            Header(panel, "Łup");
            StatRow(panel, "icon_coins", false, "złoto", s.Gold.ToString(Pl));
            StatRow(panel, "icon_trinket", false, "przedmioty", s.LootItems.ToString(Pl));
            StatRow(panel, "icon_materials", false, "materiały", s.LootMaterials.ToString(Pl));
            StatRow(panel, "miniviewrecipe_bg", false, "przepisy", s.LootRecipes.ToString(Pl));
            StatRow(panel, "icon_consumables", false, "mikstury", s.LootConsumables.ToString(Pl));
        }

        /// <summary>Balans gry: osobna sekcja pod łupem, pasek walka/interakcje z ikonami i procentami pod spodem.</summary>
        private void Balance(RectTransform panel, QuestStats s)
        {
            Spacer(panel, 10f);
            Header(panel, "Balans gry");
            int total = s.CombatActions + s.Interactions;
            var bar = NewRect("Ratio", panel);
            Fixed(bar, 14f);
            var track = bar.gameObject.AddComponent<Image>();
            track.color = Track;
            track.raycastTarget = false;
            float p = total > 0 ? (float)s.CombatActions / total : 0f;
            if (total > 0)
            {
                Fill(bar, 0f, p, CombatColor);
                Fill(bar, p, 1f, InteractColor);
            }
            var legend = NewRect("Legend", panel);
            Fixed(legend, 26f);
            if (total == 0)
            {
                var none = AddText(legend, "brak akcji", 16f, Light, TextAlignmentOptions.Left, false);
                Stretch(none.rectTransform);
                return;
            }
            int pc = Mathf.RoundToInt(p * 100f);
            Icon(legend, "icon_action_combat", Color.white, 0f, 22f, true);
            Icon(legend, "icon_action_interact", Color.white, 1f, 22f, true);
            var a = AddText(legend, "walka " + pc + "%", 16f, Light, TextAlignmentOptions.Left, false);
            Fit(a, 11f);
            Anchor(a.rectTransform, 0f, 0f, 0.5f, 1f, 28f, 0f, 0f, 0f);
            var b = AddText(legend, "interakcje " + (100 - pc) + "%", 16f, Light, TextAlignmentOptions.Right, false);
            Fit(b, 11f);
            Anchor(b.rectTransform, 0.5f, 0f, 1f, 1f, 0f, 0f, -28f, 0f);
        }

        /// <summary>Wiersz „ikona, nazwa … wartość”; wszystkie wiersze w jednym kolorze, także przy zerze.</summary>
        private void StatRow(RectTransform panel, string icon, bool white, string label, string value)
        {
            var row = NewRect("StatRow", panel);
            Fixed(row, 28f);
            var tint = icon == "icon_trinket" || icon == "icon_materials" || icon == "icon_consumables" ? Light : Color.white;
            if (icon != null) Icon(row, icon, tint, 0f, 24f, white);
            var l = AddText(row, label, 17f, Light, TextAlignmentOptions.Left, false);
            Fit(l, 13f);
            Anchor(l.rectTransform, 0f, 0f, 1f, 1f, 32f, 0f, -110f, 0f);
            var v = AddText(row, value, 18f, Light, TextAlignmentOptions.Right, true);
            Fit(v, 12f);
            Anchor(v.rectTransform, 1f, 0f, 1f, 1f, -110f, 0f, 0f, 0f);
        }

        private static string HeroName(QuestStats.HeroRow h)
        {
            string s = Loc(h.NameKey);
            return string.IsNullOrEmpty(s) ? h.HeroId : s;
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
            var bg = rt.gameObject.AddComponent<Image>();
            bg.raycastTarget = false;
            bg.color = PanelShade;
            var frameSprite = Ui("enemytab_frame");
            if (frameSprite != null)
            {
                var fr = NewRect("Frame", rt);
                Stretch(fr);
                fr.gameObject.AddComponent<LayoutElement>().ignoreLayout = true;
                var fi = fr.gameObject.AddComponent<Image>();
                fi.sprite = frameSprite;
                fi.type = Image.Type.Sliced;
                fi.pixelsPerUnitMultiplier = FrameScale;              // mniejsze narożniki ramki niż w panelu wroga
                fi.color = FrameTint;
                fi.raycastTarget = false;
            }
            var col = Column(rt, 4f, 0);
            col.padding = new RectOffset((int)PadX, (int)PadX, (int)PadTop, (int)PadBottom);   // narożniki ramki nad nagłówkiem
            return rt;
        }

        private static VerticalLayoutGroup Column(RectTransform rt, float spacing, int padding)
        {
            var v = rt.gameObject.AddComponent<VerticalLayoutGroup>();
            v.padding = new RectOffset(padding, padding, padding, padding);
            v.spacing = spacing;
            v.childAlignment = TextAnchor.UpperLeft;
            v.childControlWidth = v.childControlHeight = true;
            v.childForceExpandWidth = true;
            v.childForceExpandHeight = false;
            return v;
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
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = line;
            img.preserveAspect = true;
            img.color = Gold;
            img.raycastTarget = false;
        }

        private TMP_Text Line(RectTransform parent, string text, float size, Color color, bool bold = false)
        {
            var t = AddText(parent, text, size, color, TextAlignmentOptions.Left, bold);
            Fit(t, Mathf.Max(10f, size - 4f));
            Fixed(t.rectTransform, size + 4f);
            return t;
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
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = sp;
            img.preserveAspect = true;
            img.color = tint;
            img.raycastTarget = false;
            return img;
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
            var img = f.gameObject.AddComponent<Image>();
            img.color = color;
            img.raycastTarget = false;
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
