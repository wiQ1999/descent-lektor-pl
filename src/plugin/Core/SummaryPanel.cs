using System;
using System.Collections.Generic;
using System.Globalization;
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
    /// 1250×920 (<c>Image_ScrollBG</c>), a łup przewija się w środku, więc panel dzielimy:
    /// kafelki i pasek walka/interakcje w wolnym polu okna pod „Czasem” (<c>Group_Time</c>), ataki według broni
    /// w panelu po lewej, drużyna i łup w panelu po prawej, nad przyciskiem „Dalej” (prawy dolny róg ekranu).
    /// Płótno gry ma wysokość 1080 i szerokość zależną od proporcji ekranu; gdy na panel boczny zostaje mniej niż
    /// <see cref="SideMin"/>, zmniejszamy okno gry skalą i przywracamy ją po zamknięciu.
    ///
    /// Panel jest dzieckiem okna gry, więc znika i zanika razem z nim; przycisku „Dalej” nie dotykamy. Grafiki i czcionkę
    /// bierzemy z gry: tabliczka pola „Czas” i czcionka nazwy misji z okna, kamienne tło i ramka panelu wroga, ornament nagłówka,
    /// ikony akcji i łupu z pakietu d3/uitextures oraz okrągłe portrety bohaterów jak w UIHeroProgress.
    ///
    /// Podgląd (ustawienie <c>podsumowanie_podglad</c>, skrót Ctrl+P w misji): ten sam panel nad planszą, z ramką
    /// w miejscu okna gry, bez otwierania okna gry. Drugie naciśnięcie zamyka podgląd.
    /// </summary>
    internal sealed class SummaryPanel
    {
        private const float WindowW = 1250f, WindowH = 920f, WindowY = 30f;
        private const float SideMin = 280f, SideMax = 380f, Gap = 16f, Edge = 16f, ContinueClear = 140f, MinScale = 0.72f;
        private const int MaxBars = 8;
        private const float PadX = 22f, PadTop = 36f, PadBottom = 26f, FrameScale = 1.3f, TileInset = 20f, Portrait = 68f;
        private const string UiBundle = "d3/uitextures", UiPath = "assets/d3/textures/ui/";
        // Dół pola „Czas” w oknie gry według prefabu (Group_Time na -69,7, tło 84,6 od -64) i wysokość naszego pola:
        // dwa rzędy kafelków (2×58 + 6), pasek 20 i podpis 20 z odstępami 6.
        private const float TimeBottom = -218.3f, TileH = 58f, InnerHeight = 2f * 58f + 6f + 6f + 20f + 6f + 20f;
        private static readonly Color Light = new Color(0.93f, 0.91f, 0.86f);
        private static readonly Color Dim = new Color(0.70f, 0.67f, 0.62f);
        private static readonly Color Gold = new Color(0.86f, 0.70f, 0.38f);
        private static readonly Color CombatColor = new Color(0.72f, 0.30f, 0.24f);
        private static readonly Color InteractColor = new Color(0.30f, 0.52f, 0.76f);
        private static readonly Color Track = new Color(0f, 0f, 0f, 0.45f);
        private static readonly Color StoneTint = new Color(0.50f, 0.47f, 0.45f, 0.97f);
        private static readonly Color FrameTint = new Color(0.82f, 0.70f, 0.48f, 1f);
        private static readonly Color PanelFallback = new Color(0.12f, 0.10f, 0.09f, 0.94f);
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
        private Sprite _tileSprite;
        private Image.Type _tileType;
        private Color _tileColor = new Color(0.5f, 0.4f, 0.3f, 1f);
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

            // Pole w oknie pod „Czasem” (współrzędne okna, przed skalą).
            // Tło „Czasu” (Image_BG) wystaje pod Group_Time, więc dół liczymy z prostokątów jego elementów.
            var timeGroup = preview ? null : window.Find("Group_Time") as RectTransform;
            float tx = timeGroup != null ? timeGroup.anchoredPosition.x : 242f;
            float tTop = (timeGroup != null ? BottomIn(window, timeGroup) : TimeBottom) - 12f;
            float tW = timeGroup != null ? timeGroup.rect.width : 442f;
            float tBottom = -winH / 2f + 24f;
            bool innerFits = tTop - tBottom >= InnerHeight;

            var left = Box("LektorPL.SummaryLeft", root, new Vector2(1f, 1f), new Vector2(-halfW - Gap, top), new Vector2(side, top - bottom));
            float rightBottom = Mathf.Max(bottom, -h / 2f + ContinueClear);
            var right = Box("LektorPL.SummaryRight", root, new Vector2(0f, 1f), new Vector2(halfW + Gap, top), new Vector2(side, top - rightBottom));

            if (innerFits)
            {
                var inner = NewRect("LektorPL.SummaryInner", window);
                _built.Add(inner.gameObject);
                inner.anchorMin = inner.anchorMax = new Vector2(0.5f, 0.5f);
                inner.pivot = new Vector2(0.5f, 1f);
                inner.anchoredPosition = new Vector2(tx, tTop);
                inner.sizeDelta = new Vector2(tW, tTop - tBottom);
                Column(inner, 6f, 0);
                Tiles(inner, s, tW);
                Ratio(inner, s, false);
            }
            else
            {
                Tiles(left, s, side - 2f * PadX);
                Ratio(left, s, true);
            }
            Weapons(left, s, side - 2f * PadX);
            Team(right, s);
            Loot(right, s);

            _shown = s;
            _preview = preview;
            _log.Write(_log.New("summary_panel").Bool("preview", preview).Num("canvas_w", w).Num("scale", scale).Num("side", side)
                .Bool("inner", innerFits));
        }

        /// <summary>Najniższy punkt grupy i jej dzieci we współrzędnych okna (bez skali okna).</summary>
        private static float BottomIn(RectTransform window, RectTransform group)
        {
            var corners = new Vector3[4];
            float min = float.MaxValue;
            foreach (RectTransform rt in group.GetComponentsInChildren<RectTransform>(false))
            {
                rt.GetWorldCorners(corners);
                foreach (var c in corners) min = Mathf.Min(min, window.InverseTransformPoint(c).y);
            }
            return min == float.MaxValue ? TimeBottom : min;
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
            var t = dialog.transform;
            var tile = t.Find("Image_ScrollBG/Group_Time/Image_BG");
            var img = tile != null ? tile.GetComponent<Image>() : null;
            if (img != null) { _tileSprite = img.sprite; _tileType = img.type; _tileColor = img.color; }
        }

        // ---------- sekcje ----------

        private void Tiles(RectTransform parent, QuestStats s, float width)
        {
            var grid = NewRect("Tiles", parent);
            var g = grid.gameObject.AddComponent<GridLayoutGroup>();
            float cell = (width - 2f * 8f) / 3f;
            g.cellSize = new Vector2(cell, TileH);
            g.spacing = new Vector2(8f, 6f);
            g.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
            g.constraintCount = 3;
            g.childAlignment = TextAnchor.UpperCenter;
            Fixed(grid, TileH * 2f + 6f);
            Tile(grid, s.Rounds.ToString(Pl), "rundy");
            Tile(grid, Clock(s.SecondsPerRound), "śr. czas rundy");
            Tile(grid, s.Attacks.ToString(Pl), "ataki");
            Tile(grid, s.Interactions.ToString(Pl), "interakcje");
            Tile(grid, s.GoldPerRound.ToString(s.GoldPerRound < 10f ? "0.#" : "0", Pl), "złoto na rundę");
            Tile(grid, Loc("UI_DIFFICULTY_" + s.Difficulty.ToString().ToUpperInvariant()) ?? s.Difficulty.ToString(), "trudność");
        }

        private void Tile(RectTransform grid, string value, string label)
        {
            var rt = NewRect("Tile", grid);
            var bg = rt.gameObject.AddComponent<Image>();
            Paint(bg, _tileSprite, _tileType, _tileColor);
            // Tabliczka gry ma zwężone końce (ok. 20 jednostek z każdej strony), więc tekst trzymamy w środku.
            var v = AddText(rt, value, 26f, Light, TextAlignmentOptions.Center, true);
            Fit(v, 13f);
            Anchor(v.rectTransform, 0f, 0.40f, 1f, 1f, TileInset, 0f, -TileInset, -3f);
            var l = AddText(rt, label, 14f, Dim, TextAlignmentOptions.Center, false);
            Fit(l, 10f);
            Anchor(l.rectTransform, 0f, 0f, 1f, 0.42f, TileInset - 4f, 4f, -(TileInset - 4f), 0f);
        }

        private void Ratio(RectTransform parent, QuestStats s, bool header)
        {
            int total = s.CombatActions + s.Interactions;
            if (header) Header(parent, "Charakter misji");
            var bar = NewRect("Ratio", parent);
            Fixed(bar, 16f);
            var track = bar.gameObject.AddComponent<Image>();
            track.color = Track;
            track.raycastTarget = false;
            float p = total > 0 ? (float)s.CombatActions / total : 0f;
            if (total > 0)
            {
                Fill(bar, 0f, p, CombatColor);
                Fill(bar, p, 1f, InteractColor);
            }
            var legend = NewRect("Legend", parent);
            Fixed(legend, 26f);
            if (total == 0)
            {
                var none = AddText(legend, "brak akcji", 18f, Dim, TextAlignmentOptions.Left, false);
                Stretch(none.rectTransform);
                return;
            }
            int pc = Mathf.RoundToInt(p * 100f);
            bool icons = Icon(legend, "icon_action_combat", Color.white, 0f, 24f) != null;
            Icon(legend, "icon_action_interact", Color.white, 1f, 24f);
            float inset = icons ? 30f : 0f;
            var a = AddText(legend, "walka " + pc + "%", 18f, Light, TextAlignmentOptions.Left, false);
            Anchor(a.rectTransform, 0f, 0f, 0.5f, 1f, inset, 0f, 0f, 0f);
            var b = AddText(legend, "interakcje " + (100 - pc) + "%", 18f, Light, TextAlignmentOptions.Right, false);
            Anchor(b.rectTransform, 0.5f, 0f, 1f, 1f, 0f, 0f, -inset, 0f);
        }

        private void Weapons(RectTransform panel, QuestStats s, float width)
        {
            Header(panel, "Ataki według broni");
            var rows = new List<KeyValuePair<string, KeyValuePair<int, List<Color>>>>();
            foreach (var w in s.Weapons)
            {
                var colors = new List<Color>();
                foreach (int i in w.Heroes) colors.Add(s.Heroes[i].ColorLight);
                rows.Add(Row(Loc(w.NameKey) ?? w.Class.ToString(), w.Attacks, colors));
            }
            foreach (var hero in s.Heroes)
                if (hero.RuneAttacks > 0)
                    rows.Add(Row("Runa: " + HeroName(hero), hero.RuneAttacks, new List<Color> { hero.ColorLight }));
            rows.Sort((x, y) => y.Value.Key.CompareTo(x.Value.Key));
            if (rows.Count > MaxBars)
            {
                int rest = 0;
                for (int i = MaxBars - 1; i < rows.Count; i++) rest += rows[i].Value.Key;
                rows.RemoveRange(MaxBars - 1, rows.Count - MaxBars + 1);
                rows.Add(Row("inne", rest, new List<Color> { Dim }));
            }
            if (rows.Count == 0)
                Line(panel, "W tej misji nikt nie atakował.", 17f, Dim);
            int max = 1;
            foreach (var r in rows) max = Mathf.Max(max, r.Value.Key);
            foreach (var r in rows) Bar(panel, r.Key, r.Value.Key, max, r.Value.Value);

            // Legenda: kolory bohaterów w dwóch kolumnach.
            Spacer(panel, 8f);
            var grid = NewRect("Legend", panel);
            var g = grid.gameObject.AddComponent<GridLayoutGroup>();
            g.cellSize = new Vector2((width - 8f) / 2f, 24f);
            g.spacing = new Vector2(8f, 2f);
            g.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
            g.constraintCount = 2;
            Fixed(grid, ((s.Heroes.Count + 1) / 2) * 26f);
            foreach (var hero in s.Heroes)
            {
                var cell = NewRect("LegendItem", grid);
                var dot = NewRect("Dot", cell);
                Anchor(dot, 0f, 0.5f, 0f, 0.5f, 0f, -7f, 14f, 7f);
                var di = dot.gameObject.AddComponent<Image>();
                di.color = hero.ColorLight;
                di.raycastTarget = false;
                var t = AddText(cell, HeroName(hero), 16f, Light, TextAlignmentOptions.Left, false);
                Fit(t, 12f);
                Anchor(t.rectTransform, 0f, 0f, 1f, 1f, 20f, 0f, 0f, 0f);
            }
        }

        private static KeyValuePair<string, KeyValuePair<int, List<Color>>> Row(string name, int value, List<Color> colors)
        {
            return new KeyValuePair<string, KeyValuePair<int, List<Color>>>(name, new KeyValuePair<int, List<Color>>(value, colors));
        }

        /// <summary>Wiersz broni: nazwa i liczba nad paskiem na całą szerokość (nazwa nie dzieli miejsca z paskiem).</summary>
        private void Bar(RectTransform panel, string name, int value, int max, List<Color> colors)
        {
            var row = NewRect("Bar", panel);
            Fixed(row, 38f);
            var label = AddText(row, name, 17f, Light, TextAlignmentOptions.Left, false);
            Fit(label, 13f);
            Anchor(label.rectTransform, 0f, 1f, 1f, 1f, 0f, -22f, -40f, 0f);
            var v = AddText(row, value.ToString(Pl), 17f, Light, TextAlignmentOptions.Right, true);
            Anchor(v.rectTransform, 1f, 1f, 1f, 1f, -40f, -22f, 0f, 0f);
            var track = NewRect("Track", row);
            Anchor(track, 0f, 0f, 1f, 0f, 0f, 3f, 0f, 14f);
            var ti = track.gameObject.AddComponent<Image>();
            ti.color = Track;
            ti.raycastTarget = false;
            float frac = Mathf.Clamp01((float)value / max);
            if (colors.Count == 0) colors = new List<Color> { Dim };
            for (int i = 0; i < colors.Count; i++)                     // wspólna klasa: pasek dzielony między bohaterów
                Fill(track, frac * i / colors.Count, frac * (i + 1) / colors.Count, colors[i]);
        }

        private void Team(RectTransform panel, QuestStats s)
        {
            Header(panel, "Drużyna");
            foreach (var hero in s.Heroes)
            {
                bool shared = hero.SharedWith.Count > 0;
                var row = NewRect("Hero", panel);
                Fixed(row, shared ? 92f : 76f);
                var frame = NewRect("Portrait", row);
                Anchor(frame, 0f, 0.5f, 0f, 0.5f, 0f, -Portrait / 2f, Portrait, Portrait / 2f);
                var sprite = PortraitSprite(hero.PortraitPath);
                var pi = frame.gameObject.AddComponent<Image>();
                pi.raycastTarget = false;
                if (sprite != null) { pi.sprite = sprite; pi.preserveAspect = true; }
                else pi.color = hero.ColorDark;

                var text = NewRect("Text", row);
                Anchor(text, 0f, 0f, 1f, 1f, Portrait + 10f, 0f, 0f, 0f);
                var col = Column(text, 0f, 0);
                col.childAlignment = TextAnchor.MiddleLeft;
                var name = Line(text, HeroName(hero), 19f, hero.ColorLight, true);
                name.fontSizeMin = 14f;
                Line(text, HealthText(hero.Health), 14f, HealthColor(hero.Health));
                string fav = hero.Favorite.HasValue ? " · " + ClassName(hero.Favorite.Value) : "";
                IconLine(text, "icon_action_combat", hero.Attacks.ToString(Pl) + fav, 15f, Light);
                string feats = "wyzwania: " + hero.FeatsCompleted.ToString(Pl);
                if (hero.FeatGained > 0.001f) feats += " · postęp +" + hero.FeatGained.ToString("0.##", Pl);
                Line(text, feats, 14f, Dim);
                if (shared)
                {
                    var names = new List<string>();
                    foreach (int i in hero.SharedWith) names.Add(HeroName(s.Heroes[i]));
                    Line(text, "wspólna broń: " + string.Join(", ", names.ToArray()), 13f, Dim);
                }
            }
        }

        private void Loot(RectTransform panel, QuestStats s)
        {
            Header(panel, "Łup");
            LootRow(panel, "icon_coins", Color.white, "złoto", s.Gold);
            LootRow(panel, "icon_trinket", Light, "przedmioty", s.LootItems);
            LootRow(panel, "icon_materials", Light, "materiały", s.LootMaterials);
            LootRow(panel, "miniviewrecipe_bg", Color.white, "przepisy", s.LootRecipes);
            LootRow(panel, "icon_consumables", Light, "mikstury", s.LootConsumables);
        }

        private void LootRow(RectTransform panel, string icon, Color tint, string label, int value)
        {
            var row = NewRect("LootRow", panel);
            Fixed(row, 28f);
            bool hasIcon = Icon(row, icon, value > 0 ? tint : tint * new Color(1f, 1f, 1f, 0.45f), 0f, 24f) != null;
            var l = AddText(row, label, 17f, value > 0 ? Light : Dim, TextAlignmentOptions.Left, false);
            Fit(l, 13f);
            Anchor(l.rectTransform, 0f, 0f, 1f, 1f, hasIcon ? 32f : 0f, 0f, -56f, 0f);
            var v = AddText(row, value.ToString(Pl), 18f, value > 0 ? Light : Dim, TextAlignmentOptions.Right, true);
            Anchor(v.rectTransform, 1f, 0f, 1f, 1f, -56f, 0f, 0f, 0f);
        }

        // ---------- klocki ----------

        /// <summary>Panel boczny: kamienne tło i ozdobna ramka z panelu wroga gry; bez grafik zwykły ciemny prostokąt.</summary>
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
            var stone = Ui("enemytab_bg");
            if (stone != null) { bg.sprite = stone; bg.type = Image.Type.Tiled; bg.color = StoneTint; }   // rozciągnięty kamień robi smugi
            else bg.color = PanelFallback;
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

        private static void Paint(Image img, Sprite sprite, Image.Type type, Color color)
        {
            img.sprite = sprite;
            img.type = sprite != null && sprite.border != Vector4.zero && type == Image.Type.Simple ? Image.Type.Sliced : type;
            img.color = color;
            img.raycastTarget = false;
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

        /// <summary>Wiersz z ikoną gry na początku (np. skrzyżowane miecze przy atakach).</summary>
        private void IconLine(RectTransform parent, string icon, string text, float size, Color color)
        {
            var row = NewRect("IconLine", parent);
            Fixed(row, size + 4f);
            bool has = Icon(row, icon, Color.white, 0f, size + 4f) != null;
            var t = AddText(row, text, size, color, TextAlignmentOptions.Left, false);
            Fit(t, Mathf.Max(10f, size - 4f));
            Anchor(t.rectTransform, 0f, 0f, 1f, 1f, has ? size + 8f : 0f, 0f, 0f, 0f);
        }

        /// <summary>Ikona z grafik gry przy lewej (side 0) albo prawej (side 1) krawędzi wiersza; null, gdy jej brak.</summary>
        private Image Icon(RectTransform row, string sprite, Color tint, float side, float size)
        {
            var sp = Ui(sprite);
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

        private static string HeroName(QuestStats.HeroRow h)
        {
            return Loc(h.NameKey) ?? h.HeroId;
        }

        private static string ClassName(WeaponClasses c)
        {
            return c == WeaponClasses.Rune ? "runa" : Loc(QuestStats.ClassKey(c)) ?? c.ToString();
        }

        private static string HealthText(HeroHealth h)
        {
            switch (h)
            {
                case HeroHealth.MinorInjury: return "lekka rana";
                case HeroHealth.MajorInjury: return "ciężka rana";
                case HeroHealth.Defeated: return "pokonanie";
                default: return "bez ran";
            }
        }

        private static Color HealthColor(HeroHealth h)
        {
            switch (h)
            {
                case HeroHealth.MinorInjury: return new Color(0.95f, 0.66f, 0.30f);
                case HeroHealth.MajorInjury: return new Color(0.92f, 0.36f, 0.30f);
                case HeroHealth.Defeated: return new Color(0.75f, 0.20f, 0.20f);
                default: return new Color(0.55f, 0.80f, 0.50f);
            }
        }

        private static string Hex(Color c)
        {
            return ColorUtility.ToHtmlStringRGB(c);
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
            try { return SingletonBehaviour<PersistentGameObject>.Instance.ABLoader.LoadAsset<Sprite>(path); }
            catch (Exception e) { _log.Error("summary_portrait", e); return null; }
        }
    }
}
