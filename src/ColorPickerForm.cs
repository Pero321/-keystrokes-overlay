using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace KeystrokesOverlay
{
    /// <summary>
    /// Custom accent picker (spec §5): saturation/value square, hue strip, hex field and a
    /// screen eyedropper. Dragging live-previews the colour in the real overlay; Cancel restores.
    /// </summary>
    internal class ColorPickerForm : Form
    {
        private const int W = 440;
        private const int TITLE_H = 44;
        private const int PAD = 18;

        private readonly Rectangle _fieldRect = new Rectangle(PAD, TITLE_H + 14, 250, 190);
        private readonly Rectangle _hueRect = new Rectangle(PAD + 262, TITLE_H + 14, 16, 190);
        private readonly Rectangle _swatchRect = new Rectangle(PAD + 294, TITLE_H + 14, 90, 50);

        private float _h, _s = 1f, _v = 1f;
        private Bitmap _field, _hueBar;
        private bool _dragField, _dragHue, _syncing, _closeHover;
        private TextBox _hex;
        private UiButton _select;

        public event EventHandler<ColorEventArgs> ColorPreview;

        public Color Result { get { return FromHsv(_h, _s, _v); } }

        public ColorPickerForm(Color initial)
        {
            Text = "Keystrokes Overlay — custom color";
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.CenterParent;
            ClientSize = new Size(W, 338);
            BackColor = Theme.Bg;
            ForeColor = Theme.Text;
            DoubleBuffered = true;
            KeyPreview = true;
            ShowInTaskbar = false;

            ToHsv(initial, out _h, out _s, out _v);
            BuildHueBar();
            BuildField();
            BuildControls();
        }

        protected override void OnSizeChanged(EventArgs e)
        {
            base.OnSizeChanged(e);
            if (IsHandleCreated) ApplyRoundedCorners();
        }

        /// <summary>Applied after the final size is known — doing it at handle creation clipped the footer.</summary>
        private void ApplyRoundedCorners()
        {
            Region old = Region;
            using (GraphicsPath p = Theme.Round(new RectangleF(0, 0, ClientSize.Width, ClientSize.Height), 12f))
                Region = new Region(p);
            if (old != null) old.Dispose();
        }

        private void BuildControls()
        {
            _hex = new TextBox();
            _hex.BorderStyle = BorderStyle.None;
            _hex.BackColor = Color.FromArgb(0x17, 0x1A, 0x20);
            _hex.ForeColor = Theme.Text;
            _hex.Font = Theme.Mono(12f, false);
            _hex.Location = new Point(_swatchRect.X + 8, _swatchRect.Bottom + 44);
            _hex.Size = new Size(_swatchRect.Width - 16, 18);
            _hex.MaxLength = 7;
            _hex.TextChanged += OnHexChanged;
            Controls.Add(_hex);

            UiButton dropper = new UiButton("Eyedropper", false);
            dropper.FontPx = 10f;
            dropper.Location = new Point(_swatchRect.X, _swatchRect.Bottom + 78);
            dropper.Size = new Size(_swatchRect.Width, 30);
            dropper.Click += OnEyedropper;
            Controls.Add(dropper);

            UiButton cancel = new UiButton("Cancel", false);
            cancel.FontPx = 10f;
            cancel.Location = new Point(W - PAD - 84 - 8 - 84, ClientSize.Height - PAD - 32);
            cancel.Size = new Size(84, 32);
            cancel.Click += delegate { DialogResult = DialogResult.Cancel; Close(); };
            Controls.Add(cancel);

            _select = new UiButton("Select", true);
            _select.FontPx = 10f;
            _select.Location = new Point(W - PAD - 84, ClientSize.Height - PAD - 32);
            _select.Size = new Size(84, 32);
            _select.Click += delegate { DialogResult = DialogResult.OK; Close(); };
            Controls.Add(_select);

            SyncHex(false);
        }

        // ---- painting ------------------------------------------------------

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;

            Theme.DrawText(g, "Custom accent color", Theme.Mono(12f, true), Theme.Text, PAD, 14f);
            Theme.DrawTextMid(g, "✕", Theme.Mono(12f, false), _closeHover ? Theme.CloseHover : Theme.Faint,
                W - PAD - 10f, TITLE_H / 2f);
            using (Pen p = new Pen(Theme.Divider)) g.DrawLine(p, 0, TITLE_H, W, TITLE_H);

            g.DrawImage(_field, _fieldRect);
            g.DrawImage(_hueBar, _hueRect);

            // field cursor
            float cx = _fieldRect.X + _s * _fieldRect.Width;
            float cy = _fieldRect.Y + (1f - _v) * _fieldRect.Height;
            using (Pen p = new Pen(Color.FromArgb(190, 0, 0, 0), 3f)) g.DrawEllipse(p, cx - 6, cy - 6, 12, 12);
            using (Pen p = new Pen(Color.White, 1.6f)) g.DrawEllipse(p, cx - 6, cy - 6, 12, 12);

            // hue marker
            float hy = _hueRect.Y + (_h / 360f) * _hueRect.Height;
            using (SolidBrush b = new SolidBrush(Color.White))
                g.FillRectangle(b, _hueRect.X - 3f, hy - 2f, _hueRect.Width + 6f, 4f);
            using (Pen p = new Pen(Color.FromArgb(150, 0, 0, 0), 1f))
                g.DrawRectangle(p, _hueRect.X - 3f, hy - 2f, _hueRect.Width + 6f, 4f);

            // current colour
            using (GraphicsPath p = Theme.Round(_swatchRect, 8f))
            using (SolidBrush b = new SolidBrush(Result))
                g.FillPath(b, p);

            Theme.DrawText(g, "HEX", Theme.Mono(10f, false), Theme.Label, _swatchRect.X, _swatchRect.Bottom + 20f);
            using (GraphicsPath p = Theme.Round(
                new RectangleF(_swatchRect.X, _swatchRect.Bottom + 38f, _swatchRect.Width, 30f), 7f))
            {
                using (SolidBrush b = new SolidBrush(Color.FromArgb(0x17, 0x1A, 0x20))) g.FillPath(b, p);
                using (Pen pen = new Pen(Color.FromArgb(46, 255, 255, 255), 1f)) g.DrawPath(pen, p);
            }

            Theme.DrawText(g, "click the field or paste a HEX", Theme.Mono(10f, false),
                Color.FromArgb(102, 255, 255, 255), PAD, _fieldRect.Bottom + 12f);

            using (GraphicsPath p = Theme.Round(new RectangleF(0.5f, 0.5f, W - 1f, ClientSize.Height - 1f), 12f))
            using (Pen pen = new Pen(Theme.Border, 1f))
                g.DrawPath(pen, p);
        }

        private void BuildHueBar()
        {
            _hueBar = new Bitmap(_hueRect.Width, _hueRect.Height, PixelFormat.Format32bppArgb);
            for (int y = 0; y < _hueBar.Height; y++)
            {
                Color c = FromHsv(y * 360f / _hueBar.Height, 1f, 1f);
                for (int x = 0; x < _hueBar.Width; x++) _hueBar.SetPixel(x, y, c);
            }
        }

        private void BuildField()
        {
            if (_field == null)
                _field = new Bitmap(_fieldRect.Width, _fieldRect.Height, PixelFormat.Format32bppArgb);

            BitmapData bd = _field.LockBits(new Rectangle(0, 0, _field.Width, _field.Height),
                ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try
            {
                byte[] row = new byte[bd.Stride];
                for (int y = 0; y < _field.Height; y++)
                {
                    float v = 1f - y / (float)(_field.Height - 1);
                    for (int x = 0; x < _field.Width; x++)
                    {
                        Color c = FromHsv(_h, x / (float)(_field.Width - 1), v);
                        int i = x * 4;
                        row[i] = c.B; row[i + 1] = c.G; row[i + 2] = c.R; row[i + 3] = 255;
                    }
                    Marshal.Copy(row, 0, new IntPtr(bd.Scan0.ToInt64() + (long)y * bd.Stride), bd.Stride);
                }
            }
            finally { _field.UnlockBits(bd); }
        }

        // ---- interaction ---------------------------------------------------

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Y < TITLE_H)
            {
                if (e.X > W - 38) { DialogResult = DialogResult.Cancel; Close(); return; }
                Native.ReleaseCapture();
                Native.SendMessage(Handle, Native.WM_NCLBUTTONDOWN, new IntPtr(Native.HTCAPTION), IntPtr.Zero);
                return;
            }
            if (_fieldRect.Contains(e.Location)) { _dragField = true; PickField(e.Location); }
            else if (_hueRect.Contains(e.Location)) { _dragHue = true; PickHue(e.Y); }
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            if (_dragField) PickField(e.Location);
            else if (_dragHue) PickHue(e.Y);
            else
            {
                bool hover = e.Y < TITLE_H && e.X > W - 38;
                if (hover != _closeHover) { _closeHover = hover; Invalidate(new Rectangle(W - 40, 0, 40, TITLE_H)); }
            }
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            base.OnMouseUp(e);
            _dragField = _dragHue = false;
        }

        private void PickField(Point p)
        {
            _s = Math.Max(0f, Math.Min(1f, (p.X - _fieldRect.X) / (float)_fieldRect.Width));
            _v = 1f - Math.Max(0f, Math.Min(1f, (p.Y - _fieldRect.Y) / (float)_fieldRect.Height));
            SyncHex(true);
            Invalidate();
        }

        private void PickHue(int y)
        {
            _h = Math.Max(0f, Math.Min(359.9f, (y - _hueRect.Y) * 360f / _hueRect.Height));
            BuildField();
            SyncHex(true);
            Invalidate();
        }

        private void SyncHex(bool raisePreview)
        {
            _syncing = true;
            _hex.Text = Renderer.ToHex(Result);
            _syncing = false;
            if (_select != null) _select.Accent = Result;
            if (raisePreview && ColorPreview != null) ColorPreview(this, new ColorEventArgs(Result));
        }

        private void OnHexChanged(object sender, EventArgs e)
        {
            if (_syncing) return;
            string t = _hex.Text.Trim();
            if (t.Length != 7 && t.Length != 4) return;
            Color c = Renderer.ParseHex(t, Color.Empty);
            if (c.IsEmpty) return;
            ToHsv(c, out _h, out _s, out _v);
            BuildField();
            if (_select != null) _select.Accent = Result;
            if (ColorPreview != null) ColorPreview(this, new ColorEventArgs(Result));
            Invalidate();
        }

        private void OnEyedropper(object sender, EventArgs e)
        {
            using (EyedropperForm eye = new EyedropperForm())
            {
                Hide();
                DialogResult r = eye.ShowDialog();
                Show();
                if (r == DialogResult.OK)
                {
                    ToHsv(eye.Picked, out _h, out _s, out _v);
                    BuildField();
                    SyncHex(true);
                    Invalidate();
                }
            }
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            ApplyRoundedCorners();
            ActiveControl = null; // don't open with the hex field selected
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (e.KeyCode == Keys.Escape) { DialogResult = DialogResult.Cancel; Close(); }
            else if (e.KeyCode == Keys.Enter && !_hex.Focused) { DialogResult = DialogResult.OK; Close(); }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                if (_field != null) _field.Dispose();
                if (_hueBar != null) _hueBar.Dispose();
            }
            base.Dispose(disposing);
        }

        // ---- colour maths --------------------------------------------------

        public static Color FromHsv(float h, float s, float v)
        {
            h = ((h % 360f) + 360f) % 360f;
            float c = v * s;
            float x = c * (1f - Math.Abs((h / 60f) % 2f - 1f));
            float m = v - c;
            float r = 0, g = 0, b = 0;
            if (h < 60) { r = c; g = x; }
            else if (h < 120) { r = x; g = c; }
            else if (h < 180) { g = c; b = x; }
            else if (h < 240) { g = x; b = c; }
            else if (h < 300) { r = x; b = c; }
            else { r = c; b = x; }
            return Color.FromArgb((int)Math.Round((r + m) * 255), (int)Math.Round((g + m) * 255), (int)Math.Round((b + m) * 255));
        }

        public static void ToHsv(Color c, out float h, out float s, out float v)
        {
            float r = c.R / 255f, g = c.G / 255f, b = c.B / 255f;
            float max = Math.Max(r, Math.Max(g, b));
            float min = Math.Min(r, Math.Min(g, b));
            float d = max - min;
            if (d < 0.0001f) h = 0f;
            else if (max == r) h = 60f * (((g - b) / d) % 6f);
            else if (max == g) h = 60f * (((b - r) / d) + 2f);
            else h = 60f * (((r - g) / d) + 4f);
            if (h < 0) h += 360f;
            s = max <= 0f ? 0f : d / max;
            v = max;
        }
    }

    /// <summary>Full-screen frozen snapshot with a magnifier; click samples a pixel.</summary>
    internal class EyedropperForm : Form
    {
        private readonly Bitmap _shot;
        public Color Picked = Color.Empty;
        private Point _cursor;

        public EyedropperForm()
        {
            Rectangle v = SystemInformation.VirtualScreen;
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.Manual;
            Bounds = v;
            TopMost = true;
            ShowInTaskbar = false;
            DoubleBuffered = true;
            Cursor = Cursors.Cross;
            KeyPreview = true;

            _shot = new Bitmap(v.Width, v.Height, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(_shot))
                g.CopyFromScreen(v.Left, v.Top, 0, 0, new Size(v.Width, v.Height));
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.DrawImageUnscaled(_shot, 0, 0);

            if (_cursor.IsEmpty) return;
            const int src = 11, zoom = 9;
            int box = src * zoom;
            int bx = _cursor.X + 24, by = _cursor.Y + 24;
            if (bx + box > Width) bx = _cursor.X - 24 - box;
            if (by + box + 26 > Height) by = _cursor.Y - 24 - box - 26;

            g.InterpolationMode = InterpolationMode.NearestNeighbor;
            g.PixelOffsetMode = PixelOffsetMode.Half;
            g.DrawImage(_shot, new Rectangle(bx, by, box, box),
                new Rectangle(_cursor.X - src / 2, _cursor.Y - src / 2, src, src), GraphicsUnit.Pixel);

            using (Pen p = new Pen(Color.White, 2f)) g.DrawRectangle(p, bx, by, box, box);
            using (Pen p = new Pen(Color.FromArgb(160, 0, 0, 0), 1f)) g.DrawRectangle(p, bx - 1, by - 1, box + 2, box + 2);
            using (Pen p = new Pen(Color.White, 1f))
                g.DrawRectangle(p, bx + (src / 2) * zoom, by + (src / 2) * zoom, zoom, zoom);

            Color c = At(_cursor);
            using (SolidBrush b = new SolidBrush(Color.FromArgb(230, 12, 13, 16)))
                g.FillRectangle(b, bx, by + box + 4, box, 22);
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;
            Theme.DrawText(g, Renderer.ToHex(c), Theme.Mono(11f, true), Color.White, bx + 6, by + box + 9);
        }

        private Color At(Point p)
        {
            int x = Math.Max(0, Math.Min(_shot.Width - 1, p.X));
            int y = Math.Max(0, Math.Min(_shot.Height - 1, p.Y));
            return _shot.GetPixel(x, y);
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            _cursor = e.Location;
            Invalidate();
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button == MouseButtons.Left)
            {
                Picked = At(e.Location);
                DialogResult = DialogResult.OK;
            }
            else DialogResult = DialogResult.Cancel;
            Close();
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (e.KeyCode == Keys.Escape) { DialogResult = DialogResult.Cancel; Close(); }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing && _shot != null) _shot.Dispose();
            base.Dispose(disposing);
        }
    }
}
