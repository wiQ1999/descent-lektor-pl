using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;

namespace Doorstop
{
    /// <summary>
    /// Punkt wejścia Doorstop 4: target_assembly w doorstop_config.ini (Windows) albo DOORSTOP_TARGET_ASSEMBLY (Mac).
    /// Doorstop woła Start() przed startem Unity, więc tu nie wolno dotykać typów UnityEngine ani rdzenia.
    /// </summary>
    public static class Entrypoint
    {
        public static void Start()
        {
            LektorPL.Loader.Boot.Start();
        }
    }
}

namespace LektorPL.Loader
{
    /// <summary>
    /// Ładowanie w trzech krokach (D58): Start zapisuje ścieżki paczki, potem czekamy, aż gra wczyta
    /// UnityEngine.CoreModule, i subskrybujemy SceneManager.sceneLoaded. Przy pierwszej scenie, już na głównym
    /// wątku Unity, startuje rdzeń. Typy Unity i rdzenia są tylko w klasach SceneHook i CoreStart, kompilowanych
    /// dopiero wtedy, gdy są potrzebne. Błędy trafiają do logs/loader-*.log i nie wychodzą do gry.
    /// </summary>
    internal static class Boot
    {
        public const string Version = "0.3.0";

        internal static string BundleDir, PluginDir, LogDir;
        internal static Settings Settings;
        private static string s_logFile;
        private static int s_hooked;

        public static void Start()
        {
            try
            {
                string self = typeof(Boot).Assembly.Location;
                if (string.IsNullOrEmpty(self))
                    self = Environment.GetEnvironmentVariable("DOORSTOP_INVOKE_DLL_PATH");
                PluginDir = Path.GetDirectoryName(Path.GetFullPath(self));
                BundleDir = Path.GetDirectoryName(PluginDir);
                LogDir = Path.Combine(BundleDir, "logs");
                Directory.CreateDirectory(LogDir);
                s_logFile = Path.Combine(LogDir, "loader-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".log");
                Log("Lektor PL loader " + Version + ", paczka: " + BundleDir);
                Settings = Settings.Read(Path.Combine(BundleDir, "ustawienia.toml"));
                AppDomain.CurrentDomain.AssemblyResolve += Resolve;
                AppDomain.CurrentDomain.AssemblyLoad += OnAssemblyLoad;
                if (CoreModuleLoaded())
                {
                    Hook("już wczytany");
                    return;
                }
                // Zapas na wypadek, gdyby Mono nie zgłosił AssemblyLoad dla bibliotek wczytanych przez Unity.
                // Wątek kończy się po wykryciu modułu albo po 2 min, na długo przed wyjściem z gry (D40).
                new System.Threading.Thread(Poll) { IsBackground = true, Name = "LektorPL.Loader" }.Start();
            }
            catch (Exception e)
            {
                Log("start: " + e);
            }
        }

        private static bool IsCoreModule(Assembly a)
        {
            return a.GetName().Name == "UnityEngine.CoreModule";
        }

        private static bool CoreModuleLoaded()
        {
            foreach (Assembly a in AppDomain.CurrentDomain.GetAssemblies())
                if (IsCoreModule(a)) return true;
            return false;
        }

        private static void OnAssemblyLoad(object sender, AssemblyLoadEventArgs args)
        {
            try
            {
                if (IsCoreModule(args.LoadedAssembly)) Hook("AssemblyLoad");
            }
            catch (Exception e)
            {
                Log("assembly_load: " + e);
            }
        }

        private static void Poll()
        {
            try
            {
                for (int i = 0; i < 1200 && s_hooked == 0; i++)
                {
                    System.Threading.Thread.Sleep(100);
                    if (CoreModuleLoaded()) Hook("sprawdzanie co 100 ms");
                }
                if (s_hooked == 0) Log("UnityEngine.CoreModule nie wczytał się w 2 min, rdzeń nie wystartuje");
            }
            catch (Exception e)
            {
                Log("poll: " + e);
            }
        }

        private static void Hook(string via)
        {
            if (System.Threading.Interlocked.Exchange(ref s_hooked, 1) != 0) return;
            AppDomain.CurrentDomain.AssemblyLoad -= OnAssemblyLoad;
            Log("UnityEngine.CoreModule wczytany (" + via + "), czekam na pierwszą scenę");
            SceneHook.Subscribe();
        }

        /// <summary>LektorPL.Core leży w plugin/, a Mono szuka tylko w Managed gry.</summary>
        private static Assembly Resolve(object sender, ResolveEventArgs args)
        {
            string name = new AssemblyName(args.Name).Name;
            if (!name.StartsWith("LektorPL.", StringComparison.Ordinal)) return null;
            string path = Path.Combine(PluginDir, name + ".dll");
            return File.Exists(path) ? Assembly.LoadFrom(path) : null;
        }

        internal static void Log(string msg)
        {
            try
            {
                if (s_logFile == null) return;
                File.AppendAllText(s_logFile, DateTime.Now.ToString("HH:mm:ss.fff") + " " + msg + Environment.NewLine, Encoding.UTF8);
            }
            catch (Exception) { }
        }
    }

