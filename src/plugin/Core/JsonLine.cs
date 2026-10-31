using System.Globalization;
using System.Text;

namespace LektorPL.Core
{
    /// <summary>Minimalny zapis jednego obiektu JSON w linii (bez zależności od bibliotek JSON gry).</summary>
    public sealed class JsonLine
    {
        private readonly StringBuilder _sb = new StringBuilder(256);
        private bool _needComma;

        public JsonLine() { _sb.Append('{'); }

        public JsonLine Str(string name, string value) { Key(name); Quote(value); return this; }
        public JsonLine Int(string name, long value) { Key(name); _sb.Append(value.ToString(CultureInfo.InvariantCulture)); return this; }
        public JsonLine Num(string name, double value) { Key(name); _sb.Append(value.ToString("0.###", CultureInfo.InvariantCulture)); return this; }
        public JsonLine Bool(string name, bool value) { Key(name); _sb.Append(value ? "true" : "false"); return this; }

        /// <summary>Wstawia gotowy fragment JSON (obiekt lub tablicę zbudowaną przez <see cref="JsonArray"/>).</summary>
        public JsonLine Raw(string name, string json) { Key(name); _sb.Append(json ?? "null"); return this; }

        public override string ToString() { return _sb.ToString() + "}"; }

        private void Key(string name)
        {
            if (_needComma) _sb.Append(',');
            _needComma = true;
            Quote(name);
            _sb.Append(':');
        }

        private void Quote(string s) { AppendQuoted(_sb, s); }

        internal static void AppendQuoted(StringBuilder sb, string s)
        {
            if (s == null) { sb.Append("null"); return; }
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20)
                            sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else
                            sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
        }
    }

    /// <summary>Tablica JSON z elementów: obiektów <see cref="JsonLine"/> albo napisów.</summary>
    public sealed class JsonArray
    {
        private readonly StringBuilder _sb = new StringBuilder("[");
        private bool _needComma;

        public JsonArray Add(JsonLine obj) { Sep(); _sb.Append(obj.ToString()); return this; }
        public JsonArray Add(string s) { Sep(); JsonLine.AppendQuoted(_sb, s); return this; }
        public override string ToString() { return _sb.ToString() + "]"; }

        private void Sep()
        {
            if (_needComma) _sb.Append(',');
            _needComma = true;
        }
    }
}
