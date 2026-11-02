using System;
using System.IO;
using UnityEngine;

namespace LektorPL.Core
{
    public sealed class Options
    {
        /// <summary>Katalog dzienników JSONL; domyślnie %LOCALAPPDATA%\LektorPL\logs (na Macu ~/.local/share/LektorPL/logs).</summary>
        public string LogDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "LektorPL", "logs");

        /// <summary>Zapisuje nowe teksty widocznych TMP_Text (diagnostyka pokrycia z E1; kosztuje ok. 6 ms na skan).</summary>
        public bool SniffText = false;
        public float SniffInterval = 1f;
        public int SniffMinLength = 12;

        /// <summary>Po ilu sekundach uznać okno fabularne za pokazane, gdy tekst się nie zmienił (np. dwa identyczne okna).</summary>
        public double StoryShownTimeout = 3.0;

        /// <summary>Port companiona na localhost; 0 wyłącza wysyłkę (zostaje sam dziennik).</summary>
        public int CompanionPort = 47810;

        /// <summary>Co ile sekund sprawdzać cel misji w HUD (D31).</summary>
        public float ObjectiveInterval = 0.5f;

        /// <summary>
        /// Etap diagnostyczny crasha przy wyjściu (D40): 0 sam plugin bez działania, 1 ukryty obiekt z pustym Runnerem,
        /// 2 dodatkowo dziennik, 3 dodatkowo Tracker (hooki i polling), 4 całość z wysyłką do companiona.
        /// </summary>
        public int DiagnosticStage = 4;

        /// <summary>Komunikaty diagnostyczne dla loadera (np. log BepInEx).</summary>
        public Action<string> Info;
    }

    /// <summary>Punkt wejścia rdzenia, niezależny od loadera.</summary>
    public static class Bootstrap
    {
        public const string Version = "0.2.1";
        private static GameObject s_host;

        /// <summary>Tworzy ukryty obiekt z <see cref="Runner"/>; zwraca ścieżkę dziennika. Kolejne wywołania nic nie robią.</summary>
        public static string Start(Options options)
        {
            if (s_host != null)
                return s_host.GetComponent<Runner>().LogPath;
            int stage = options.DiagnosticStage;
            string prefix = "Lektor PL " + Version + " (etap diagnostyczny " + stage + ")";
            if (stage <= 0)
            {
                options.Info?.Invoke(prefix + ": nic nie uruchamiam");
                return null;
            }
            s_host = new GameObject("LektorPL") { hideFlags = HideFlags.HideAndDontSave };
            UnityEngine.Object.DontDestroyOnLoad(s_host);
            var runner = s_host.AddComponent<Runner>();
            if (stage == 1)
            {
                options.Info?.Invoke(prefix + ": pusty Runner, bez dziennika");
                return null;
            }
            var log = new EventLog(options.LogDirectory);
            Tracker tracker = stage >= 3 ? new Tracker(log, options) : null;
            if (tracker == null)
                log.Write(log.New("start").Str("plugin", Version).Int("stage", stage));
            Sender sender = null;
            if (stage >= 4 && options.CompanionPort > 0)
            {
                sender = new Sender(options.CompanionPort);
                log.Sink = sender.Enqueue;
            }
            runner.Init(tracker, log, sender);
            options.Info?.Invoke(prefix + ": dziennik " + log.FilePath);
            return log.FilePath;
        }
    }

    public sealed class Runner : MonoBehaviour
    {
        private Tracker _tracker;
        private EventLog _log;
        private Sender _sender;
        private bool _stopped;

        public string LogPath => _log?.FilePath;

        internal void Init(Tracker tracker, EventLog log, Sender sender)
        {
            _tracker = tracker;
            _log = log;
            _sender = sender;
        }

        private void LateUpdate()
        {
            _tracker?.LateUpdate();
            if (_sender == null || _tracker == null) return;
            try
            {
                string change = _sender.Pump(Time.unscaledTime);
                if (change != null) _log.Write(_log.New("companion").Str("state", change));
            }
            catch (Exception e) { _log.Error("sender", e); }
        }

        private void OnApplicationQuit()
        {
            Stop();
        }

        private void OnDestroy()
        {
            Stop();
        }

        private void Stop()
        {
            if (_stopped || _log == null) return;
            _stopped = true;
            if (_tracker != null)
            {
                try { _tracker.Shutdown(); } catch (Exception e) { _log.Error("shutdown", e); }
                _tracker = null;
            }
            else
            {
                _log.Write(_log.New("stop"));
            }
            _sender?.Pump(Time.unscaledTime);   // wyślij zdarzenie stop, potem zamknij gniazdo
            _sender?.Dispose();
            _sender = null;
            _log.Sink = null;
            _log.Dispose();
        }
    }
}
