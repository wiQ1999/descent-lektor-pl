using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace LektorPL.Core
{
    /// <summary>
    /// Minimalny odczyt JSON (stan od companiona): obiekt to Dictionary&lt;string, object&gt;, tablica List&lt;object&gt;,
    /// liczba double, poza tym string, bool i null. Błędny tekst daje null zamiast wyjątku.
    /// </summary>
    internal static class Json
    {
        public static object Parse(string text)
        {
            try
            {
                int i = 0;
                object v = Value(text, ref i);
                Skip(text, ref i);
                return i == text.Length ? v : null;
            }
            catch (Exception)
            {
                return null;
            }
        }

        // ---------- pomocnicze do odczytu pól ----------

        public static Dictionary<string, object> Obj(object o, string name)
        {
            return Get(o, name) as Dictionary<string, object>;
        }

        public static List<object> List(object o, string name)
        {
            return Get(o, name) as List<object>;
        }

        public static string Str(object o, string name, string fallback = null)
        {
            return Get(o, name) as string ?? fallback;
        }

        public static double Num(object o, string name, double fallback = 0)
        {
            return Get(o, name) is double d ? d : fallback;
        }

        public static bool Bool(object o, string name, bool fallback = false)
        {
            return Get(o, name) is bool b ? b : fallback;
        }

        public static object Get(object o, string name)
        {
            return o is Dictionary<string, object> d && d.TryGetValue(name, out object v) ? v : null;
        }

        // ---------- parser ----------

        private static void Skip(string s, ref int i)
        {
            while (i < s.Length && char.IsWhiteSpace(s[i])) i++;
        }

        private static object Value(string s, ref int i)
        {
            Skip(s, ref i);
            char c = s[i];
            if (c == '{') return Object(s, ref i);
            if (c == '[') return Array(s, ref i);
            if (c == '"') return String(s, ref i);
            if (s.Length - i >= 4 && string.CompareOrdinal(s, i, "true", 0, 4) == 0) { i += 4; return true; }
            if (s.Length - i >= 5 && string.CompareOrdinal(s, i, "false", 0, 5) == 0) { i += 5; return false; }
            if (s.Length - i >= 4 && string.CompareOrdinal(s, i, "null", 0, 4) == 0) { i += 4; return null; }
            return Number(s, ref i);
        }

        private static Dictionary<string, object> Object(string s, ref int i)
        {
            var d = new Dictionary<string, object>();
            i++;
            Skip(s, ref i);
            if (s[i] == '}') { i++; return d; }
            while (true)
            {
                Skip(s, ref i);
                string key = String(s, ref i);
                Skip(s, ref i);
                if (s[i++] != ':') throw new FormatException();
                d[key] = Value(s, ref i);
                Skip(s, ref i);
                char c = s[i++];
                if (c == '}') return d;
                if (c != ',') throw new FormatException();
            }
        }

        private static List<object> Array(string s, ref int i)
        {
            var list = new List<object>();
            i++;
            Skip(s, ref i);
            if (s[i] == ']') { i++; return list; }
            while (true)
            {
                list.Add(Value(s, ref i));
                Skip(s, ref i);
                char c = s[i++];
                if (c == ']') return list;
                if (c != ',') throw new FormatException();
            }
        }

        private static string String(string s, ref int i)
        {
            if (s[i] != '"') throw new FormatException();
            i++;
            var sb = new StringBuilder();
            while (true)
            {
                char c = s[i++];
                if (c == '"') return sb.ToString();
                if (c != '\\') { sb.Append(c); continue; }
                char e = s[i++];
                switch (e)
                {
                    case 'n': sb.Append('\n'); break;
                    case 't': sb.Append('\t'); break;
                    case 'r': sb.Append('\r'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'u':
                        sb.Append((char)int.Parse(s.Substring(i, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                        i += 4;
                        break;
                    default: sb.Append(e); break;
                }
            }
        }

        private static double Number(string s, ref int i)
        {
            int start = i;
            while (i < s.Length && "+-0123456789.eE".IndexOf(s[i]) >= 0) i++;
            if (i == start) throw new FormatException();
            return double.Parse(s.Substring(start, i - start), NumberStyles.Float, CultureInfo.InvariantCulture);
        }
    }
}
