using System;
using System.IO;
using UnityEngine;

namespace LektorPL.Core
{
    public sealed class Options
    {
        /// <summary>Katalog dzienników JSONL; domyślnie %LOCALAPPDATA%\LektorPL\logs (na Macu ~/.local/share/LektorPL/logs).</summary>
        public string LogDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "LektorPL", "logs");

        /// <summary>Zapisuje nowe teksty widocznych TMP_Text (zapas do pomiaru pokrycia okien spoza systemu wiadomości).</summary>
        public bool SniffText = true;
        public float SniffInterval = 1f;
        public int SniffMinLength = 12;

        /// <summary>Po ilu sekundach uznać okno fabularne za pokazane, gdy tekst się nie zmienił (np. dwa identyczne okna).</summary>
        public double StoryShownTimeout = 3.0;

        /// <summary>Komunikaty diagnostyczne dla loadera (np. log BepInEx).</summary>
        public Action<string> Info;
    }

    /// <summary>Punkt wejścia rdzenia, niezależny od loadera.</summary>
    public static class Bootstrap
    {
        public const string Version = "0.1.1";
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
            runner.Init(new Tracker(log, options), log);
            options.Info?.Invoke("Lektor PL " + Version + ": dziennik " + log.FilePath);
            return log.FilePath;
        }
    }

    public sealed class Runner : MonoBehaviour
    {
        private Tracker _tracker;
        private EventLog _log;

        public string LogPath => _log?.FilePath;

        internal void Init(Tracker tracker, EventLog log)
        {
            _tracker = tracker;
            _log = log;
        }

        private void LateUpdate()
        {
            _tracker?.LateUpdate();
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
            _log.Dispose();
        }
    }
}
