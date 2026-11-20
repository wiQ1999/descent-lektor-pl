using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Reflection;
using FFG.Core;
using FFG.D3;
using FFG.D3.UI;
using FFG.D3.WorldMap;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace LektorPL.Core
{
    /// <summary>
    /// Śledzi okna wiadomości gry, cel misji i aktywacje wrogów; zapisuje je do dziennika, który trafia też do companiona.
    ///
    /// Zwykłe okna: delegaty MessageController.MessageDisplayBegin/End. Begin przychodzi, zanim gra
    /// rozwiąże tekst (losuje warianty ListOfKeys), więc tekst renderujemy dopiero w LateUpdate,
    /// bez losowania (performRNG: false). Dodatkowo odpytujemy _curProcessingMessage, żeby wykryć
    /// okna, które ominęły delegaty.
    /// Okna fabularne: StoryMessageController nie ma zdarzeń, więc odpytujemy _curProcessingMessage,
    /// a moment pokazania tekstu (po załadowaniu bundli) rozpoznajemy po zmianie UIStoryMessageDialog.
    /// Cel misji (D31): odpytujemy UIGame._lastObjectiveKey i _LastObjectiveArguments; zmiana klucza albo tekstu
    /// (także samego licznika) daje zdarzenie objective. Aktywacja wroga (D30): GameController._curEnemyActivation,
    /// ustawiane w UIGame.ShowEnemyActivation i zerowane po zamknięciu okna aktywacji.
    /// </summary>
    internal sealed class Tracker
    {
        private const BindingFlags Private = BindingFlags.NonPublic | BindingFlags.Instance;
        private static readonly FieldInfo McCurrent = typeof(MessageController).GetField("_curProcessingMessage", Private);
        private static readonly FieldInfo McBack = typeof(MessageController).GetField("_pendingBack", Private);
        private static readonly FieldInfo McData = typeof(MessageController).GetField("_pendingAdditionalData", Private);
        private static readonly FieldInfo SmCurrent = typeof(StoryMessageController).GetField("_curProcessingMessage", Private);
        private static readonly FieldInfo SmBack = typeof(StoryMessageController).GetField("_pendingBack", Private);
        private static readonly FieldInfo SmData = typeof(StoryMessageController).GetField("_pendingAdditionalData", Private);
        private static readonly FieldInfo UgObjectiveKey = typeof(UIGame).GetField("_lastObjectiveKey", Private);
        private static readonly FieldInfo UgObjectiveArgs = typeof(UIGame).GetField("_LastObjectiveArguments", Private);
        private static readonly FieldInfo GcActivation = typeof(GameController).GetField("_curEnemyActivation", Private);
        private static readonly FieldInfo AdWeapon = typeof(UIHeroAttackDialog).GetField("_currentWeapon", Private);
        private static readonly FieldInfo AdPlayer = typeof(UIHeroAttackDialog).GetField("_player", Private);
        private static readonly FieldInfo AdEnemy = typeof(UIHeroAttackDialog).GetField("_enemy", Private);
        private static readonly FieldInfo FcCompleted = typeof(FeatsController).GetField("_completedFeatIds", Private);
        private static readonly FieldInfo FcPending = typeof(FeatsController).GetField("_pendingCompletedFeats", Private);
        private static readonly FieldInfo I2LanguageField =
            typeof(I2.Loc.LocalizationManager).GetField("mCurrentLanguage", BindingFlags.NonPublic | BindingFlags.Static);

        private readonly EventLog _log;
        private readonly Options _options;
        private readonly Stopwatch _work = new Stopwatch();
        private int _nextId;

        // Zwykłe okna.
        private MessageController _hooked;
        private MessageController.MessageDisplayBeginDelegate _onBegin;
        private MessageController.MessageDisplayEndDelegate _onEnd;
        private IMessageRequest _pending;          // po Begin, przed wyrenderowaniem
        private double _pendingAt;
        private IMessageRequest _open;             // wyrenderowane, jeszcze nie zamknięte
        private int _openId;
        private float _nextHookCheck;

        // Okna fabularne.
        private IMessageRequest _story;
        private int _storyId;
        private double _storyAt;
        private bool _storyAwaitingText;
        private string _storyBaselineText;
        private StoryMessageSettings _storyBaselineSettings;

        // Cel misji i aktywacja wroga.
        private string _objectiveKey, _objectiveText;
        private float _nextObjectiveCheck;
        private EnemyActivationRequest _activation;
        private int _activationId;

        // Kafelki zdolności w oknie ataku (E16, D101).
        private string _abilitySig;
        private int _abilityId;
        private string _defenseKey;                 // obrona wroga w otwartym oknie ataku (D102)
        private int _defenseId;
        private float _nextAbilityCheck;
        private string _featSig;                    // okno „Wyzwanie ukończone” (UIFeatsDialog.DialogSelectNewFeat, l14)
        private int _featId;
        private object _featList;                   // _completedFeatIds: nowa lista = wczytany zapis, nowa baza (l16)
        private readonly HashSet<string> _featsDone = new HashSet<string>();

        // Podsumowanie misji (E20, D113). Gra zeruje QuestId zaraz po pokazaniu okna (RecordQuestCompletion),
        // więc pamiętamy ostatni niepusty.
        private bool _summaryVisible;
        private string _lastQuestId;

        /// <summary>Statystyki z ostatniego pokazania okna podsumowania misji (null, gdy okno jest zamknięte).</summary>
        public QuestStats Summary { get; private set; }

        // Wybrany cel na mapie (panel DestinationDetails).
        private DestinationNode _detailsNode;
        private float _nextDetailsCheck;

        // Wydajność.
        private float _perfWindowStart;
        private int _perfFrames;
        private float _perfMaxDelta;
        private double _perfWorkMs, _perfWorkMaxMs;

        // Nasłuch TMP_Text (zapas do pomiaru pokrycia).
        private float _nextSniff;
        private readonly HashSet<string> _sniffed = new HashSet<string>();

        public Tracker(EventLog log, Options options)
        {
            _log = log;
            _options = options;
            _onBegin = OnBegin;
            _onEnd = OnEnd;
            SceneManager.activeSceneChanged += OnSceneChanged;
            _log.Write(_log.New("start").Str("plugin", Bootstrap.Version).Str("game", Application.version)
                .Str("unity", Application.unityVersion).Str("platform", Application.platform.ToString())
                .Bool("fields_ok", McCurrent != null && McBack != null && McData != null && SmCurrent != null && SmBack != null && SmData != null
                    && I2LanguageField != null)
                .Bool("sources_ok", UgObjectiveKey != null && UgObjectiveArgs != null && GcActivation != null && AdEnemy != null)
                .Bool("sniffer", options.SniffText).Int("stage", options.DiagnosticStage));
        }

        public void Shutdown()
        {
            SceneManager.activeSceneChanged -= OnSceneChanged;
            Unhook();
            _log.Write(_log.New("stop"));
        }

        public void LateUpdate()
        {
            _work.Reset();
            _work.Start();
            try { EnsureHooked(); } catch (Exception e) { _log.Error("hook", e); }
            try { FlushPending(); PollMessages(); } catch (Exception e) { _log.Error("messages", e); }
            try { PollStory(); } catch (Exception e) { _log.Error("story", e); }
            try { PollObjective(); } catch (Exception e) { _log.Error("objective", e); }
            try { PollActivation(); } catch (Exception e) { _log.Error("activation", e); }
            try { PollDetails(); } catch (Exception e) { _log.Error("details", e); }
            try { PollAbility(); } catch (Exception e) { _log.Error("ability", e); }
            try { PollQuestSummary(); } catch (Exception e) { _summaryVisible = true; _log.Error("quest_summary", e); }
            try { if (_options.SniffText) Sniff(); } catch (Exception e) { _log.Error("sniff", e); }
            _work.Stop();
            Perf(_work.Elapsed.TotalMilliseconds);
        }

        // ---------- zwykłe okna ----------

        private void EnsureHooked()
        {
            if (!SingletonBehaviour<PersistentGameObject>.IsInitialized)
                return;
            var mc = SingletonBehaviour<PersistentGameObject>.Instance.Messages;
            if (mc != _hooked)
            {
                Unhook();
                if (mc == null) return;
                mc.MessageDisplayBegin += _onBegin;
                mc.MessageDisplayEnd += _onEnd;
                _hooked = mc;
                _log.Write(_log.New("hooked").Str("language", SafeLanguage()));
                return;
            }
            // Pole delegata jest publiczne, więc ktoś mógłby je nadpisać; sprawdzamy co kilka sekund.
            if (Time.unscaledTime < _nextHookCheck || mc == null) return;
            _nextHookCheck = Time.unscaledTime + 5f;
            if (!Contains(mc.MessageDisplayBegin, _onBegin)) { mc.MessageDisplayBegin += _onBegin; _log.Write(_log.New("rehooked").Str("what", "begin")); }
            if (!Contains(mc.MessageDisplayEnd, _onEnd)) { mc.MessageDisplayEnd += _onEnd; _log.Write(_log.New("rehooked").Str("what", "end")); }
        }

        private static bool Contains(Delegate list, Delegate d)
        {
            if (list == null) return false;
            foreach (var x in list.GetInvocationList())
                if (x.Equals(d)) return true;
            return false;
        }

        private void Unhook()
        {
            if (_hooked == null) return;
            try
            {
                _hooked.MessageDisplayBegin -= _onBegin;
                _hooked.MessageDisplayEnd -= _onEnd;
            }
            catch (Exception e) { _log.Error("unhook", e); }
            _hooked = null;
        }

        private void OnBegin(IMessageRequest msg)
        {
            try
            {
                FlushPending();
                if (_open != null && _open != msg)
                    WriteClose("message", _open, _openId, "replaced", null);
                _pending = msg;
                _pendingAt = Time.realtimeSinceStartupAsDouble;
            }
            catch (Exception e) { _log.Error("begin", e); }
        }

        private void OnEnd(IMessageRequest msg)
        {
            try
            {
                if (_pending == msg) FlushPending();
                int id = msg == _open ? _openId : -1;
                WriteClose("message", msg, id, "delegate", _hooked);
                if (msg == _open) _open = null;
            }
            catch (Exception e) { _log.Error("end", e); }
        }

        private void FlushPending()
        {
            if (_pending == null) return;
            var msg = _pending;
            _pending = null;
            _open = msg;
            _openId = ++_nextId;
            var line = _log.New("open").Str("kind", "message").Int("id", _openId).Str("via", "delegate")
                .Num("begin_t", _pendingAt);
            Describe(line, msg);
            _log.Write(line);
        }

        /// <summary>Kontrola krzyżowa: okno widoczne w kontrolerze, a nieogłoszone przez delegaty (i odwrotnie).</summary>
        private void PollMessages()
        {
            if (_hooked == null || McCurrent == null) return;
            var cur = McCurrent.GetValue(_hooked) as IMessageRequest;
            if (cur != null && cur != _open && cur != _pending)
            {
                if (_open != null) WriteClose("message", _open, _openId, "poll", _hooked);
                _open = cur;
                _openId = ++_nextId;
                var line = _log.New("open").Str("kind", "message").Int("id", _openId).Str("via", "poll");
                Describe(line, cur);
                _log.Write(line);
            }
            else if (cur == null && _open != null)
            {
                WriteClose("message", _open, _openId, "poll", _hooked);
                _open = null;
            }
        }

        // ---------- okna fabularne ----------

        private void PollStory()
        {
            if (SmCurrent == null || !SingletonBehaviour<PersistentGameObject>.IsInitialized) return;
            var sm = SingletonBehaviour<PersistentGameObject>.Instance.StoryMessages;
            if (sm == null) return;
            var cur = SmCurrent.GetValue(sm) as IMessageRequest;
            if (cur != _story)
            {
                if (_story != null)
                {
                    WriteClose("story", _story, _storyId, "poll", sm);
                    CaptureStoryBaseline();
                }
                _story = cur;
                if (cur != null)
                {
                    _storyId = ++_nextId;
                    _storyAt = Time.realtimeSinceStartupAsDouble;
                    _storyAwaitingText = true;
                    var line = _log.New("open").Str("kind", "story").Int("id", _storyId).Str("via", "poll");
                    Describe(line, cur);
                    _log.Write(line);
                }
            }
            if (_story != null && _storyAwaitingText)
                TryStoryShown();
        }

        private void CaptureStoryBaseline()
        {
            var dlg = StoryDialog();
            _storyBaselineText = dlg != null && dlg.TextMessage != null ? dlg.TextMessage.text : null;
            _storyBaselineSettings = dlg != null ? dlg.CurrentSettings : null;
        }

        private static UIStoryMessageDialog StoryDialog()
        {
            return SingletonBehaviour<UIGame>.IsInitialized ? SingletonBehaviour<UIGame>.Instance.StoryMessageDialog : null;
        }

        /// <summary>Tekst pojawia się po załadowaniu bundli (korutyna gry); czekamy na zmianę okna.</summary>
        private void TryStoryShown()
        {
            var dlg = StoryDialog();
            if (dlg == null || !dlg.IsVisible) return;
            string text = dlg.TextMessage != null ? dlg.TextMessage.text : null;
            var settings = dlg.CurrentSettings;
            double waited = Time.realtimeSinceStartupAsDouble - _storyAt;
            string reason = text != _storyBaselineText ? "text"
                : settings != _storyBaselineSettings ? "settings"
                : waited > _options.StoryShownTimeout ? "timeout" : null;
            if (reason == null) return;
            _storyAwaitingText = false;
            var line = _log.New("shown").Str("kind", "story").Int("id", _storyId).Str("reason", reason)
                .Num("wait", waited).Str("text", Render(_story)).Str("ui_text", text);
            if (settings != null)
            {
                line.Str("background", settings.BackgroundType.ToString());
                var speakers = new JsonArray();
                AddSpeaker(speakers, 1, settings.Character_1);
                AddSpeaker(speakers, 2, settings.Character_2);
                AddSpeaker(speakers, 3, settings.Character_3);
                AddSpeaker(speakers, 4, settings.Character_4);
                line.Raw("characters", speakers.ToString());
            }
            _log.Write(line);
        }

        private void AddSpeaker(JsonArray list, int slot, StoryMessageCharacterSettings c)
        {
            if (c == null) return;
            try
            {
                var model = c.Character;
                if (model == null) return;
                var item = new JsonLine().Int("slot", slot).Str("model", model.KeyName).Bool("speaking", c.IsSpeaking)
                    .Bool("player_context", c.PlayerContext).Bool("variable", model.IsVariableCharacter());
                string resolved = null;
                try { resolved = c.GetNameKey(); }
                catch (Exception e) { _log.Error("speaker_name", e); }
                list.Add(item.Str("name_key", resolved));
            }
            catch (Exception e) { _log.Error("speaker", e); }
        }

        // ---------- cel misji i aktywacja wroga ----------

        private void PollObjective()
        {
            if (UgObjectiveKey == null || Time.unscaledTime < _nextObjectiveCheck || !SingletonBehaviour<UIGame>.IsInitialized) return;
            _nextObjectiveCheck = Time.unscaledTime + _options.ObjectiveInterval;
            var ui = SingletonBehaviour<UIGame>.Instance;
            string key = UgObjectiveKey.GetValue(ui) as string;
            bool visible = ui.LabelCurrentObjective != null && ui.LabelCurrentObjective.gameObject.activeSelf;
            if (key == null || !visible)
            {
                _objectiveKey = _objectiveText = null;
                return;
            }
            var args = UgObjectiveArgs?.GetValue(ui) as List<MessageArgument>;
            string text;
            try { text = MessageRequestUtils.ResolveTerm(key, args, colorArgs: false, performRNG: false); }
            catch (Exception e) { _log.Error("objective_render", e); return; }
            if (key == _objectiveKey && text == _objectiveText) return;
            _log.Write(_log.New("objective").Str("key", key).Str("prev_key", _objectiveKey).Raw("args", Arguments(args)).Str("text", text));
            _objectiveKey = key;
            _objectiveText = text;
        }

        // Mapa ustawia CurrentNode przy otwarciu panelu celu, ale po zamknięciu panelu go nie czyści:
        // o tym, że cel jest wybrany, decyduje widoczność panelu (D70).
        private void PollDetails()
        {
            if (Time.unscaledTime < _nextDetailsCheck) return;
            _nextDetailsCheck = Time.unscaledTime + _options.ObjectiveInterval;
            var node = SingletonBehaviour<WorldMapSceneController>.IsInitialized
                ? SingletonBehaviour<WorldMapSceneController>.Instance.CurrentNode : null;
            var panel = SingletonBehaviour<UIGame>.IsInitialized ? SingletonBehaviour<UIGame>.Instance.DestinationDetails : null;
            if (node != null && (panel == null || !panel.IsVisible)) node = null;
            if (node == _detailsNode) return;
            if (_detailsNode != null)
                _log.Write(_log.New("close").Str("kind", "details").Str("via", "poll"));
            _detailsNode = node;
            var model = node != null ? node.Model : null;
            if (model == null) return;
            _log.Write(_log.New("details").Str("key", model.DescKey).Str("name_key", model.NameKey)
                .Str("text", panel.TextDescription != null ? panel.TextDescription.text : null));
        }

        // Okno ataku po potwierdzeniu trafień pokazuje kafelki UIAbilityTrigger (nazwa w szablonie WEAPON_ABILITY_TRIGGER
        // i opis). Pula kafelków czyści się dopiero przy następnym ataku, więc o zamknięciu decyduje widoczność okna.
        // Klucze kafelka: zdolności części B i C bieżącej broni oraz talizmany aktywnych graczy, dopasowane po tekście opisu.
        private void PollAbility()
        {
            if (Time.unscaledTime < _nextAbilityCheck) return;
            _nextAbilityCheck = Time.unscaledTime + _options.ObjectiveInterval;
            var dialog = SingletonBehaviour<UIGame>.IsInitialized ? SingletonBehaviour<UIGame>.Instance.HeroAttackDialog : null;
            try { PollFeat(); } catch (Exception e) { _log.Error("feat", e); }
            try { PollFeatDone(); } catch (Exception e) { _log.Error("feat_done", e); }
            PollDefense(dialog);
            var tiles = new List<UIAbilityTrigger>();
            var sig = new System.Text.StringBuilder();
            if (dialog != null && dialog.IsVisible && dialog.PoolAbilityTrigger != null)
                foreach (GameObject go in dialog.PoolAbilityTrigger)
                {
                    if (go == null || !go.activeInHierarchy) continue;
                    var t = go.GetComponent<UIAbilityTrigger>();
                    if (t == null || t.TextAbilityName == null || string.IsNullOrEmpty(t.TextAbilityName.text)) continue;
                    tiles.Add(t);
                    sig.Append(t.TextAbilityName.text).Append('\u0001').Append(t.TextAbilityDesc != null ? t.TextAbilityDesc.text : null).Append('\u0002');
                }
            string s = tiles.Count > 0 ? sig.ToString() : null;
            if (s == _abilitySig) return;
            if (_abilitySig != null)
                _log.Write(_log.New("close").Str("kind", "ability").Int("id", _abilityId).Str("via", "poll"));
            _abilitySig = s;
            if (s == null) return;
            _abilityId = ++_nextId;
            var cands = AbilityCandidates(dialog, out string extraKey);
            var items = new JsonArray();
            foreach (var t in tiles)
            {
                string name = t.TextAbilityName.text, desc = t.TextAbilityDesc != null ? t.TextAbilityDesc.text : null;
                var item = new JsonLine().Str("name", name).Str("desc", desc);
                foreach (var c in cands)
                {
                    string d = Loc(c.Value);
                    if (string.IsNullOrEmpty(d) || desc == null) continue;
                    bool plain = desc == d, extra = extraKey != null && desc.StartsWith(d + " (", StringComparison.Ordinal);
                    if (!plain && !extra) continue;
                    string n = Loc(c.Key);
                    if (!string.IsNullOrEmpty(n) && name.IndexOf(n, StringComparison.Ordinal) < 0) continue;
                    item.Str("name_key", c.Key).Str("desc_key", c.Value);
                    if (extra) item.Str("extra_key", extraKey);
                    break;
                }
                items.Add(item);
            }
            _log.Write(_log.New("open").Str("kind", "ability").Int("id", _abilityId).Str("via", "poll").Raw("items", items.ToString()));
        }

        // Okno ataku pokazuje obronę wroga w polu TextDefensive (klucz SerializedEnemy.GetDefenseKey, ustawiony przez grę
        // przy otwarciu okna). Jedno zdarzenie na otwarcie okna; zamknięcie przy ukryciu okna albo zmianie wroga (D102).
        private void PollDefense(UIHeroAttackDialog dialog)
        {
            string key = null, text = null;
            if (dialog != null && dialog.IsVisible && AdEnemy != null && AdEnemy.GetValue(dialog) is SerializedEnemy enemy)
            {
                text = dialog.TextDefensive != null ? dialog.TextDefensive.text : null;
                if (!string.IsNullOrEmpty(text)) key = enemy.GetDefenseKey();
            }
            if (key == _defenseKey) return;
            if (_defenseKey != null)
                _log.Write(_log.New("close").Str("kind", "defense").Int("id", _defenseId).Str("via", "poll"));
            _defenseKey = key;
            if (key == null) return;
            _defenseId = ++_nextId;
            _log.Write(_log.New("open").Str("kind", "defense").Int("id", _defenseId).Str("via", "poll").Str("key", key).Str("text", text));
        }

        // Ukończone wyzwanie: gra pokazuje panel DialogSelectNewFeat z nazwą wyzwania i opisem nagrody
        // (FeatsController.GetRewardDescription albo UI_FEAT_REPLACED przy wymianie). Lektor czyta nagłówek i nagrodę.
        private void PollFeat()
        {
            var feats = SingletonBehaviour<UIGame>.IsInitialized ? SingletonBehaviour<UIGame>.Instance.FeatsDialog : null;
            var panel = feats != null ? feats.DialogSelectNewFeat : null;
            string sig = null, reward = null, name = null;
            if (panel != null && panel.gameObject.activeInHierarchy && panel.alpha > 0.05f)
            {
                reward = feats.RewardDescription != null ? feats.RewardDescription.text : null;
                name = feats.FeatName != null ? feats.FeatName.text : null;
                sig = (name ?? "") + "\u0001" + (reward ?? "");
            }
            if (sig == _featSig) return;
            if (_featSig != null)
                _log.Write(_log.New("close").Str("kind", "feat").Int("id", _featId).Str("via", "poll"));
            _featSig = sig;
            if (sig == null) return;
            _featId = ++_nextId;
            _log.Write(_log.New("open").Str("kind", "feat").Int("id", _featId).Str("via", "poll").Str("name", name)
                .Str("reward", reward).Bool("replaced", reward != null && reward == Loc("UI_FEAT_REPLACED")));
        }

        // Chwila ukończenia wyzwania (l16): gra dopisuje id do _pendingCompletedFeats (powiadomienie „nazwa (3/3)”),
        // a po opróżnieniu stosu przenosi je do _completedFeatIds. Zgłaszamy każde nowe id raz; wyzwania z wczytanego
        // zapisu (nowa lista _completedFeatIds) tworzą bazę bez zgłoszeń.
        private void PollFeatDone()
        {
            if (FcCompleted == null || FcPending == null || !SingletonBehaviour<PersistentGameObject>.IsInitialized) return;
            var fc = SingletonBehaviour<PersistentGameObject>.Instance.FeatController;
            var done = fc != null ? FcCompleted.GetValue(fc) as List<string> : null;
            var pending = fc != null ? FcPending.GetValue(fc) as List<string> : null;
            if (done == null) return;
            bool baseline = !ReferenceEquals(done, _featList) || done.Count + (pending != null ? pending.Count : 0) < _featsDone.Count;
            var now = new List<string>(done);
            if (pending != null) now.AddRange(pending);
            if (baseline)
            {
                _featList = done;
                _featsDone.Clear();
                foreach (var id in now) _featsDone.Add(id);
                return;
            }
            foreach (var id in now)
            {
                if (string.IsNullOrEmpty(id) || !_featsDone.Add(id)) continue;
                var feat = UserCollectionManager.GetFeat(id, ownedOnly: true);
                string hero = feat != null && feat.HeroSource != null ? feat.HeroSource.Id : null;
                _log.Write(_log.New("feat_done").Str("kind", "feat_done").Int("id", ++_nextId).Str("feat", id)
                    .Str("desc_key", feat != null ? feat.DescriptionKey : null)
                    .Str("hero_key", hero != null ? hero + "_NAME" : null)
                    .Str("name", feat != null ? feat.GetLocalizedFeatName() : null));
            }
        }

        // Okno podsumowania misji (UIQuestSummary): GameController.OnQuestFinished pokazuje je i wypełnia w jednej klatce,
        // po SetQuestTime, więc w LateUpdate dane misji są kompletne. Liczymy raz na pokazanie.
        private void PollQuestSummary()
        {
            var gd = SingletonBehaviour<GameData>.IsInitialized ? SingletonBehaviour<GameData>.Instance.Data : null;
            if (gd != null && !string.IsNullOrEmpty(gd.QuestId)) _lastQuestId = gd.QuestId;
            var dialog = SingletonBehaviour<UIGame>.IsInitialized ? SingletonBehaviour<UIGame>.Instance.QuestSummaryDialog : null;
            bool visible = dialog != null && dialog.IsVisible;
            if (visible == _summaryVisible) return;
            _summaryVisible = visible;
            if (!visible)
            {
                Summary = null;
                _log.Write(_log.New("close").Str("kind", "quest_summary").Str("via", "poll"));
                return;
            }
            Summary = QuestStats.Read(gd, _lastQuestId);
            var line = _log.New("quest_summary").Str("kind", "quest_summary").Int("id", ++_nextId);
            _log.Write(Summary != null ? Summary.Describe(line) : line.Bool("empty", true));
        }

        private static List<KeyValuePair<string, string>> AbilityCandidates(UIHeroAttackDialog dialog, out string extraKey)
        {
            var list = new List<KeyValuePair<string, string>>();
            extraKey = null;
            var weapon = AdWeapon != null ? AdWeapon.GetValue(dialog) as SerializedWeapon : null;
            if (weapon != null)
            {
                foreach (var part in new[] { weapon.PartB, weapon.PartC })
                    if (part != null && part.Ability != null)
                        list.Add(new KeyValuePair<string, string>(part.Ability.KeyName, part.Ability.KeyDesc));
                if (weapon.PartC != null && weapon.PartC.Ability != null) extraKey = weapon.PartC.Ability.KeyDesc;
            }
            var players = new List<SerializedPlayer>();
            if (AdPlayer != null && AdPlayer.GetValue(dialog) is SerializedPlayer me) players.Add(me);
            if (SingletonBehaviour<GameData>.IsInitialized && SingletonBehaviour<GameData>.Instance.Data != null
                && SingletonBehaviour<GameData>.Instance.Data.ActivePlayers != null)
                players.AddRange(SingletonBehaviour<GameData>.Instance.Data.ActivePlayers);
            foreach (var pl in players)
            {
                var trinket = pl != null ? pl.EquippedTrinket : null;
                if (trinket != null) list.Add(new KeyValuePair<string, string>(trinket.KeyName, trinket.AbilityKey));
            }
            return list;
        }

        private static string Loc(string key)
        {
            return string.IsNullOrEmpty(key) ? null : FFGLocalization.Get(key, returnKeyOnMissing: false);
        }

        private void PollActivation()
        {
            if (GcActivation == null || !SingletonBehaviour<GameController>.IsInitialized) return;
            var cur = GcActivation.GetValue(SingletonBehaviour<GameController>.Instance) as EnemyActivationRequest;
            if (cur == _activation) return;
            if (_activation != null)
                _log.Write(_log.New("close").Str("kind", "activation").Int("id", _activationId).Str("via", "poll")
                    .Str("key", _activation.Message?.Key));
            _activation = cur;
            if (cur == null) return;
            _activationId = ++_nextId;
            var line = _log.New("open").Str("kind", "activation").Int("id", _activationId).Str("via", "poll");
            try { line.Str("enemy", cur.Enemy?.ModelId); }
            catch (Exception) { line.Str("enemy", "<error>"); }
            if (cur.Message != null) Describe(line, cur.Message);
            _log.Write(line);
        }

        // ---------- opis wiadomości ----------

        private void Describe(JsonLine line, IMessageRequest msg)
        {
            line.Str("type", msg.GetType().Name).Str("key", msg.Key).Str("title", msg.TitleKey);
            try { line.Str("actor", msg.Actor != null ? msg.Actor.name : null); }
            catch (Exception) { line.Str("actor", "<error>"); }
            line.Str("source", msg.Source != null ? msg.Source.GetType().Name : null);
            var s = msg.Settings;
            if (s != null)
                line.Raw("settings", new JsonLine().Bool("tutorial", s.IsTutorial).Bool("back_disabled", s.BackDisabled)
                    .Bool("can_skip", s.CanSkip).ToString());
            line.Raw("args", Arguments(msg.Arguments));
            line.Str("text", Render(msg));
            if (msg is MultipleChoiceMessageRequest mc)
            {
                var choices = new JsonArray();
                foreach (var ch in mc.Choices)
                    choices.Add(new JsonLine().Str("key", ch?.Key).Bool("conditional", ch?.Condition != null).Bool("met", ch != null && ch.ConditionMet));
                line.Raw("choices", choices.ToString());
                if (!string.IsNullOrEmpty(mc.VirtueOneKey))
                    line.Str("virtue1", mc.VirtueOneKey).Str("virtue2", mc.VirtueTwoKey);
            }
        }

        private string Arguments(List<MessageArgument> args)
        {
            if (args == null) return "null";
            var arr = new JsonArray();
            for (int i = 0; i < args.Count; i++)
            {
                var a = args[i];
                var item = new JsonLine().Int("i", i);
                if (a == null) { arr.Add(item.Str("type", null)); continue; }
                item.Str("type", a.ArgType.ToString());
                try { item.Str("as_key", a.ResolveArgument(returnAsKey: true)); }
                catch (Exception e) { item.Str("as_key_error", e.GetType().Name); }
                try { item.Str("value", a.ResolveArgument(returnAsKey: false)); }
                catch (Exception e) { item.Str("value_error", e.GetType().Name); }
                arr.Add(item);
            }
            return arr.ToString();
        }

        /// <summary>Tekst okna bez ponownego losowania wariantów (gra losuje przy własnym renderowaniu).</summary>
        private string Render(IMessageRequest msg)
        {
            try { return MessageRequestUtils.ResolveTerm(msg.Key, msg.Arguments, colorArgs: false, performRNG: false); }
            catch (Exception e) { _log.Error("render", e); return null; }
        }

        private void WriteClose(string kind, IMessageRequest msg, int id, string via, object controller)
        {
            var line = _log.New("close").Str("kind", kind).Int("id", id).Str("via", via).Str("key", msg.Key);
            FieldInfo back = kind == "story" ? SmBack : McBack, data = kind == "story" ? SmData : McData;
            if (controller != null && back != null && data != null)
            {
                bool isBack = (bool)back.GetValue(controller);
                int value = (int)data.GetValue(controller);
                line.Bool("back", isBack).Int("data", value);
                if (!isBack && msg is MultipleChoiceMessageRequest mc && value >= 0 && value < mc.Choices.Count)
                    line.Str("choice_key", mc.Choices[value]?.Key);
            }
            _log.Write(line);
        }

        // ---------- pozostałe ----------

        private void OnSceneChanged(UnityEngine.SceneManagement.Scene from, UnityEngine.SceneManagement.Scene to)
        {
            try { _log.Write(_log.New("scene").Str("name", to.name).Str("language", SafeLanguage())); }
            catch (Exception e) { _log.Error("scene", e); }
        }

        private void Sniff()
        {
            if (Time.unscaledTime < _nextSniff) return;
            _nextSniff = Time.unscaledTime + _options.SniffInterval;
            var dlg = StoryDialog();
            foreach (var tmp in UnityEngine.Object.FindObjectsOfType<TMP_Text>())
            {
                if (!tmp.isActiveAndEnabled || (dlg != null && tmp == dlg.TextMessage)) continue;
                string text = tmp.text;
                if (string.IsNullOrEmpty(text) || text.Length < _options.SniffMinLength) continue;
                string path = PathOf(tmp.transform);
                if (_sniffed.Count > 50000) _sniffed.Clear();
                if (!_sniffed.Add(path + "\u0001" + text)) continue;
                _log.Write(_log.New("tmp").Str("path", path).Str("text", text));
            }
        }

        private static string PathOf(Transform t)
        {
            string path = t.name;
            for (int i = 0; i < 3 && t.parent != null; i++)
            {
                t = t.parent;
                path = t.name + "/" + path;
            }
            return path;
        }

        /// <summary>
        /// Czytamy pole, nie właściwość: getter I2 LocalizationManager.CurrentLanguage inicjalizuje I2
        /// (i zatrzaskuje s_isInitialized). Wywołany przed załadowaniem bundli zostawia język null,
        /// a gra przekazuje go potem do AkSoundEngine.SetCurrentLanguage, co kończy się crashem Wwise.
        /// </summary>
        private static string SafeLanguage()
        {
            try { return I2LanguageField?.GetValue(null) as string; }
            catch (Exception) { return null; }
        }

        private void Perf(double workMs)
        {
            float now = Time.unscaledTime;
            if (_perfFrames == 0) _perfWindowStart = now;
            _perfFrames++;
            _perfMaxDelta = Math.Max(_perfMaxDelta, Time.unscaledDeltaTime);
            _perfWorkMs += workMs;
            _perfWorkMaxMs = Math.Max(_perfWorkMaxMs, workMs);
            if (now - _perfWindowStart < 60f) return;
            _log.Write(_log.New("perf").Int("frames", _perfFrames).Num("seconds", now - _perfWindowStart)
                .Num("max_frame_ms", _perfMaxDelta * 1000f).Num("work_ms_total", _perfWorkMs).Num("work_ms_max", _perfWorkMaxMs));
            _perfFrames = 0;
            _perfMaxDelta = 0f;
            _perfWorkMs = _perfWorkMaxMs = 0;
        }
    }
}
