using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Drawing.Text;
using System.Globalization;
using System.Runtime.InteropServices;

namespace KeystrokesOverlay
{
    internal class RenderModel
    {
        public bool[] Down = new bool[6];
        public int LeftCps, RightCps;
        public long LeftTotal, RightTotal;
        public bool ShowCps = true;
        public bool ShowCounters;
        public float Scale = 1f;
        public float Backdrop = 0.55f; // 0..1 — dark plate behind idle tiles
        public Color Accent = Color.FromArgb(0xE4, 0x55, 0xE0);
        public bool MoveMode;
        public string Hint; // first-run caption under the widget

        public string Signature()
        {
            return (Down[0] ? "1" : "0") + (Down[1] ? "1" : "0") + (Down[2] ? "1" : "0") + (Down[3] ? "1" : "0")
                 + (Down[4] ? "1" : "0") + (Down[5] ? "1" : "0")
                 + "|" + LeftCps + "|" + RightCps
                 + "|" + (ShowCounters ? LeftTotal + "/" + RightTotal : "-")
                 + "|" + (ShowCps ? "c" : "-") + (ShowCounters ? "n" : "-")
                 + "|" + Scale.ToString("0.00", CultureInfo.InvariantCulture)
                 + "|" + Backdrop.ToString("0.00", CultureInfo.InvariantCulture)
                 + "|" + Accent.ToArgb().ToString(CultureInfo.InvariantCulture)
                 + "|" + (MoveMode ? "m" : "-")
                 + "|" + (Hint == null ? "-" : Hint);
        }
    }

    /// <summary>Draws the "neon outline" (variant 1c) overlay into a 32-bit ARGB bitmap.</summary>
    internal static class Renderer
    {
        // base geometry, in CSS pixels at 100 %
        private const float KEY_W = 42f, KEY_H = 38f, KEY_FONT = 16f;
        private const float MB_W = 66f, MB_H = 32f, MB_FONT = 13f;
        private const float GAP = 5f, RADIUS = 6f, BORDER = 2f;
        private const float CPS_FONT = 22f, CPS_SEP_FONT = 13f, CPS_LABEL_FONT = 10f;
        private const float COUNT_FONT = 9f;
        private const float HINT_FONT = 10f;
        private const float PAD = 20f; // room for the glow

        private static readonly Color IdleFill = Color.FromArgb(18, 255, 255, 255);   // rgba(255,255,255,.07)
        private static readonly Color IdleBorder = Color.FromArgb(115, 255, 255, 255); // rgba(255,255,255,.45)
        private static readonly Color IdleText = Color.White;
        private static readonly Color OnFill = Color.FromArgb(235, 255, 255, 255);    // rgba(255,255,255,.92)
        private static readonly Color OnBorder = Color.White;
        private static readonly Color OnText = Color.FromArgb(0x11, 0x12, 0x14);

