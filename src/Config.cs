using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;

namespace KeystrokesOverlay
{
    /// <summary>
    /// Portable settings. Stored as config.json next to the exe; falls back to
    /// %APPDATA%\KeystrokesOverlay when the exe folder is read-only.
    /// </summary>
    internal class Config
    {
        public string Accent = "#e455e0";
        public string RecentAccent = ""; // last custom colour, kept as a 5th swatch
        public int Scale = 100;        // 60..200 %
        public int Opacity = 88;       // 30..100 %
        public bool ShowCps = true;
        public bool ShowCounters = false;
        public int CpsWindowMs = 1000;  // 500..3000
        public int TileBackdrop = 55;   // 0..100 — dark plate behind idle tiles, keeps them readable on light scenes
        public int PosX = int.MinValue;
        public int PosY = int.MinValue;
        public bool AutoStart = false;
        public bool Visible = true;
        public bool HintShown = false; // first-run "F8 — settings" caption

        private static string _path;

        public static string FilePath
        {
            get
            {
                if (_path != null) return _path;
                string exeDir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
                string candidate = Path.Combine(exeDir, "config.json");
                if (CanWrite(exeDir))
                {
                    _path = candidate;
                }
                else
                {
                    string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                        "KeystrokesOverlay");
                    try { Directory.CreateDirectory(dir); }
                    catch { }
                    _path = Path.Combine(dir, "config.json");
                }
                return _path;
            }
        }

        private static bool CanWrite(string dir)
        {
            try
            {
                string probe = Path.Combine(dir, ".write-probe.tmp");
                File.WriteAllText(probe, "x");
                File.Delete(probe);
                return true;
            }
            catch { return false; }
        }

        public static Config Load()
        {
            Config c = new Config();
            try
            {
                if (!File.Exists(FilePath)) return c;
                Dictionary<string, string> map = MiniJson.ParseFlat(File.ReadAllText(FilePath, Encoding.UTF8));
                c.Accent = GetStr(map, "accent", c.Accent);
                c.RecentAccent = GetStr(map, "recentAccent", c.RecentAccent);
                c.Scale = Clamp(GetInt(map, "scale", c.Scale), 60, 200);
                c.Opacity = Clamp(GetInt(map, "opacity", c.Opacity), 30, 100);
                c.ShowCps = GetBool(map, "showCps", c.ShowCps);
                c.ShowCounters = GetBool(map, "showCounters", c.ShowCounters);
                c.CpsWindowMs = Clamp(GetInt(map, "cpsWindowMs", c.CpsWindowMs), 500, 3000);
                c.TileBackdrop = Clamp(GetInt(map, "tileBackdrop", c.TileBackdrop), 0, 100);
                c.PosX = GetInt(map, "posX", c.PosX);
                c.PosY = GetInt(map, "posY", c.PosY);
                c.AutoStart = GetBool(map, "autoStart", c.AutoStart);
                c.Visible = GetBool(map, "visible", c.Visible);
                c.HintShown = GetBool(map, "hintShown", c.HintShown);
            }
            catch { }
            return c;
        }

        public void Save()
        {
            try
            {
                StringBuilder sb = new StringBuilder();
                sb.AppendLine("{");
                sb.AppendLine("  \"accent\": \"" + Accent + "\",");
                sb.AppendLine("  \"recentAccent\": \"" + RecentAccent + "\",");
                sb.AppendLine("  \"scale\": " + Scale.ToString(CultureInfo.InvariantCulture) + ",");
                sb.AppendLine("  \"opacity\": " + Opacity.ToString(CultureInfo.InvariantCulture) + ",");
                sb.AppendLine("  \"showCps\": " + (ShowCps ? "true" : "false") + ",");
                sb.AppendLine("  \"showCounters\": " + (ShowCounters ? "true" : "false") + ",");
                sb.AppendLine("  \"cpsWindowMs\": " + CpsWindowMs.ToString(CultureInfo.InvariantCulture) + ",");
                sb.AppendLine("  \"tileBackdrop\": " + TileBackdrop.ToString(CultureInfo.InvariantCulture) + ",");
                sb.AppendLine("  \"posX\": " + PosX.ToString(CultureInfo.InvariantCulture) + ",");
                sb.AppendLine("  \"posY\": " + PosY.ToString(CultureInfo.InvariantCulture) + ",");
                sb.AppendLine("  \"autoStart\": " + (AutoStart ? "true" : "false") + ",");
                sb.AppendLine("  \"visible\": " + (Visible ? "true" : "false") + ",");
                sb.AppendLine("  \"hintShown\": " + (HintShown ? "true" : "false"));
                sb.AppendLine("}");
                File.WriteAllText(FilePath, sb.ToString(), Encoding.UTF8);
            }
            catch { }
        }

        public static int Clamp(int v, int lo, int hi)
        {
            if (v < lo) return lo;
            if (v > hi) return hi;
            return v;
        }

        private static string GetStr(Dictionary<string, string> m, string k, string def)
        {
            string v;
            if (m.TryGetValue(k, out v) && v.Length > 0) return v;
            return def;
        }

        private static int GetInt(Dictionary<string, string> m, string k, int def)
        {
            string v;
            int r;
            if (m.TryGetValue(k, out v) && int.TryParse(v, NumberStyles.Integer, CultureInfo.InvariantCulture, out r)) return r;
            return def;
        }

        private static bool GetBool(Dictionary<string, string> m, string k, bool def)
        {
            string v;
            if (m.TryGetValue(k, out v))
            {
                if (v == "true") return true;
                if (v == "false") return false;
            }
            return def;
        }
    }

    /// <summary>Tiny reader for the flat one-level JSON this app writes.</summary>
    internal static class MiniJson
    {
        public static Dictionary<string, string> ParseFlat(string json)
        {
            Dictionary<string, string> map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            int i = 0;
            while (i < json.Length)
            {
                int keyStart = json.IndexOf('"', i);
                if (keyStart < 0) break;
                int keyEnd = json.IndexOf('"', keyStart + 1);
                if (keyEnd < 0) break;
                string key = json.Substring(keyStart + 1, keyEnd - keyStart - 1);

                int colon = json.IndexOf(':', keyEnd + 1);
                if (colon < 0) break;

                int p = colon + 1;
                while (p < json.Length && char.IsWhiteSpace(json[p])) p++;
                if (p >= json.Length) break;

                string value;
                if (json[p] == '"')
                {
                    int vEnd = json.IndexOf('"', p + 1);
                    if (vEnd < 0) break;
                    value = json.Substring(p + 1, vEnd - p - 1);
                    i = vEnd + 1;
                }
                else
                {
                    int vEnd = p;
                    while (vEnd < json.Length && json[vEnd] != ',' && json[vEnd] != '}' && json[vEnd] != '\n') vEnd++;
                    value = json.Substring(p, vEnd - p).Trim();
                    i = vEnd;
                }
                map[key] = value;
            }
            return map;
        }
    }
}
