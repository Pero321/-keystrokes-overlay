using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Windows.Forms;

namespace KeystrokesOverlay
{
    /// <summary>Palette and type scale of settings option 2a (dark game-tool).</summary>
    internal static class Theme
    {
        public static readonly Color Bg = Color.FromArgb(0x0F, 0x11, 0x15);
        public static readonly Color Border = Color.FromArgb(23, 255, 255, 255);   // rgba(255,255,255,.09)
        public static readonly Color Divider = Color.FromArgb(18, 255, 255, 255);  // rgba(255,255,255,.07)
        public static readonly Color Text = Color.White;
        public static readonly Color Section = Color.FromArgb(191, 255, 255, 255); // .75
        public static readonly Color Label = Color.FromArgb(128, 255, 255, 255);   // .5
        public static readonly Color Faint = Color.FromArgb(89, 255, 255, 255);    // .35
        public static readonly Color Ghost = Color.FromArgb(77, 255, 255, 255);    // .3
        public static readonly Color Track = Color.FromArgb(31, 255, 255, 255);    // .12
        public static readonly Color TrackOff = Color.FromArgb(36, 255, 255, 255); // .14
        public static readonly Color KnobOff = Color.FromArgb(140, 255, 255, 255); // .55
        public static readonly Color OnAccentInk = Color.FromArgb(0x10, 0x12, 0x16);
        public static readonly Color CloseHover = Color.FromArgb(0xFF, 0x5A, 0x5A);

        public static Font Mono(float px, bool boldFace)
        {
            return Fonts.Px(boldFace ? Fonts.Bold : Fonts.Medium, px);
        }

        public static GraphicsPath Round(RectangleF r, float radius)
        {
            float d = Math.Min(radius * 2f, Math.Min(r.Width, r.Height));
            GraphicsPath p = new GraphicsPath();
            if (d <= 0.5f) { p.AddRectangle(r); return p; }
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }

        public static Color Mix(Color a, Color b, float t)
        {
            return Color.FromArgb(
                (int)(a.R + (b.R - a.R) * t),
                (int)(a.G + (b.G - a.G) * t),
                (int)(a.B + (b.B - a.B) * t));
        }

        /// <summary>Dark ink on light accents, white on dark ones.</summary>
        public static Color OnAccent(Color accent)
        {
            double lum = (0.299 * accent.R + 0.587 * accent.G + 0.114 * accent.B) / 255.0;
            return lum > 0.5 ? OnAccentInk : Color.White;
        }

        private static readonly StringFormat Tight = MakeTight();

        private static StringFormat MakeTight()
        {
            StringFormat sf = new StringFormat(StringFormat.GenericTypographic);
            sf.FormatFlags |= StringFormatFlags.NoClip | StringFormatFlags.NoWrap;
            return sf;
        }

        public static float MeasureText(Graphics g, string text, Font f)
        {
            // the typographic format drops a lone space, which collapses tracked text
            if (text == " ") return g.MeasureString("0", f, PointF.Empty, Tight).Width;
            return g.MeasureString(text, f, PointF.Empty, Tight).Width;
        }

        public static void DrawText(Graphics g, string text, Font f, Color c, float x, float y)
        {
            using (SolidBrush b = new SolidBrush(c)) g.DrawString(text, f, b, x, y, Tight);
        }

        /// <summary>Vertically centres text on <paramref name="cy"/> using the glyph box.</summary>
        public static void DrawTextMid(Graphics g, string text, Font f, Color c, float x, float cy)
        {
            SizeF sz = g.MeasureString(text, f, PointF.Empty, Tight);
            DrawText(g, text, f, c, x, cy - sz.Height / 2f);
        }

        public static float MeasureTracked(Graphics g, string text, Font f, float tracking)
        {
            float w = 0f;
            for (int i = 0; i < text.Length; i++)
            {
                w += MeasureText(g, text[i].ToString(), f);
                if (i < text.Length - 1) w += tracking;
            }
            return w;
        }

        /// <summary>GDI+ has no letter-spacing, so tracked text is drawn glyph by glyph.</summary>
        public static void DrawTracked(Graphics g, string text, Font f, Color c, float x, float cy, float tracking)
        {
            float cx = x;
            for (int i = 0; i < text.Length; i++)
            {
                string ch = text[i].ToString();
                DrawTextMid(g, ch, f, c, cx, cy);
                cx += MeasureText(g, ch, f) + tracking;
            }
        }
    }