        public static Bitmap Render(RenderModel m)
        {
            float s = m.Scale;
            float keyW = KEY_W * s, keyH = KEY_H * s;
            float mbW = MB_W * s, mbH = MB_H * s;
            float gap = GAP * s, pad = PAD * s;

            float rowKeysW = keyW * 3 + gap * 2;
            float rowMouseW = mbW * 2 + gap;
            float contentW = Math.Max(rowKeysW, rowMouseW);
            if (!string.IsNullOrEmpty(m.Hint))
            {
                // JetBrains Mono advance is 0.6em — enough to widen the canvas before measuring
                contentW = Math.Max(contentW, m.Hint.Length * HINT_FONT * s * 0.6f + 24f * s);
            }

            float cpsH = m.ShowCps ? CPS_FONT * s * 1.30f : 0f;
            bool hasHint = !string.IsNullOrEmpty(m.Hint);
            float hintH = hasHint ? HINT_FONT * s * 2.2f : 0f;

            float contentH = keyH + gap + keyH + gap + mbH
                           + (m.ShowCps ? gap + cpsH : 0f)
                           + (hasHint ? gap + hintH : 0f);

            int w = (int)Math.Ceiling(contentW + pad * 2);
            int h = (int)Math.Ceiling(contentH + pad * 2);

            Bitmap bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(bmp))
            {
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                g.TextRenderingHint = TextRenderingHint.AntiAlias;
                g.CompositingQuality = CompositingQuality.HighQuality;
                g.Clear(Color.Transparent);

                float left = pad + (contentW - rowKeysW) / 2f;
                float leftMouse = pad + (contentW - rowMouseW) / 2f;
                float y = pad;

                RectangleF rW = new RectangleF(pad + (contentW - keyW) / 2f, y, keyW, keyH);
                y += keyH + gap;
                RectangleF rA = new RectangleF(left, y, keyW, keyH);
                RectangleF rS = new RectangleF(left + keyW + gap, y, keyW, keyH);
                RectangleF rD = new RectangleF(left + (keyW + gap) * 2, y, keyW, keyH);
                y += keyH + gap;
                RectangleF rL = new RectangleF(leftMouse, y, mbW, mbH);
                RectangleF rR = new RectangleF(leftMouse + mbW + gap, y, mbW, mbH);
                y += mbH;

                if (m.MoveMode) DrawMoveBackdrop(g, w, h, m);

                // ---- glow of the pressed tiles (CSS: 0 0 16px accent, 0 0 4px #fff) ----
                RectangleF[] rects = { rW, rA, rS, rD, rL, rR };
                DrawGlow(g, bmp.Width, bmp.Height, rects, m, s);

                // ---- tiles ----
                float bd = Math.Max(0f, Math.Min(1f, m.Backdrop));
                DrawTile(g, rW, "W", KEY_FONT * s, m.Down[InputTracker.K_W], s, bd, null);
                DrawTile(g, rA, "A", KEY_FONT * s, m.Down[InputTracker.K_A], s, bd, null);
                DrawTile(g, rS, "S", KEY_FONT * s, m.Down[InputTracker.K_S], s, bd, null);
                DrawTile(g, rD, "D", KEY_FONT * s, m.Down[InputTracker.K_D], s, bd, null);

                // total click counters live under the LMB / RMB labels
                string lTotal = m.ShowCounters ? m.LeftTotal.ToString(CultureInfo.InvariantCulture) : null;
                string rTotal = m.ShowCounters ? m.RightTotal.ToString(CultureInfo.InvariantCulture) : null;
                DrawTile(g, rL, "LMB", MB_FONT * s, m.Down[InputTracker.K_LMB], s, bd, lTotal);
                DrawTile(g, rR, "RMB", MB_FONT * s, m.Down[InputTracker.K_RMB], s, bd, rTotal);

                if (m.ShowCps)
                {
                    y += gap;
                    DrawCpsLine(g, pad, y, contentW, cpsH, m, s, bd);
                    y += cpsH;
                }
                if (hasHint)
                {
                    y += gap;
                    DrawHint(g, pad, y, contentW, hintH, m, s);
                }
            }
            return bmp;
        }

        private static void DrawMoveBackdrop(Graphics g, int w, int h, RenderModel m)
        {
            RectangleF r = new RectangleF(1f, 1f, w - 2f, h - 2f);
            using (GraphicsPath p = RoundedRect(r, 10f * m.Scale))
            using (SolidBrush b = new SolidBrush(Color.FromArgb(120, 8, 8, 10)))
            using (Pen pen = new Pen(Color.FromArgb(200, m.Accent), 2f))
            {
                pen.DashStyle = DashStyle.Dash;
                g.FillPath(b, p);
                g.DrawPath(pen, p);
            }

            Font hintFont = Fonts.Px(Fonts.Medium, 9f * m.Scale);
            string hint = "drag · F9 to lock";
            float hintW = MeasureW(g, hint, hintFont);
            DrawWithShadow(g, hint, hintFont, Color.FromArgb(220, 255, 255, 255),
                (w - hintW) / 2f, h - PAD * m.Scale / 2f, m.Scale);
        }