    internal static class SceneHook
    {
        public static void Subscribe()
        {
            UnityEngine.SceneManagement.SceneManager.sceneLoaded += OnSceneLoaded;
        }

        private static void OnSceneLoaded(UnityEngine.SceneManagement.Scene scene, UnityEngine.SceneManagement.LoadSceneMode mode)
        {
            UnityEngine.SceneManagement.SceneManager.sceneLoaded -= OnSceneLoaded;
            Boot.Log("pierwsza scena: " + scene.name);
            try
            {
                CoreStart.Run();
            }
            catch (Exception e)
            {
                Boot.Log("rdzeń nie wystartował: " + e);
            }
        }
    }

    internal static class CoreStart
    {
        public static void Run()
        {
            Settings s = Boot.Settings;
            var options = new LektorPL.Core.Options
            {
                LogDirectory = Boot.LogDir,
                CompanionPort = s.Int("port", 47810),
                DiagnosticStage = s.Int("plugin.stage", 4),
                Info = Boot.Log,
            };
            if (s.Bool("plugin.autostart", true))
            {
                string python = s.Str("plugin.python", null);
                if (string.IsNullOrEmpty(python))
                    python = Path.DirectorySeparatorChar == '\\'
                        ? Path.Combine(Boot.BundleDir, "python", "python.exe")
                        : Path.Combine(Path.Combine(Boot.BundleDir, "python"), Path.Combine("bin", "python3"));
                options.CompanionExe = Path.GetFullPath(python);
                options.CompanionWorkDir = Boot.BundleDir;
                options.CompanionArgs = "-I -m lektor.companion --quiet"
                    + " --config " + Quote(Path.Combine(Boot.BundleDir, "ustawienia.toml"))
                    + " --logs " + Quote(Boot.LogDir)
                    + " --parent-pid " + System.Diagnostics.Process.GetCurrentProcess().Id
                    + " --exit-after-disconnect " + s.Int("plugin.exit_after_disconnect", 15)
                    + " --exit-if-no-client " + s.Int("plugin.exit_if_no_client", 120);
            }
            string log = LektorPL.Core.Bootstrap.Start(options);
            Boot.Log("rdzeń " + LektorPL.Core.Bootstrap.Version + " uruchomiony, dziennik: " + log);
        }

        private static string Quote(string path)
        {
            return "\"" + path + "\"";
        }
    }

    /// <summary>
    /// Kilka kluczy z ustawienia.toml (resztę czyta companion): port oraz sekcja [plugin].
    /// Obsługuje tylko prosty podzbiór TOML: klucz = "tekst" | 'tekst' | liczba | true/false, komentarze #.
    /// </summary>
    internal sealed class Settings
    {
        private readonly Dictionary<string, string> _values = new Dictionary<string, string>();

        public static Settings Read(string file)
        {
            var s = new Settings();
            if (!File.Exists(file))
            {
                Boot.Log("brak pliku ustawień, wartości domyślne: " + file);
                return s;
            }
            string section = "";
            foreach (string raw in File.ReadAllLines(file, Encoding.UTF8))
            {
                string line = raw.Trim();
                if (line.Length == 0 || line[0] == '#') continue;
                if (line[0] == '[')
                {
                    int end = line.IndexOf(']');
                    section = end > 0 ? line.Substring(1, end - 1).Trim() + "." : "";
                    continue;
                }
                int eq = line.IndexOf('=');
                if (eq <= 0) continue;
                string key = section + line.Substring(0, eq).Trim();
                string value = Value(line.Substring(eq + 1).Trim());
                if (value != null) s._values[key] = value;
            }
            return s;
        }

        private static string Value(string v)
        {
            if (v.Length == 0) return null;
            if (v[0] == '\'')
            {
                int end = v.IndexOf('\'', 1);
                return end > 0 ? v.Substring(1, end - 1) : null;
            }
            if (v[0] == '"')
            {
                var sb = new StringBuilder();
                for (int i = 1; i < v.Length; i++)
                {
                    char c = v[i];
                    if (c == '"') return sb.ToString();
                    if (c == '\\' && i + 1 < v.Length) c = v[++i];
                    sb.Append(c);
                }
                return null;
            }
            int hash = v.IndexOf('#');
            return (hash >= 0 ? v.Substring(0, hash) : v).Trim();
        }

        public string Str(string key, string fallback)
        {
            return _values.TryGetValue(key, out string v) ? v : fallback;
        }

        public int Int(string key, int fallback)
        {
            return _values.TryGetValue(key, out string v) && int.TryParse(v, System.Globalization.NumberStyles.Integer, System.Globalization.CultureInfo.InvariantCulture, out int n) ? n : fallback;
        }

        public bool Bool(string key, bool fallback)
        {
            if (!_values.TryGetValue(key, out string v)) return fallback;
            if (v == "true") return true;
            if (v == "false") return false;
            return fallback;
        }
    }
}