    internal interface IAccentAware
    {
        Color Accent { set; }
    }

    internal abstract class UiControl : Control
    {
        protected UiControl()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint
                   | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
            BackColor = Theme.Bg;
        }

        protected static void Prepare(Graphics g)
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.TextRenderingHint = TextRenderingHint.AntiAlias;
        }
    }

    // ---------------------------------------------------------------- slider

    /// <summary>4px track, accent fill, 14px white knob — one row of the Appearance group.</summary>
    internal class UiSlider : UiControl, IAccentAware
    {
        private int _min, _max = 100, _value = 50, _step = 1;
        private bool _dragging;
        private Color _accent = Color.Magenta;

        public event EventHandler ValueChanged;

        public UiSlider()
        {
            Height = 20;
            SetStyle(ControlStyles.Selectable, true);
            TabStop = true;
        }

        public Color Accent { set { _accent = value; Invalidate(); } }
        public int Minimum { get { return _min; } set { _min = value; Invalidate(); } }
        public int Maximum { get { return _max; } set { _max = value; Invalidate(); } }
        public int Step { get { return _step; } set { _step = Math.Max(1, value); } }

        public int Value
        {
            get { return _value; }
            set
            {
                int v = Math.Max(_min, Math.Min(_max, value));
                if (v == _value) return;
                _value = v;
                Invalidate();
                if (ValueChanged != null) ValueChanged(this, EventArgs.Empty);
            }
        }

        private const float KnobR = 7f;

        private void SetFromX(int x)
        {
            float t = (x - KnobR) / Math.Max(1f, Width - KnobR * 2f);
            t = Math.Max(0f, Math.Min(1f, t));
            int raw = (int)Math.Round(_min + t * (_max - _min));
            Value = (int)Math.Round((raw - _min) / (double)_step) * _step + _min;
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button != MouseButtons.Left) return;
            _dragging = true;
            Focus();
            SetFromX(e.X);
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            if (_dragging) SetFromX(e.X);
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            base.OnMouseUp(e);
            _dragging = false;
        }

        protected override bool IsInputKey(Keys keyData)
        {
            if (keyData == Keys.Left || keyData == Keys.Right) return true;
            return base.IsInputKey(keyData);
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (e.KeyCode == Keys.Left) Value = _value - _step;
            else if (e.KeyCode == Keys.Right) Value = _value + _step;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            Prepare(g);
            float cy = Height / 2f;
            float x0 = KnobR, x1 = Width - KnobR;
            float t = (_value - _min) / (float)Math.Max(1, _max - _min);
            float cx = x0 + (x1 - x0) * t;

            using (GraphicsPath track = Theme.Round(new RectangleF(0, cy - 2f, Width, 4f), 2f))
            using (SolidBrush b = new SolidBrush(Theme.Track))
                g.FillPath(b, track);

            using (GraphicsPath fill = Theme.Round(new RectangleF(0, cy - 2f, Math.Max(4f, cx), 4f), 2f))
            using (SolidBrush b = new SolidBrush(_accent))
                g.FillPath(b, fill);

            if (Focused)
            {
                using (SolidBrush halo = new SolidBrush(Color.FromArgb(40, _accent)))
                    g.FillEllipse(halo, cx - KnobR - 4f, cy - KnobR - 4f, (KnobR + 4f) * 2f, (KnobR + 4f) * 2f);
            }
            using (SolidBrush shadow = new SolidBrush(Color.FromArgb(70, 0, 0, 0)))
                g.FillEllipse(shadow, cx - KnobR, cy - KnobR + 1f, KnobR * 2f, KnobR * 2f);
            using (SolidBrush knob = new SolidBrush(Color.White))
                g.FillEllipse(knob, cx - KnobR, cy - KnobR, KnobR * 2f, KnobR * 2f);
        }
    }

    // ---------------------------------------------------------------- toggle

    /// <summary>Label on the left, 34×19 pill on the right.</summary>
    internal class UiToggle : UiControl, IAccentAware
    {
        private bool _checked, _hover;
        private Color _accent = Color.Magenta;

        public event EventHandler CheckedChanged;

        public UiToggle()
        {
            Height = 22;
            Cursor = Cursors.Hand;
        }

        public Color Accent { set { _accent = value; Invalidate(); } }

        public bool Checked
        {
            get { return _checked; }
            set
            {
                if (_checked == value) return;
                _checked = value;
                Invalidate();
                if (CheckedChanged != null) CheckedChanged(this, EventArgs.Empty);
            }
        }

        public void SetCheckedSilently(bool value)
        {
            _checked = value;
            Invalidate();
        }

        protected override void OnMouseEnter(EventArgs e) { base.OnMouseEnter(e); _hover = true; Invalidate(); }
        protected override void OnMouseLeave(EventArgs e) { base.OnMouseLeave(e); _hover = false; Invalidate(); }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button == MouseButtons.Left) Checked = !_checked;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            Prepare(g);
            float cy = Height / 2f;

            Theme.DrawTextMid(g, Text, Theme.Mono(10f, false),
                _hover || _checked ? Color.FromArgb(200, 255, 255, 255) : Theme.Label, 0f, cy);

            RectangleF pill = new RectangleF(Width - 34f, cy - 9.5f, 34f, 19f);
            using (GraphicsPath p = Theme.Round(pill, 9.5f))
            using (SolidBrush b = new SolidBrush(_checked ? _accent : Theme.TrackOff))
                g.FillPath(b, p);

            float knob = 15f;
            float kx = _checked ? pill.Right - knob - 2f : pill.X + 2f;
            using (SolidBrush b = new SolidBrush(_checked ? Theme.OnAccent(_accent) : Theme.KnobOff))
                g.FillEllipse(b, kx, pill.Y + 2f, knob, knob);
        }
    }

    // ------------------------------------------------------------- segmented

    /// <summary>Three-way segmented control (CPS window).</summary>
    internal class UiSegmented : UiControl, IAccentAware
    {
        private string[] _items = new string[0];
        private int _index;
        private int _hover = -1;
        private Color _accent = Color.Magenta;

        public event EventHandler SelectedChanged;

        public UiSegmented()
        {
            Height = 26;
            Cursor = Cursors.Hand;
        }

        public Color Accent { set { _accent = value; Invalidate(); } }
        public string[] Items { get { return _items; } set { _items = value; Invalidate(); } }

        public int SelectedIndex
        {
            get { return _index; }
            set
            {
                if (_index == value) return;
                _index = value;
                Invalidate();
                if (SelectedChanged != null) SelectedChanged(this, EventArgs.Empty);
            }
        }

        public void SetIndexSilently(int value)
        {
            _index = value;
            Invalidate();
        }

        private int HitTest(int x)
        {
            if (_items.Length == 0) return -1;
            int i = (int)(x / (Width / (float)_items.Length));
            return Math.Max(0, Math.Min(_items.Length - 1, i));
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            int h = HitTest(e.X);
            if (h != _hover) { _hover = h; Invalidate(); }
        }

        protected override void OnMouseLeave(EventArgs e) { base.OnMouseLeave(e); _hover = -1; Invalidate(); }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button == MouseButtons.Left) SelectedIndex = HitTest(e.X);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            Prepare(g);
            RectangleF r = new RectangleF(0.5f, 0.5f, Width - 1f, Height - 1f);
            float seg = Width / (float)Math.Max(1, _items.Length);

            using (GraphicsPath p = Theme.Round(r, 7f))
            {
                Region old = g.Clip;
                g.SetClip(p);
                for (int i = 0; i < _items.Length; i++)
                {
                    bool on = i == _index;
                    if (on)
                    {
                        using (SolidBrush b = new SolidBrush(_accent))
                            g.FillRectangle(b, i * seg, 0, seg, Height);
                    }
                    else if (i == _hover)
                    {
                        using (SolidBrush b = new SolidBrush(Color.FromArgb(14, 255, 255, 255)))
                            g.FillRectangle(b, i * seg, 0, seg, Height);
                    }
                    Font f = Theme.Mono(10f, on);
                    float tw = Theme.MeasureText(g, _items[i], f);
                    Theme.DrawTextMid(g, _items[i], f, on ? Theme.OnAccent(_accent) : Theme.KnobOff,
                        i * seg + (seg - tw) / 2f, Height / 2f);
                }
                g.Clip = old;
                using (Pen pen = new Pen(Theme.Track, 1f)) g.DrawPath(pen, p);
            }
        }
    }

    // ---------------------------------------------------------------- button

    /// <summary>Primary (accent) or ghost button; optional dimmed hint text after the label.</summary>
    internal class UiButton : UiControl, IAccentAware
    {
        private bool _hover, _down;
        private Color _accent = Color.Magenta;

        public bool Primary;
        public string Hint;
        public float Tracking;
        public float FontPx = 11f;

        public UiButton(string text, bool primary)
        {
            Text = text;
            Primary = primary;
            Height = 34;
            Cursor = Cursors.Hand;
            Tracking = primary ? FontPx * 0.06f : 0f;
        }

        public Color Accent { set { _accent = value; Invalidate(); } }

        protected override void OnMouseEnter(EventArgs e) { base.OnMouseEnter(e); _hover = true; Invalidate(); }
        protected override void OnMouseLeave(EventArgs e) { base.OnMouseLeave(e); _hover = _down = false; Invalidate(); }
        protected override void OnMouseDown(MouseEventArgs e) { base.OnMouseDown(e); _down = true; Invalidate(); }
        protected override void OnMouseUp(MouseEventArgs e) { base.OnMouseUp(e); _down = false; Invalidate(); }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            Prepare(g);
            RectangleF r = new RectangleF(0.5f, 0.5f, Width - 1f, Height - 1f);

            Color fill, ink;
            if (Primary)
            {
                fill = _down ? Theme.Mix(_accent, Color.Black, 0.16f)
                     : _hover ? Theme.Mix(_accent, Color.White, 0.10f) : _accent;
                ink = Theme.OnAccent(_accent);
                using (GraphicsPath p = Theme.Round(r, 9f))
                using (SolidBrush b = new SolidBrush(fill))
                    g.FillPath(b, p);
            }
            else
            {
                ink = _hover ? Color.White : Color.FromArgb(200, 255, 255, 255);
                using (GraphicsPath p = Theme.Round(r, 9f))
                {
                    if (_hover)
                    {
                        using (SolidBrush b = new SolidBrush(Color.FromArgb(_down ? 20 : 12, 255, 255, 255)))
                            g.FillPath(b, p);
                    }
                    using (Pen pen = new Pen(Color.FromArgb(46, 255, 255, 255), 1f)) g.DrawPath(pen, p);
                }
            }

            Font f = Theme.Mono(FontPx, true);
            float w = Tracking > 0f ? Theme.MeasureTracked(g, Text, f, Tracking) : Theme.MeasureText(g, Text, f);
            float hintW = 0f;
            Font hf = null;
            if (!string.IsNullOrEmpty(Hint))
            {
                hf = Theme.Mono(FontPx, false);
                hintW = Theme.MeasureText(g, Hint, hf) + 8f;
            }
            float x = (Width - (w + hintW)) / 2f;
            float cy = Height / 2f;

            if (Tracking > 0f) Theme.DrawTracked(g, Text, f, ink, x, cy, Tracking);
            else Theme.DrawTextMid(g, Text, f, ink, x, cy);

            if (hf != null)
                Theme.DrawTextMid(g, Hint, hf, Color.FromArgb(140, ink), x + w + 8f, cy);
        }
    }

    // ------------------------------------------------------------------ link

    /// <summary>Small underlined text button used in the footer.</summary>
    internal class UiLink : UiControl
    {
        private bool _hover;

        public UiLink(string text)
        {
            Text = text;
            Height = 16;
            Cursor = Cursors.Hand;
        }

        protected override void OnMouseEnter(EventArgs e) { base.OnMouseEnter(e); _hover = true; Invalidate(); }
        protected override void OnMouseLeave(EventArgs e) { base.OnMouseLeave(e); _hover = false; Invalidate(); }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            Prepare(g);
            Font f = Theme.Mono(10f, false);
            Color c = _hover ? Color.FromArgb(220, 255, 255, 255) : Color.FromArgb(102, 255, 255, 255);
            Theme.DrawTextMid(g, Text, f, c, 0f, Height / 2f);
            float w = Theme.MeasureText(g, Text, f);
            using (Pen p = new Pen(c, 1f)) g.DrawLine(p, 0f, Height / 2f + 7f, w, Height / 2f + 7f);
        }
    }

    // ---------------------------------------------------------------- swatch

    /// <summary>24×24 colour chip; the last one is a dashed "+" that opens the picker.</summary>
    internal class UiSwatch : UiControl
    {
        private bool _hover;
        public Color Value = Color.Magenta;
        public bool Selected;
        public bool AddButton;

        public UiSwatch()
        {
            Size = new Size(24, 24);
            Cursor = Cursors.Hand;
        }

        protected override void OnMouseEnter(EventArgs e) { base.OnMouseEnter(e); _hover = true; Invalidate(); }
        protected override void OnMouseLeave(EventArgs e) { base.OnMouseLeave(e); _hover = false; Invalidate(); }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            Prepare(g);
            RectangleF r = new RectangleF(1f, 1f, Width - 2f, Height - 2f);

            if (AddButton)
            {
                using (GraphicsPath p = Theme.Round(r, 7f))
                using (Pen pen = new Pen(_hover ? Color.FromArgb(140, 255, 255, 255) : Color.FromArgb(77, 255, 255, 255), 1f))
                {
                    pen.DashStyle = DashStyle.Dash;
                    g.DrawPath(pen, p);
                }
                Font f = Theme.Mono(12f, false);
                float w = Theme.MeasureText(g, "+", f);
                Theme.DrawTextMid(g, "+", f, _hover ? Color.White : Theme.KnobOff, (Width - w) / 2f, Height / 2f - 1f);
                return;
            }

            using (GraphicsPath p = Theme.Round(r, 7f))
            using (SolidBrush b = new SolidBrush(Value))
                g.FillPath(b, p);

            if (Selected)
            {
                using (GraphicsPath p = Theme.Round(new RectangleF(1f, 1f, Width - 2f, Height - 2f), 7f))
                using (Pen pen = new Pen(Color.White, 2f))
                    g.DrawPath(pen, p);
            }
            else if (_hover)
            {
                using (GraphicsPath p = Theme.Round(r, 7f))
                using (Pen pen = new Pen(Color.FromArgb(110, 255, 255, 255), 2f))
                    g.DrawPath(pen, p);
            }
        }
    }

    // --------------------------------------------------------------- preview

    /// <summary>
    /// Live overlay preview over the diagonal-stripe backdrop from the spec; it mirrors
    /// real key and mouse state, so the settings can be judged while pressing keys.
    /// </summary>
    internal class UiPreview : UiControl
    {
        public Func<RenderModel> ModelProvider;

        public UiPreview()
        {
            Height = 150;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            Prepare(g);
            RectangleF r = new RectangleF(0.5f, 0.5f, Width - 1f, Height - 1f);

            using (GraphicsPath clip = Theme.Round(r, 10f))
            {
                Region old = g.Clip;
                g.SetClip(clip);

                using (SolidBrush b = new SolidBrush(Color.FromArgb(0x1C, 0x20, 0x27)))
                    g.FillRectangle(b, 0, 0, Width, Height);
                using (SolidBrush b = new SolidBrush(Color.FromArgb(0x20, 0x24, 0x2B)))
                {
                    // 10px diagonal stripes at 135°
                    for (float x = -Height; x < Width + Height; x += 20f)
                    {
                        PointF[] band =
                        {
                            new PointF(x, 0), new PointF(x + 10f, 0),
                            new PointF(x + 10f + Height, Height), new PointF(x + Height, Height)
                        };
                        g.FillPolygon(b, band);
                    }
                }

                if (ModelProvider != null)
                {
                    RenderModel m = ModelProvider();
                    using (Bitmap bmp = Renderer.Render(m))
                    {
                        float scale = Math.Min(1f, Math.Min((Width - 24f) / bmp.Width, (Height - 24f) / bmp.Height));
                        float w = bmp.Width * scale, h = bmp.Height * scale;
                        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                        g.DrawImage(bmp, (Width - w) / 2f, (Height - h) / 2f, w, h);
                    }
                }

                Theme.DrawTracked(g, "PREVIEW OVER GAMEPLAY", Theme.Mono(8f, false), Theme.Ghost, 11f, 13f, 8f * 0.12f);
                g.Clip = old;
            }

            using (GraphicsPath p = Theme.Round(r, 10f))
            using (Pen pen = new Pen(Color.FromArgb(15, 255, 255, 255), 1f))
                g.DrawPath(pen, p);
        }
    }
}