        private static void DrawGlow(Graphics g, int w, int h, RectangleF[] rects, RenderModel m, float s)
        {
            for (int i = 0; i < rects.Length; i++)
            {
                if (!m.Down[i]) continue;
                RectangleF r = rects[i];
                GlowSprite sprite = GlowCache.Get(r.Width, r.Height, RADIUS * s, s, m.Accent);
                g.DrawImage(sprite.Bitmap, (int)Math.Round(r.X) - sprite.Margin, (int)Math.Round(r.Y) - sprite.Margin);
            }
        }

        private class GlowSprite
        {
            public Bitmap Bitmap;
            public int Margin;
        }

        /// <summary>
        /// Tile chrome (dark rim, contrast plate, fill, border) never changes for a given
        /// size/state, so it is painted once into a sprite and blitted afterwards.
        /// </summary>
        private static class TileCache
        {
            private static readonly System.Collections.Generic.Dictionary<string, GlowSprite> _cache =
                new System.Collections.Generic.Dictionary<string, GlowSprite>();

            public static GlowSprite Get(float w, float h, float s, bool on, float backdrop)
            {
                int iw = (int)Math.Round(w), ih = (int)Math.Round(h);
                int bdKey = (int)Math.Round(backdrop * 100f);
                string key = iw + "x" + ih + "s" + ((int)Math.Round(s * 100)) + (on ? "on" : "off") + "b" + bdKey;
                GlowSprite sprite;
                if (_cache.TryGetValue(key, out sprite)) return sprite;

                float bw = BORDER * s;
                int margin = (int)Math.Ceiling(bw + 2f);
                Bitmap bmp = new Bitmap(iw + margin * 2, ih + margin * 2, PixelFormat.Format32bppArgb);
                using (Graphics g = Graphics.FromImage(bmp))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                    g.Clear(Color.Transparent);
                    DrawTileChrome(g, new RectangleF(margin, margin, iw, ih), on, s, backdrop);
                }

                sprite = new GlowSprite();
                sprite.Bitmap = bmp;
                sprite.Margin = margin;

