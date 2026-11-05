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
                .Bool("sources_ok", UgObjectiveKey != null && UgObjectiveArgs != null && GcActivation != null)
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
