using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Globalization;
using System.Windows.Forms;
using Microsoft.Win32;

namespace KeystrokesOverlay
{
    /// <summary>Settings window, option 2a: preview first, one accent action, live apply.</summary>
    internal class SettingsForm : Form
    {
        public static readonly string[] Presets = { "#e455e0", "#ffd23f", "#5ee6a8", "#4ea8ff" };
        private static readonly int[] CpsWindows = { 500, 1000, 2000 };

        private const int W = 600;
        private const int TITLE_H = 47;
        private const int PADX = 18;
        private const int PADY = 16;
        private const int LABEL_W = 78;
        private const int VALUE_W = 42;
        private const int GAP = 16;
        private const int ROW_GAP = 11;

        private readonly Config _cfg;
        private readonly OverlayForm _overlay;

        private readonly List<UiSwatch> _swatches = new List<UiSwatch>();
        private UiSwatch _recent, _add;
        private UiPreview _preview;
        private UiSlider _scale, _opacity, _contrast;
        private UiSegmented _cpsWindow;
        private UiToggle _showCps, _showTotals, _autoStart;
        private readonly Timer _tick = new Timer();

        private int _yAppearance, _yScale, _yOpacity, _yContrast, _yColor;
        private int _yDivider, _yCounters, _yCpsWindow, _yFooter;

        private bool _loading;
        private bool _closeHover;

        public SettingsForm(Config cfg, OverlayForm overlay)
        {
            _cfg = cfg;
            _overlay = overlay;

            Text = "Keystrokes Overlay — settings";
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = Theme.Bg;
            ForeColor = Theme.Text;
            DoubleBuffered = true;
            KeyPreview = true;

            BuildUi();
            LoadValues();

            _tick.Interval = 60; // keeps the preview in sync with real key/mouse state
            _tick.Tick += delegate { if (_preview != null) _preview.Invalidate(); };
            _tick.Start();
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            ApplyRoundedCorners();
        }

        protected override void OnSizeChanged(EventArgs e)
        {
            base.OnSizeChanged(e);
            if (IsHandleCreated) ApplyRoundedCorners();
        }

        /// <summary>Radius-12 window, per the spec. Recomputed on resize so it can never clip content.</summary>
        private void ApplyRoundedCorners()
        {
            Region old = Region;
            using (GraphicsPath p = Theme.Round(new RectangleF(0, 0, ClientSize.Width, ClientSize.Height), 12f))
                Region = new Region(p);
            if (old != null) old.Dispose();
        }

        // ---- layout --------------------------------------------------------

        private void BuildUi()
        {
            int inner = W - PADX * 2;
            int y = TITLE_H + PADY;

            _preview = new UiPreview();
            _preview.Location = new Point(PADX, y);
            _preview.Size = new Size(inner, 150);
            _preview.ModelProvider = BuildPreviewModel;
            Controls.Add(_preview);
            y += 150 + GAP;

            UiButton move = new UiButton("Move overlay", true);
            move.Hint = "F9";
            move.Location = new Point(PADX, y);
            move.Size = new Size(inner, 38);
            move.Click += delegate { _overlay.SetMoveMode(true); };
            Controls.Add(move);
            y += 38 + GAP;

            _yAppearance = y;
            y += 16 + ROW_GAP;

            _yScale = y;
            _scale = MakeSlider(y, 60, 200, 5);
            _scale.ValueChanged += OnScaleChanged;
            y += 20 + ROW_GAP;

            _yOpacity = y;
            _opacity = MakeSlider(y, 30, 100, 2);
            _opacity.ValueChanged += OnOpacityChanged;
            y += 20 + ROW_GAP;

            _yContrast = y;
            _contrast = MakeSlider(y, 0, 100, 5);
            _contrast.ValueChanged += OnContrastChanged;
            y += 20 + ROW_GAP;

            _yColor = y;
            int sx = PADX + LABEL_W + 12;
            for (int i = 0; i < Presets.Length; i++)
            {
                UiSwatch sw = new UiSwatch();
                sw.Location = new Point(sx + i * 30, y);
                sw.Value = Renderer.ParseHex(Presets[i], Color.Magenta);
                sw.Tag = Presets[i];
                sw.Click += OnPresetClick;
                _swatches.Add(sw);
                Controls.Add(sw);
            }

            _recent = new UiSwatch();
            _recent.Location = new Point(sx + Presets.Length * 30, y);
            _recent.Visible = false;
            _recent.Click += OnRecentClick;
            Controls.Add(_recent);

            _add = new UiSwatch();
            _add.AddButton = true;
            _add.Location = new Point(sx + (Presets.Length + 1) * 30, y);
            _add.Click += OnCustomColor;
            Controls.Add(_add);
            y += 24 + GAP;

            _yDivider = y;
            y += 1 + GAP;

            _yCounters = y;
            y += 16 + ROW_GAP;

            _yCpsWindow = y;
            _cpsWindow = new UiSegmented();
            _cpsWindow.Items = new string[] { "0.5s", "1s", "2s" };
            _cpsWindow.Size = new Size(144, 26);
            _cpsWindow.Location = new Point(W - PADX - 144, y);
            _cpsWindow.SelectedChanged += OnCpsWindowChanged;
            Controls.Add(_cpsWindow);
            y += 26 + ROW_GAP;

            _showCps = MakeToggle("Show CPS", y);
            _showCps.CheckedChanged += OnShowCpsChanged;
            y += 22 + ROW_GAP;

            _showTotals = MakeToggle("Total click counters", y);
            _showTotals.CheckedChanged += OnShowTotalsChanged;
            y += 22 + ROW_GAP;

            _autoStart = MakeToggle("Start with Windows", y);
            _autoStart.CheckedChanged += OnAutoStartChanged;
            y += 22 + PADY;

            _yFooter = y;

            UiLink resetCounters = new UiLink("reset counters");
            resetCounters.Location = new Point(PADX, _yFooter + 12);
            resetCounters.Size = new Size(96, 16);
            resetCounters.Click += delegate { InputTracker.ResetCounters(); _overlay.ApplyConfig(); _preview.Invalidate(); };
            Controls.Add(resetCounters);

            UiLink resetPosition = new UiLink("reset position");
            resetPosition.Location = new Point(PADX + 96 + 16, _yFooter + 12);
            resetPosition.Size = new Size(96, 16);
            resetPosition.Click += delegate { _overlay.ResetPosition(); };
            Controls.Add(resetPosition);

            ClientSize = new Size(W, _yFooter + 40);
        }