                if (_cache.Count > 24)
                {
                    foreach (GlowSprite old in _cache.Values) old.Bitmap.Dispose();
                    _cache.Clear();
                }
                _cache[key] = sprite;
                return sprite;
            }
        }

        private static void DrawTileChrome(Graphics g, RectangleF r, bool on, float s, float backdrop)
        {
            float bw = BORDER * s;

            // dark rim just outside the tile: without it a white border melts into a bright scene
            using (GraphicsPath outer = RoundedRect(RectangleF.Inflate(r, bw / 2f, bw / 2f), RADIUS * s + bw / 2f))
            using (Pen op = new Pen(Color.FromArgb((int)(70 + 90 * backdrop), 0, 0, 0), Math.Max(1f, 1.5f * s)))
                g.DrawPath(op, outer);

            RectangleF inner = RectangleF.Inflate(r, -bw / 2f, -bw / 2f);
            using (GraphicsPath p = RoundedRect(inner, RADIUS * s))
            using (Pen pen = new Pen(on ? OnBorder : IdleBorder, bw))
            {
                Color body = on ? OnFill : Over(IdleFill, PlateColor(backdrop));
                using (SolidBrush fill = new SolidBrush(body)) g.FillPath(fill, p);
                g.DrawPath(pen, p);
            }
        }

        private static Color PlateColor(float backdrop)
        {
            if (backdrop <= 0.002f) return Color.FromArgb(0, 0x0A, 0x0B, 0x0E);
            return Color.FromArgb((int)(235 * backdrop), 0x0A, 0x0B, 0x0E);
        }

        /// <summary>Source-over composite of two translucent colours, so one fill can replace two.</summary>
        private static Color Over(Color top, Color under)
        {
            float at = top.A / 255f, au = under.A / 255f;
            float outA = at + au * (1f - at);
            if (outA <= 0.0001f) return Color.FromArgb(0, 0, 0, 0);
            float r = (top.R * at + under.R * au * (1f - at)) / outA;
            float gg = (top.G * at + under.G * au * (1f - at)) / outA;
            float b = (top.B * at + under.B * au * (1f - at)) / outA;
            return Color.FromArgb((int)Math.Round(outA * 255f), (int)Math.Round(r), (int)Math.Round(gg), (int)Math.Round(b));
        }

        /// <summary>
        /// The halo only depends on tile size, scale and accent — so it is blurred once and
        /// then blitted, keeping per-frame cost far below the input-latency budget.
        /// </summary>
        private static class GlowCache
        {
            private static readonly System.Collections.Generic.Dictionary<string, GlowSprite> _cache =
                new System.Collections.Generic.Dictionary<string, GlowSprite>();

            public static GlowSprite Get(float w, float h, float radius, float s, Color accent)
            {
                int iw = (int)Math.Round(w), ih = (int)Math.Round(h);
                string key = iw + "x" + ih + "r" + ((int)Math.Round(radius)) + "s" + ((int)Math.Round(s * 100))
                           + "c" + accent.ToArgb();
                GlowSprite sprite;
                if (_cache.TryGetValue(key, out sprite)) return sprite;

                int rWide = Math.Max(1, (int)Math.Round(7f * s));
                int rTight = Math.Max(1, (int)Math.Round(2f * s));
                int margin = rWide * 3 + 2;
                int bw = iw + margin * 2, bh = ih + margin * 2;

                byte[] mask;
                using (Bitmap maskBmp = new Bitmap(bw, bh, PixelFormat.Format32bppArgb))
                {
                    using (Graphics mg = Graphics.FromImage(maskBmp))
                    {
                        mg.SmoothingMode = SmoothingMode.AntiAlias;
                        mg.Clear(Color.Transparent);
                        using (SolidBrush wb = new SolidBrush(Color.White))
                        using (GraphicsPath p = RoundedRect(new RectangleF(margin, margin, iw, ih), radius))
                            mg.FillPath(wb, p);
                    }
                    mask = ExtractAlpha(maskBmp);
                }

                Bitmap result = new Bitmap(bw, bh, PixelFormat.Format32bppArgb);
                using (Graphics rg = Graphics.FromImage(result))
                {
                    rg.Clear(Color.Transparent);
                    byte[] wide = Blur(CopyOf(mask), bw, bh, rWide, 3);
                    using (Bitmap halo = Colorize(wide, bw, bh, accent, 2.2f)) rg.DrawImage(halo, 0, 0);
                    byte[] tight = Blur(CopyOf(mask), bw, bh, rTight, 2);
                    using (Bitmap core = Colorize(tight, bw, bh, Color.White, 1.4f)) rg.DrawImage(core, 0, 0);
                }

                sprite = new GlowSprite();
                sprite.Bitmap = result;
                sprite.Margin = margin;

                if (_cache.Count > 24)
                {
                    foreach (GlowSprite old in _cache.Values) old.Bitmap.Dispose();
                    _cache.Clear();
                }
                _cache[key] = sprite;
                return sprite;
            }
        }

        private static void DrawTile(Graphics g, RectangleF r, string text, float fontPx, bool on, float s,
            float backdrop, string subText)
        {
            GlowSprite tile = TileCache.Get(r.Width, r.Height, s, on, backdrop);
            g.DrawImage(tile.Bitmap, (int)Math.Round(r.X) - tile.Margin, (int)Math.Round(r.Y) - tile.Margin);

            Color ink = on ? OnText : IdleText;
            if (string.IsNullOrEmpty(subText))
            {
                using (SolidBrush tb = new SolidBrush(ink))
                    DrawCentered(g, text, Fonts.Px(Fonts.Bold, fontPx), tb, r);
                return;
            }

            RectangleF top = new RectangleF(r.X, r.Y - 5f * s, r.Width, r.Height);
            RectangleF bottom = new RectangleF(r.X, r.Y + 9f * s, r.Width, r.Height);
            using (SolidBrush tb = new SolidBrush(ink))
                DrawCentered(g, text, Fonts.Px(Fonts.Bold, fontPx), tb, top);
            using (SolidBrush sb = new SolidBrush(Color.FromArgb(179, ink)))
                DrawCentered(g, subText, Fonts.Px(Fonts.Medium, COUNT_FONT * s), sb, bottom);
        }

        /// <summary>First-run caption: an accent-tinted pill telling the user which keys do what.</summary>
        private static void DrawHint(Graphics g, float x, float y, float width, float height, RenderModel m, float s)
        {
            Font f = Fonts.Px(Fonts.Medium, HINT_FONT * s);
            float tw = MeasureW(g, m.Hint, f);
            RectangleF r = new RectangleF(x + (width - tw) / 2f - 9f * s, y, tw + 18f * s, height);
            using (GraphicsPath p = RoundedRect(r, height / 2f))
            {
                using (SolidBrush b = new SolidBrush(Color.FromArgb(225, 0x0A, 0x0B, 0x0E))) g.FillPath(b, p);
                using (Pen pen = new Pen(Color.FromArgb(150, m.Accent), Math.Max(1f, 1.5f * s))) g.DrawPath(pen, p);
            }
            DrawWithShadow(g, m.Hint, f, Color.White, x + (width - tw) / 2f, y + height / 2f, s);
        }

        /// <summary>A soft dark pill behind a text row — far cheaper than outlining glyphs, and reads better.</summary>
        private static void DrawTextPlate(Graphics g, float cx, float cy, float w, float h, float s, float backdrop)
        {
            if (backdrop <= 0.002f) return;
            RectangleF r = new RectangleF(cx - w / 2f - 7f * s, cy - h / 2f, w + 14f * s, h);
            using (GraphicsPath p = RoundedRect(r, h / 2f))
            using (SolidBrush b = new SolidBrush(Color.FromArgb((int)(190 * backdrop), 0x0A, 0x0B, 0x0E)))
                g.FillPath(b, p);
        }

        private static void DrawCpsLine(Graphics g, float x, float y, float width, float height, RenderModel m, float s,
            float backdrop)
        {
            Font big = Fonts.Px(Fonts.Bold, CPS_FONT * s);
            Font sep = Fonts.Px(Fonts.Bold, CPS_SEP_FONT * s);
            Font lbl = Fonts.Px(Fonts.Medium, CPS_LABEL_FONT * s);
            {
                string l = m.LeftCps.ToString(CultureInfo.InvariantCulture);
                string r = m.RightCps.ToString(CultureInfo.InvariantCulture);
                float gap = 6f * s;
                float tracking = CPS_LABEL_FONT * s * 0.12f;

                float wl = MeasureW(g, l, big);
                float ws = MeasureW(g, "|", sep);
                float wr = MeasureW(g, r, big);
                float wc = MeasureTracked(g, "CPS", lbl, tracking);
                float total = wl + gap + ws + gap + wr + gap + wc;

                float cx = x + (width - total) / 2f;
                float baseline = y + height / 2f;

                DrawTextPlate(g, x + width / 2f, baseline, total, height * 0.92f, s, backdrop);

                DrawWithShadow(g, l, big, Color.White, cx, baseline, s);
                cx += wl + gap;
                DrawWithShadow(g, "|", sep, Color.FromArgb(153, 255, 255, 255), cx, baseline, s);
                cx += ws + gap;
                DrawWithShadow(g, r, big, Color.White, cx, baseline, s);
                cx += wr + gap;
                DrawTrackedWithShadow(g, "CPS", lbl, Color.FromArgb(204, 255, 255, 255), cx, baseline, tracking, s);
            }
        }

        // ---- text helpers -------------------------------------------------

        private static readonly StringFormat Tight = MakeTightFormat();

        private static StringFormat MakeTightFormat()
        {
            StringFormat sf = new StringFormat(StringFormat.GenericTypographic);
            sf.FormatFlags |= StringFormatFlags.NoClip | StringFormatFlags.NoWrap;
            sf.Alignment = StringAlignment.Near;
            sf.LineAlignment = StringAlignment.Near;
            return sf;
        }

        private static readonly System.Collections.Generic.Dictionary<string, SizeF> _measured =
            new System.Collections.Generic.Dictionary<string, SizeF>();

        /// <summary>MeasureString is the most expensive call in the frame; the strings repeat, so cache them.</summary>
        private static SizeF Measure(Graphics g, string text, Font f)
        {
            string key = f.Name + "|" + f.Size.ToString("0.0", CultureInfo.InvariantCulture) + "|" + text;
            SizeF sz;
            if (_measured.TryGetValue(key, out sz)) return sz;
            sz = g.MeasureString(text, f, PointF.Empty, Tight);
            if (_measured.Count > 512) _measured.Clear();
            _measured[key] = sz;
            return sz;
        }

        private static float MeasureW(Graphics g, string text, Font f)
        {
            return Measure(g, text, f).Width;
        }

        private static float MeasureTracked(Graphics g, string text, Font f, float tracking)
        {
            float w = 0f;
            for (int i = 0; i < text.Length; i++)
            {
                w += MeasureW(g, text[i].ToString(), f);
                if (i < text.Length - 1) w += tracking;
            }
            return w;
        }

        /// <summary>Draws text centred inside <paramref name="r"/> using the glyph box, not the line box.</summary>
        private static void DrawCentered(Graphics g, string text, Font f, Brush brush, RectangleF r)
        {
            SizeF sz = Measure(g, text, f);
            float tx = r.X + (r.Width - sz.Width) / 2f;
            float ty = r.Y + (r.Height - sz.Height) / 2f;
            g.DrawString(text, f, brush, tx, ty, Tight);
        }

        private static void DrawWithShadow(Graphics g, string text, Font f, Color color, float x, float centerY, float s)
        {
            SizeF sz = Measure(g, text, f);
            float y = centerY - sz.Height / 2f;
            using (SolidBrush sh = new SolidBrush(Color.FromArgb(120, 0, 0, 0)))
                g.DrawString(text, f, sh, x + 1f * s, y + 1.5f * s, Tight);
            using (SolidBrush b = new SolidBrush(color))
                g.DrawString(text, f, b, x, y, Tight);
        }

        private static void DrawTrackedWithShadow(Graphics g, string text, Font f, Color color, float x, float centerY,
            float tracking, float s)
        {
            float cx = x;
            for (int i = 0; i < text.Length; i++)
            {
                string ch = text[i].ToString();
                DrawWithShadow(g, ch, f, color, cx, centerY, s);
                cx += MeasureW(g, ch, f) + tracking;
            }
        }

        // ---- geometry / blur ----------------------------------------------

        private static GraphicsPath RoundedRect(RectangleF r, float radius)
        {
            float d = Math.Min(radius * 2f, Math.Min(r.Width, r.Height));
            GraphicsPath p = new GraphicsPath();
            if (d <= 0.1f)
            {
                p.AddRectangle(r);
                return p;
            }
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }

        private static byte[] CopyOf(byte[] a)
        {
            byte[] c = new byte[a.Length];
            Buffer.BlockCopy(a, 0, c, 0, a.Length);
            return c;
        }

        private static byte[] ExtractAlpha(Bitmap bmp)
        {
            int w = bmp.Width, h = bmp.Height;
            BitmapData bd = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            try
            {
                byte[] row = new byte[bd.Stride];
                byte[] a = new byte[w * h];
                for (int yy = 0; yy < h; yy++)
                {
                    Marshal.Copy(new IntPtr(bd.Scan0.ToInt64() + (long)yy * bd.Stride), row, 0, bd.Stride);
                    int o = yy * w;
                    for (int xx = 0; xx < w; xx++) a[o + xx] = row[xx * 4 + 3];
                }
                return a;
            }
            finally { bmp.UnlockBits(bd); }
        }

        private static Bitmap Colorize(byte[] alpha, int w, int h, Color color, float gain)
        {
            Bitmap bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
            BitmapData bd = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try
            {
                byte[] row = new byte[bd.Stride];
                byte cb = color.B, cg = color.G, cr = color.R;
                for (int yy = 0; yy < h; yy++)
                {
                    int o = yy * w;
                    for (int xx = 0; xx < w; xx++)
                    {
                        int a = (int)(alpha[o + xx] * gain);
                        if (a > 255) a = 255;
                        int i = xx * 4;
                        row[i] = cb; row[i + 1] = cg; row[i + 2] = cr; row[i + 3] = (byte)a;
                    }
                    Marshal.Copy(row, 0, new IntPtr(bd.Scan0.ToInt64() + (long)yy * bd.Stride), bd.Stride);
                }
            }
            finally { bmp.UnlockBits(bd); }
            return bmp;
        }

        /// <summary>Box blur repeated a few times ≈ a gaussian, which is what CSS blur looks like.</summary>
        private static byte[] Blur(byte[] a, int w, int h, int r, int passes)
        {
            byte[] cur = a;
            byte[] tmp = new byte[w * h];
            for (int p = 0; p < passes; p++)
            {
                BlurH(cur, tmp, w, h, r);
                BlurV(tmp, cur, w, h, r);
            }
            return cur;
        }

        private static void BlurH(byte[] src, byte[] dst, int w, int h, int r)
        {
            int win = r * 2 + 1;
            for (int y = 0; y < h; y++)
            {
                int o = y * w;
                int sum = 0;
                for (int i = -r; i <= r; i++) sum += src[o + Clamp(i, 0, w - 1)];
                for (int x = 0; x < w; x++)
                {
                    dst[o + x] = (byte)(sum / win);
                    sum += src[o + Clamp(x + r + 1, 0, w - 1)] - src[o + Clamp(x - r, 0, w - 1)];
                }
            }
        }

        private static void BlurV(byte[] src, byte[] dst, int w, int h, int r)
        {
            int win = r * 2 + 1;
            for (int x = 0; x < w; x++)
            {
                int sum = 0;
                for (int i = -r; i <= r; i++) sum += src[Clamp(i, 0, h - 1) * w + x];
                for (int y = 0; y < h; y++)
                {
                    dst[y * w + x] = (byte)(sum / win);
                    sum += src[Clamp(y + r + 1, 0, h - 1) * w + x] - src[Clamp(y - r, 0, h - 1) * w + x];
                }
            }
        }

        private static int Clamp(int v, int lo, int hi)
        {
            if (v < lo) return lo;
            if (v > hi) return hi;
            return v;
        }

        public static Color ParseHex(string hex, Color fallback)
        {
            try
            {
                if (hex == null) return fallback;
                string s = hex.Trim();
                if (s.StartsWith("#")) s = s.Substring(1);
                if (s.Length == 3)
                {
                    s = new string(new char[] { s[0], s[0], s[1], s[1], s[2], s[2] });
                }
                if (s.Length != 6) return fallback;
                int r = int.Parse(s.Substring(0, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture);
                int g = int.Parse(s.Substring(2, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture);
                int b = int.Parse(s.Substring(4, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture);
                return Color.FromArgb(r, g, b);
            }
            catch { return fallback; }
        }

        public static string ToHex(Color c)
        {
            return "#" + c.R.ToString("x2", CultureInfo.InvariantCulture)
                       + c.G.ToString("x2", CultureInfo.InvariantCulture)
                       + c.B.ToString("x2", CultureInfo.InvariantCulture);
        }
    }
}
