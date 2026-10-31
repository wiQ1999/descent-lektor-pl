using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;

namespace LektorPL.Core
{
    /// <summary>Dziennik zdarzeń JSONL. Każda linia ma ev, t (s od startu gry), frame i utc.</summary>
    public sealed class EventLog : IDisposable
    {
        private const int MaxErrorsPerPlace = 20;
        private readonly StreamWriter _writer;
        private readonly Dictionary<string, int> _errors = new Dictionary<string, int>();

        public string FilePath { get; }

        public EventLog(string directory)
        {
            Directory.CreateDirectory(directory);
            FilePath = Path.Combine(directory, "hook-" + DateTime.Now.ToString("yyyyMMdd'-'HHmmss", CultureInfo.InvariantCulture) + ".jsonl");
            var stream = new FileStream(FilePath, FileMode.Create, FileAccess.Write, FileShare.Read);
            _writer = new StreamWriter(stream, new UTF8Encoding(false)) { AutoFlush = true };
        }

        public JsonLine New(string ev)
        {
            return new JsonLine()
                .Str("ev", ev)
                .Num("t", Time.realtimeSinceStartupAsDouble)
                .Int("frame", Time.frameCount)
                .Str("utc", DateTime.UtcNow.ToString("yyyy'-'MM'-'dd'T'HH':'mm':'ss'.'fff'Z'", CultureInfo.InvariantCulture));
        }

        public void Write(JsonLine line)
        {
            try { _writer.WriteLine(line.ToString()); }
            catch (Exception) { /* dysk pełny lub plik zamknięty: lektor nie może przerywać gry */ }
        }

        /// <summary>Zapisuje wyjątek, najwyżej <see cref="MaxErrorsPerPlace"/> razy dla jednego miejsca.</summary>
        public void Error(string where, Exception e)
        {
            _errors.TryGetValue(where, out int n);
            _errors[where] = ++n;
            if (n > MaxErrorsPerPlace) return;
            Write(New("error").Str("where", where).Str("type", e.GetType().FullName).Str("msg", e.Message)
                .Str("stack", e.StackTrace).Bool("last_reported", n == MaxErrorsPerPlace));
        }

        public void Dispose()
        {
            try { _writer.Dispose(); } catch (Exception) { }
        }
    }
}