        private UiSlider MakeSlider(int y, int min, int max, int step)
        {
            UiSlider s = new UiSlider();
            s.Location = new Point(PADX + LABEL_W + 12, y);
            s.Size = new Size(W - PADX * 2 - LABEL_W - 12 - VALUE_W - 12, 20);
            s.Minimum = min;
            s.Maximum = max;
            s.Step = step;
            Controls.Add(s);
            return s;
        }

        private UiToggle MakeToggle(string text, int y)
        {
            UiToggle t = new UiToggle();
            t.Text = text;
            t.Location = new Point(PADX, y);
            t.Size = new Size(W - PADX * 2, 22);
            Controls.Add(t);
            return t;
        }

        // ---- chrome --------------------------------------------------------

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;

            // title bar
            Theme.DrawText(g, "Keystrokes", Theme.Mono(13f, true), Theme.Text, PADX, 15f);
            float titleW = Theme.MeasureText(g, "Keystrokes", Theme.Mono(13f, true));
            Theme.DrawText(g, "WASD · LMB · RMB · CPS", Theme.Mono(10f, false), Theme.Faint, PADX + titleW + 10f, 18f);
            Theme.DrawTextMid(g, "✕", Theme.Mono(12f, false), _closeHover ? Theme.CloseHover : Theme.Faint,
                W - PADX - 10f, TITLE_H / 2f);
            using (Pen p = new Pen(Theme.Divider)) g.DrawLine(p, 0, TITLE_H, W, TITLE_H);

            // groups
            Theme.DrawText(g, "Appearance", Theme.Mono(11f, true), Theme.Section, PADX, _yAppearance);
            Theme.DrawText(g, "Counters", Theme.Mono(11f, true), Theme.Section, PADX, _yCounters);

            SliderRow(g, "Scale", _yScale, _scale.Value.ToString(CultureInfo.InvariantCulture) + "%");
            SliderRow(g, "Opacity", _yOpacity, _opacity.Value.ToString(CultureInfo.InvariantCulture) + "%");
            SliderRow(g, "Contrast", _yContrast, _contrast.Value.ToString(CultureInfo.InvariantCulture) + "%");

            Theme.DrawTextMid(g, "Color", Theme.Mono(10f, false), Theme.Label, PADX, _yColor + 12f);
            Theme.DrawTextMid(g, "CPS window", Theme.Mono(10f, false), Theme.Label, PADX, _yCpsWindow + 13f);

            using (Pen p = new Pen(Theme.Divider)) g.DrawLine(p, PADX, _yDivider, W - PADX, _yDivider);

            // footer
            using (Pen p = new Pen(Theme.Divider)) g.DrawLine(p, 0, _yFooter, W, _yFooter);
            string hint = "F8 — settings · F9 — move";
            Font hf = Theme.Mono(10f, false);
            float hw = Theme.MeasureText(g, hint, hf);
            Theme.DrawTextMid(g, hint, hf, Theme.Ghost, W - PADX - hw, _yFooter + 20f);

