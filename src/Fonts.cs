using System;
using System.Drawing;
using System.Drawing.Text;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;

namespace KeystrokesOverlay
{
    /// <summary>
    /// JetBrains Mono is embedded in the exe, so nothing has to be installed. The faces are
    /// registered twice: with GDI+ (for everything we paint ourselves) and with GDI
    /// (so plain WinForms controls such as the hex input can use them too).
    /// </summary>
    internal static class Fonts
    {
        [DllImport("gdi32.dll")]
        private static extern IntPtr AddFontMemResourceEx(IntPtr pbFont, uint cbFont, IntPtr pdv, out uint pcFonts);

        private static PrivateFontCollection _pfc;
        private static FontFamily _bold;   // weight 600/700
        private static FontFamily _medium; // weight 400/500

        public static FontFamily Bold { get { EnsureLoaded(); return _bold; } }
        public static FontFamily Medium { get { EnsureLoaded(); return _medium; } }

        private static void EnsureLoaded()
        {
            if (_pfc != null) return;
            _pfc = new PrivateFontCollection();
            FontFamily boldFam = AddResource("JetBrainsMono-Bold.ttf");
            FontFamily medFam = AddResource("JetBrainsMono-Medium.ttf");
            _bold = boldFam != null ? boldFam : FallbackFamily();
            _medium = medFam != null ? medFam : _bold;
        }

        private static FontFamily AddResource(string name)
        {
            try
            {
                Assembly asm = Assembly.GetExecutingAssembly();
                using (Stream s = asm.GetManifestResourceStream(name))
                {
                    if (s == null) return null;
                    byte[] data = new byte[s.Length];
                    int read = 0;
                    while (read < data.Length)
                    {
                        int n = s.Read(data, read, data.Length - read);
                        if (n <= 0) break;
                        read += n;
                    }
                    IntPtr p = Marshal.AllocCoTaskMem(data.Length);
                    Marshal.Copy(data, 0, p, data.Length);
                    // the buffer must stay allocated for the lifetime of the process
                    int before = _pfc.Families.Length;
                    _pfc.AddMemoryFont(p, data.Length);
                    uint installed;
                    AddFontMemResourceEx(p, (uint)data.Length, IntPtr.Zero, out installed);

                    FontFamily[] fams = _pfc.Families;
                    if (fams.Length > before) return fams[fams.Length - 1];
                    return null;
                }
            }
            catch { return null; }
        }

        private static FontFamily FallbackFamily()
        {
            try { return new FontFamily("Consolas"); }
            catch { return FontFamily.GenericMonospace; }
        }

        private static readonly System.Collections.Generic.Dictionary<string, Font> _cache =
            new System.Collections.Generic.Dictionary<string, Font>();

        /// <summary>
        /// Cached font sized in CSS-like pixels. Cached because creating fonts per frame
        /// costs more than everything else the renderer does. Never dispose the result.
        /// </summary>
        public static Font Px(FontFamily family, float pixels)
        {
            string key = family.Name + "|" + ((int)Math.Round(pixels * 10));
            Font cached;
            if (_cache.TryGetValue(key, out cached)) return cached;
            Font f = Create(family, pixels);
            if (_cache.Count > 64)
            {
                foreach (Font old in _cache.Values) old.Dispose();
                _cache.Clear();
            }
            _cache[key] = f;
            return f;
        }

        private static Font Create(FontFamily family, float pixels)
        {
            FontStyle[] order = { FontStyle.Regular, FontStyle.Bold, FontStyle.Italic };
            foreach (FontStyle st in order)
            {
                if (family.IsStyleAvailable(st)) return new Font(family, pixels, st, GraphicsUnit.Pixel);
            }
            return new Font(FontFamily.GenericMonospace, pixels, FontStyle.Bold, GraphicsUnit.Pixel);
        }
    }
}
