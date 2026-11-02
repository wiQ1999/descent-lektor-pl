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

        /// <summary>Komunikaty diagnostyczne dla loadera (np. log BepInEx).</summary>
        public Action<string> Info;
    }

    /// <summary>Punkt wejścia rdzenia, niezależny od loadera.</summary>
    public static class Bootstrap
    {
        public const string Version = "0.2.0";
        private static GameObject s_host;

        /// <summary>Tworzy ukryty obiekt z <see cref="Runner"/>; zwraca ścieżkę dziennika. Kolejne wywołania nic nie robią.</summary>
        public static string Start(Options options)
        {
            if (s_host != null)
                return s_host.GetComponent<Runner>().LogPath;
            var log = new EventLog(options.LogDirectory);
            s_host = new GameObject("LektorPL") { hideFlags = HideFlags.HideAndDontSave };
            UnityEngine.Object.DontDestroyOnLoad(s_host);
            var runner = s_host.AddComponent<Runner>();
            Sender sender = null;
            if (options.CompanionPort > 0)
            {
                sender = new Sender(options.CompanionPort);
                log.Sink = sender.Enqueue;
            }
            runner.Init(new Tracker(log, options), log, sender);
            options.Info?.Invoke("Lektor PL " + Version + ": dziennik " + log.FilePath);
            return log.FilePath;
        }
    }

    public sealed class Runner : MonoBehaviour
    {
        private Tracker _tracker;
        private EventLog _log;
        private Sender _sender;

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
            if (_tracker == null) return;
            try { _tracker.Shutdown(); } catch (Exception e) { _log.Error("shutdown", e); }
            _tracker = null;
            _sender?.Pump(Time.unscaledTime);   // wyślij zdarzenie stop, potem zamknij gniazdo
            _sender?.Dispose();
            _sender = null;
            _log.Sink = null;
            _log.Dispose();
        }
    }
}