            using (GraphicsPath p = Theme.Round(new RectangleF(0.5f, 0.5f, W - 1f, ClientSize.Height - 1f), 12f))
            using (Pen pen = new Pen(Theme.Border, 1f))
                g.DrawPath(pen, p);
        }

        private void SliderRow(Graphics g, string label, int y, string value)
        {
            Theme.DrawTextMid(g, label, Theme.Mono(10f, false), Theme.Label, PADX, y + 10f);
            Font vf = Theme.Mono(10f, false);
            float vw = Theme.MeasureText(g, value, vf);
            Theme.DrawTextMid(g, value, vf, Theme.Text, W - PADX - vw, y + 10f);
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Y >= TITLE_H) return;
            if (e.X > W - 38) { Close(); return; }
            Native.ReleaseCapture();
            Native.SendMessage(Handle, Native.WM_NCLBUTTONDOWN, new IntPtr(Native.HTCAPTION), IntPtr.Zero);
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            bool hover = e.Y < TITLE_H && e.X > W - 38;
            if (hover != _closeHover) { _closeHover = hover; Invalidate(new Rectangle(W - 40, 0, 40, TITLE_H)); }
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (e.KeyCode == Keys.Escape) Close();
        }

        // ---- values --------------------------------------------------------

        private Color Accent()
        {
            return Renderer.ParseHex(_cfg.Accent, Color.FromArgb(0xE4, 0x55, 0xE0));
        }

        private RenderModel BuildPreviewModel()
        {
            RenderModel m = new RenderModel();
            for (int i = 0; i < 6; i++) m.Down[i] = InputTracker.IsDown(i);
            int l, r;
            InputTracker.GetCps(_cfg.CpsWindowMs, out l, out r);
            m.LeftCps = l;
            m.RightCps = r;
            m.LeftTotal = InputTracker.TotalLeft;
            m.RightTotal = InputTracker.TotalRight;
            m.ShowCps = _cfg.ShowCps;
            m.ShowCounters = _cfg.ShowCounters;
            m.Scale = _cfg.Scale / 100f * 0.9f; // preview renders at 90 %
            m.Backdrop = _cfg.TileBackdrop / 100f;
            m.Accent = Accent();
            return m;
        }

        private void LoadValues()
        {
            _loading = true;
            _scale.Value = Config.Clamp(_cfg.Scale, 60, 200);
            _opacity.Value = Config.Clamp(_cfg.Opacity, 30, 100);
            _contrast.Value = Config.Clamp(_cfg.TileBackdrop, 0, 100);
            _cpsWindow.SetIndexSilently(WindowIndex(_cfg.CpsWindowMs));
            _showCps.SetCheckedSilently(_cfg.ShowCps);
            _showTotals.SetCheckedSilently(_cfg.ShowCounters);
            _autoStart.SetCheckedSilently(_cfg.AutoStart);
            _loading = false;
            RefreshAccent();
        }

        private static int WindowIndex(int ms)
        {
            int best = 1;
            int bestDiff = int.MaxValue;
            for (int i = 0; i < CpsWindows.Length; i++)
            {
                int d = Math.Abs(CpsWindows[i] - ms);
                if (d < bestDiff) { bestDiff = d; best = i; }
            }
            return best;
        }

        /// <summary>Pushes the accent into every control that tints itself with it.</summary>
        private void RefreshAccent()
        {
            Color accent = Accent();
            foreach (Control c in Controls)
            {
                IAccentAware aware = c as IAccentAware;
                if (aware != null) aware.Accent = accent;
            }

            bool matchedPreset = false;
            foreach (UiSwatch sw in _swatches)
            {
                bool sel = string.Equals((string)sw.Tag, _cfg.Accent, StringComparison.OrdinalIgnoreCase);
                sw.Selected = sel;
                matchedPreset |= sel;
                sw.Invalidate();
            }

            string recent = _cfg.RecentAccent;
            bool recentIsPreset = false;
            foreach (string p in Presets)
                if (string.Equals(p, recent, StringComparison.OrdinalIgnoreCase)) recentIsPreset = true;

            if (!string.IsNullOrEmpty(recent) && !recentIsPreset)
            {
                _recent.Visible = true;
                _recent.Value = Renderer.ParseHex(recent, accent);
                _recent.Tag = recent;
                _recent.Selected = !matchedPreset && string.Equals(recent, _cfg.Accent, StringComparison.OrdinalIgnoreCase);
                _recent.Invalidate();
                _add.Location = new Point(PADX + LABEL_W + 12 + (Presets.Length + 1) * 30, _yColor);
            }
            else
            {
                _recent.Visible = false;
                _add.Location = new Point(PADX + LABEL_W + 12 + Presets.Length * 30, _yColor);
            }
            Invalidate();
        }

        private void Apply()
        {
            _cfg.Save();
            _overlay.ApplyConfig();
            _preview.Invalidate();
            Invalidate();
        }

        private void OnPresetClick(object sender, EventArgs e)
        {
            _cfg.Accent = (string)((Control)sender).Tag;
            RefreshAccent();
            Apply();
        }

        private void OnRecentClick(object sender, EventArgs e)
        {
            object tag = ((Control)sender).Tag;
            if (tag == null) return;
            _cfg.Accent = (string)tag;
            RefreshAccent();
            Apply();
        }

        private void OnCustomColor(object sender, EventArgs e)
        {
            string previous = _cfg.Accent;
            using (DimForm dim = new DimForm(this))
            using (ColorPickerForm dlg = new ColorPickerForm(Accent()))
            {
                dim.Show(this);
                dlg.ColorPreview += OnPickerPreview;
                DialogResult r = dlg.ShowDialog(this);
                dlg.ColorPreview -= OnPickerPreview;
                dim.Hide();

                if (r == DialogResult.OK)
                {
                    _cfg.Accent = Renderer.ToHex(dlg.Result);
                    _cfg.RecentAccent = _cfg.Accent;
                }
                else
                {
                    _cfg.Accent = previous; // cancel restores the previous value
                }
            }
            RefreshAccent();
            Apply();
        }

        /// <summary>Live-preview a colour in the real overlay while the picker is being dragged.</summary>
        private void OnPickerPreview(object sender, ColorEventArgs e)
        {
            _cfg.Accent = Renderer.ToHex(e.Color);
            _overlay.ApplyConfig();
            _preview.Invalidate();
        }

        private void OnScaleChanged(object sender, EventArgs e)
        {
            if (_loading) return;
            _cfg.Scale = _scale.Value;
            Apply();
        }

        private void OnOpacityChanged(object sender, EventArgs e)
        {
            if (_loading) return;
            _cfg.Opacity = _opacity.Value;
            Apply();
        }

        private void OnContrastChanged(object sender, EventArgs e)
        {
            if (_loading) return;
            _cfg.TileBackdrop = _contrast.Value;
            Apply();
        }

        private void OnCpsWindowChanged(object sender, EventArgs e)
        {
            if (_loading) return;
            _cfg.CpsWindowMs = CpsWindows[_cpsWindow.SelectedIndex];
            Apply();
        }

        private void OnShowCpsChanged(object sender, EventArgs e)
        {
            if (_loading) return;
            _cfg.ShowCps = _showCps.Checked;
            Apply();
        }

        private void OnShowTotalsChanged(object sender, EventArgs e)
        {
            if (_loading) return;
            _cfg.ShowCounters = _showTotals.Checked;
            Apply();
        }

        private void OnAutoStartChanged(object sender, EventArgs e)
        {
            if (_loading) return;
            _cfg.AutoStart = _autoStart.Checked;
            try
            {
                SetAutoStart(_cfg.AutoStart);
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, "Could not change the startup entry: " + ex.Message, "Keystrokes Overlay",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            Apply();
        }

        internal static void SetAutoStart(bool on)
        {
            const string keyPath = @"Software\Microsoft\Windows\CurrentVersion\Run";
            const string valueName = "KeystrokesOverlay";
            using (RegistryKey key = Registry.CurrentUser.OpenSubKey(keyPath, true))
            {
                if (key == null) return;
                if (on)
                {
                    string exe = System.Reflection.Assembly.GetExecutingAssembly().Location;
                    key.SetValue(valueName, "\"" + exe + "\"");
                }
                else if (key.GetValue(valueName) != null)
                {
                    key.DeleteValue(valueName, false);
                }
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            _tick.Stop();
            _cfg.Save();
            base.OnFormClosing(e);
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing) _tick.Dispose();
            base.Dispose(disposing);
        }
    }

    internal class ColorEventArgs : EventArgs
    {
        public readonly Color Color;
        public ColorEventArgs(Color c) { Color = c; }
    }

    /// <summary>Dim veil shown behind the modal colour picker.</summary>
    internal class DimForm : Form
    {
        public DimForm(Form owner)
        {
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.Manual;
            Bounds = owner.Bounds;
            BackColor = Color.Black;
            Opacity = 0.45;
            ShowInTaskbar = false;
            TopMost = owner.TopMost;
        }

        protected override bool ShowWithoutActivation { get { return true; } }
    }
}
