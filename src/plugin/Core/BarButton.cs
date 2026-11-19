using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using FFG.D3.UI;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace LektorPL.Core
{
    /// <summary>
    /// Przycisk lektora na dolnym pasku gry, obok zębatki i drużyny (próba).
    ///
    /// Kopia przycisku drużyny (<c>UIGame.SubmenuPartyButton</c>) powstaje pod nieaktywnym rodzicem, więc skrypty gry
    /// w kopii nie startują; usuwamy je, zanim kopia trafi na płótno. Obrazy wspólne z zębatką (ramka) zostają,
    /// a ikona drużyny znika i w jej miejsce idzie napis „PL” czcionką gry. Kliknięcie otwiera menu lektora.
    /// Pozycja co klatkę: drużyna + (drużyna − zębatka), widoczność i przezroczystość jak przycisk drużyny.
    /// Gdy coś się nie uda, przycisku nie ma, a menu działa ze skrótu.
    /// </summary>
    internal sealed class BarButton
    {
        private const BindingFlags Private = BindingFlags.NonPublic | BindingFlags.Instance;
        private static readonly FieldInfo OptionsVisible = typeof(UIGame).GetField("_isSubMenuOptionsVisible", Private);
        private static readonly FieldInfo PartyVisible = typeof(UIGame).GetField("_isSubMenuPartyVisible", Private);

        private readonly EventLog _log;
        private readonly Action _onClick;
        private UIGame _ui;
        private GameObject _go;
        private Button _button;
        private CanvasGroup _group;
        private TMP_Text _label;
        private bool _failed, _gameMenuWasOpen;

        public BarButton(EventLog log, Action onClick)
        {
            _log = log;
            _onClick = onClick;
        }

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

        public void Update(bool menuOpen)
        {
            GameSubmenuOpened = false;
            if (!SingletonBehaviour<UIGame>.IsInitialized) { _ui = null; return; }
            var ui = SingletonBehaviour<UIGame>.Instance;
            if (ui != _ui) { _ui = ui; _go = null; _failed = false; }
            bool gameMenu = IsTrue(OptionsVisible) || IsTrue(PartyVisible);
            GameSubmenuOpened = gameMenu && !_gameMenuWasOpen;
            _gameMenuWasOpen = gameMenu;
            if (_failed) return;
            try
            {
                Button party = ui.SubmenuPartyButton, options = ui.SubmenuOptionsButton;
                if (party == null || options == null) return;
                if (_go == null) Create(ui, party, options);
                if (_go == null) return;
                Follow(party, options, menuOpen);
            }
            catch (Exception e)
            {
                _failed = true;
                _log.Error("bar_button", e);
            }
        }

        private bool IsTrue(FieldInfo f)
        {
            return f != null && _ui != null && f.GetValue(_ui) is bool b && b;
        }

        private void Create(UIGame ui, Button party, Button options)
        {
            Canvas canvas = party.GetComponentInParent<Canvas>();
            if (canvas == null) return;
            Transform root = canvas.rootCanvas.transform;
            var holder = new GameObject("LektorPL.Holder");
            holder.SetActive(false);
            holder.transform.SetParent(root, false);
            GameObject go = UnityEngine.Object.Instantiate(party.gameObject, holder.transform, true);
            go.name = "LektorPL.Button";
            var dump = new StringBuilder();
            Strip(go, dump);
            HideIcon(go, options, dump);

            _button = go.GetComponent<Button>();
            if (_button == null) { UnityEngine.Object.Destroy(holder); _failed = true; return; }
            _button.onClick = new Button.ButtonClickedEvent();
            _button.onClick.AddListener(() => _onClick());
            _group = go.GetComponent<CanvasGroup>() ?? go.AddComponent<CanvasGroup>();
            _label = AddLabel(ui, go);

            go.transform.SetParent(root, true);
            go.transform.SetAsLastSibling();
            UnityEngine.Object.Destroy(holder);
            _go = go;
            _log.Write(_log.New("overlay_button").Str("parent", party.transform.parent != null ? party.transform.parent.name : null)
                .Str("canvas", canvas.rootCanvas.name).Str("tree", dump.ToString()));
        }

        /// <summary>Usuwa z kopii skrypty gry (Assembly-CSharp i inne spoza Unity), zostawia grafikę, przycisk i układ.</summary>
        private static void Strip(GameObject go, StringBuilder dump)
        {
            foreach (Component c in go.GetComponentsInChildren<Component>(true))
            {
                if (c == null || c is Transform) continue;
                string asm = c.GetType().Assembly.GetName().Name;
                bool unity = asm.StartsWith("UnityEngine", StringComparison.Ordinal) || asm.StartsWith("Unity.TextMeshPro", StringComparison.Ordinal);
                dump.Append(c.gameObject.name).Append(':').Append(c.GetType().Name).Append(unity ? "" : "(usunięty)").Append("; ");
                if (!unity) UnityEngine.Object.DestroyImmediate(c);
            }
        }

        /// <summary>Obrazy, których sprite'a nie ma w zębatce, to ikona drużyny: wyłączamy je razem z napisami.</summary>
        private static void HideIcon(GameObject go, Button options, StringBuilder dump)
        {
            var shared = new HashSet<string>();
            foreach (Image img in options.GetComponentsInChildren<Image>(true))
                if (img.sprite != null) shared.Add(img.sprite.name);
            foreach (Image img in go.GetComponentsInChildren<Image>(true))
            {
                string name = img.sprite != null ? img.sprite.name : null;
                bool keep = name == null || shared.Contains(name);
                dump.Append("img ").Append(img.gameObject.name).Append('=').Append(name ?? "-").Append(keep ? "" : "(ukryty)").Append("; ");
                if (!keep) img.enabled = false;
            }
            foreach (TMP_Text t in go.GetComponentsInChildren<TMP_Text>(true))
                t.enabled = false;
        }

        private static TMP_Text AddLabel(UIGame ui, GameObject go)
        {
            TMP_FontAsset font = null;
            foreach (TMP_Text t in ui.GetComponentsInChildren<TMP_Text>(true))
                if (t.font != null) { font = t.font; break; }
            var rt = (RectTransform)go.transform;
            var child = new GameObject("LektorPL.Label", typeof(RectTransform));
            child.transform.SetParent(go.transform, false);
            var crt = (RectTransform)child.transform;
            crt.anchorMin = Vector2.zero;
            crt.anchorMax = Vector2.one;
            crt.offsetMin = crt.offsetMax = Vector2.zero;
            var label = child.AddComponent<TextMeshProUGUI>();
            if (font != null) label.font = font;
            label.text = "PL";
            label.alignment = TextAlignmentOptions.Center;
            label.fontSize = Mathf.Max(18f, rt.rect.height * 0.36f);
            label.fontStyle = FontStyles.Bold;
            label.color = new Color(0.93f, 0.91f, 0.86f);
            label.raycastTarget = false;
            return label;
        }

        private void Follow(Button party, Button options, bool menuOpen)
        {
            bool visible = party.gameObject.activeInHierarchy;
            if (_go.activeSelf != visible) _go.SetActive(visible);
            if (!visible) return;
            Vector3 p = party.transform.position, o = options.transform.position;
            _go.transform.position = p + (p - o);
            _go.transform.rotation = party.transform.rotation;
            float alpha = 1f;
            bool blocks = true;
            foreach (CanvasGroup g in party.GetComponentsInParent<CanvasGroup>())
            {
                alpha *= g.alpha;
                blocks &= g.blocksRaycasts;
                if (g.ignoreParentGroups) break;
            }
            _group.alpha = alpha;
            _group.blocksRaycasts = blocks && alpha > 0.01f;
            _button.interactable = party.interactable;
            _label.color = menuOpen ? new Color(0.86f, 0.70f, 0.38f) : new Color(0.93f, 0.91f, 0.86f);
        }
    }
}
