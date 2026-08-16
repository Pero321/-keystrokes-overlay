using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Windows.Forms;

namespace KeystrokesOverlay
{
    /// <summary>
    /// Per-pixel-alpha layered window that sits on top of the game and (outside of
    /// move mode) lets every click fall straight through to it.
    /// </summary>
    internal class OverlayForm : Form
    {
        public const int HOTKEY_MOVE = 1;
        public const int HOTKEY_SETTINGS = 2;

        private const string FIRST_RUN_HINT = "F8 — settings · F9 — move";
        private const int FIRST_RUN_SECONDS = 12;

        private readonly Config _cfg;
        private readonly Timer _timer;
        private string _lastSignature = "";
        private bool _moveMode;
        private int _tick;
        private int _hintTicksLeft;

        public event EventHandler MoveModeChanged;
        public event EventHandler SettingsRequested;

        public bool MoveMode { get { return _moveMode; } }

        public OverlayForm(Config cfg)
        {
            _cfg = cfg;
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.Manual;
            TopMost = true;
            Text = "Keystrokes Overlay";
            SetStyle(ControlStyles.Selectable, false);

            _timer = new Timer();
            _timer.Interval = 100; // CPS recalculation cadence
            _timer.Tick += OnTick;
        }

        protected override bool ShowWithoutActivation { get { return true; } }

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ExStyle |= Native.WS_EX_LAYERED | Native.WS_EX_TOOLWINDOW | Native.WS_EX_NOACTIVATE | Native.WS_EX_TOPMOST;
                if (!_moveMode) cp.ExStyle |= Native.WS_EX_TRANSPARENT;
                return cp;
            }
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            InputTracker.NotifyHwnd = Handle;
            // single-key hotkeys: F8/F9 never collide with typing or WASD
            Native.RegisterHotKey(Handle, HOTKEY_MOVE, Native.MOD_NOREPEAT, (uint)Keys.F9);
            Native.RegisterHotKey(Handle, HOTKEY_SETTINGS, Native.MOD_NOREPEAT, (uint)Keys.F8);
            ApplyClickThrough();
            RestorePosition();
            _timer.Start();
            Redraw(true);
        }

        protected override void OnHandleDestroyed(EventArgs e)
        {
            Native.UnregisterHotKey(Handle, HOTKEY_MOVE);
            Native.UnregisterHotKey(Handle, HOTKEY_SETTINGS);
            InputTracker.NotifyHwnd = IntPtr.Zero;
            base.OnHandleDestroyed(e);
        }

        /// <summary>On the very first run the overlay itself explains which keys open what.</summary>
        public void ShowFirstRunHint()
        {
            _hintTicksLeft = FIRST_RUN_SECONDS * 10; // the timer ticks every 100 ms
            Redraw(true);
        }

        private void OnTick(object sender, EventArgs e)
        {
            if (_hintTicksLeft > 0)
            {
                _hintTicksLeft--;
                if (_hintTicksLeft == 0)
                {
                    _cfg.HintShown = true;
                    _cfg.Save();
                }
            }
            Redraw(false);
            _tick++;
            if (_tick % 10 == 0 && Visible) ReassertTopMost();
        }

        private void ReassertTopMost()
        {
            Native.SetWindowPos(Handle, Native.HWND_TOPMOST, 0, 0, 0, 0,
                Native.SWP_NOMOVE | Native.SWP_NOSIZE | Native.SWP_NOACTIVATE);
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == Native.WM_APP_REDRAW)
            {
                Redraw(false); // key state changed — repaint right now, no timer wait
                return;
            }
            if (m.Msg == Native.WM_HOTKEY)
            {
                int id = m.WParam.ToInt32();
                if (id == HOTKEY_MOVE) ToggleMoveMode();
                else if (id == HOTKEY_SETTINGS && SettingsRequested != null) SettingsRequested(this, EventArgs.Empty);
                return;
            }
            if (m.Msg == Native.WM_NCHITTEST && _moveMode)
            {
                m.Result = new IntPtr(Native.HTCAPTION); // drag anywhere on the widget
                return;
            }
            if (m.Msg == Native.WM_EXITSIZEMOVE)
            {
                SavePosition();
                return;
            }
            base.WndProc(ref m);
        }

        // ---- state ---------------------------------------------------------

        public void ToggleMoveMode()
        {
            SetMoveMode(!_moveMode);
        }

        public void SetMoveMode(bool on)
        {
            if (_moveMode == on) return;
            _moveMode = on;
            if (on && !Visible) ShowOverlay(true);
            ApplyClickThrough();
            if (!on) SavePosition();
            Redraw(true);
            if (MoveModeChanged != null) MoveModeChanged(this, EventArgs.Empty);
        }

        private void ApplyClickThrough()
        {
            if (!IsHandleCreated) return;
            int ex = Native.GetWindowLong(Handle, Native.GWL_EXSTYLE);
            if (_moveMode) ex &= ~Native.WS_EX_TRANSPARENT;
            else ex |= Native.WS_EX_TRANSPARENT;
            Native.SetWindowLong(Handle, Native.GWL_EXSTYLE, ex);
        }

        public void ShowOverlay(bool visible)
        {
            _cfg.Visible = visible;
            if (visible)
            {
                if (!Visible) Show();
                ReassertTopMost();
                Redraw(true);
            }
            else
            {
                if (_moveMode) SetMoveMode(false);
                Hide();
            }
            _cfg.Save();
        }

        public void ApplyConfig()
        {
            Redraw(true);
        }

        // ---- position ------------------------------------------------------

        private void RestorePosition()
        {
            Rectangle screen = Screen.PrimaryScreen.WorkingArea;
            int x = _cfg.PosX, y = _cfg.PosY;
            if (x == int.MinValue || y == int.MinValue)
            {
                x = screen.Left + 60;
                y = screen.Top + screen.Height / 2 - Height / 2;
            }
            Rectangle virt = SystemInformation.VirtualScreen;
            if (x < virt.Left - 200) x = virt.Left;
            if (y < virt.Top - 200) y = virt.Top;
            if (x > virt.Right - 40) x = virt.Right - 200;
            if (y > virt.Bottom - 40) y = virt.Bottom - 200;
            Location = new Point(x, y);
        }

        private void SavePosition()
        {
            _cfg.PosX = Location.X;
            _cfg.PosY = Location.Y;
            _cfg.Save();
        }

        public void ResetPosition()
        {
            _cfg.PosX = int.MinValue;
            _cfg.PosY = int.MinValue;
            RestorePosition();
            SavePosition();
        }

        // ---- painting ------------------------------------------------------

        private void Redraw(bool force)
        {
            if (!IsHandleCreated || (!Visible && !force)) return;

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
            m.Scale = _cfg.Scale / 100f;
            m.Backdrop = Config.Clamp(_cfg.TileBackdrop, 0, 100) / 100f;
            m.Accent = Renderer.ParseHex(_cfg.Accent, Color.FromArgb(0xE4, 0x55, 0xE0));
            m.MoveMode = _moveMode;
            m.Hint = _hintTicksLeft > 0 && !_moveMode ? FIRST_RUN_HINT : null;

            string sig = m.Signature();
            if (!force && sig == _lastSignature) return;
            _lastSignature = sig;

            using (Bitmap bmp = Renderer.Render(m))
            {
                SetBitmap(bmp, (byte)(255 * Config.Clamp(_cfg.Opacity, 30, 100) / 100));
            }
        }

        private void SetBitmap(Bitmap bitmap, byte opacity)
        {
            if (bitmap.PixelFormat != PixelFormat.Format32bppArgb) return;

            IntPtr screenDc = Native.GetDC(IntPtr.Zero);
            IntPtr memDc = Native.CreateCompatibleDC(screenDc);
            IntPtr hBitmap = IntPtr.Zero;
            IntPtr oldBitmap = IntPtr.Zero;
            try
            {
                if (Size != bitmap.Size) Size = bitmap.Size; // keep the managed bounds in sync first
                // GDI wants premultiplied alpha for ULW_ALPHA
                hBitmap = bitmap.GetHbitmap(Color.FromArgb(0));
                oldBitmap = Native.SelectObject(memDc, hBitmap);

                Native.SIZE size = new Native.SIZE(bitmap.Width, bitmap.Height);
                Native.POINT src = new Native.POINT(0, 0);
                Native.POINT dst = new Native.POINT(Left, Top);
                Native.BLENDFUNCTION blend = new Native.BLENDFUNCTION();
                blend.BlendOp = Native.AC_SRC_OVER;
                blend.BlendFlags = 0;
                blend.SourceConstantAlpha = opacity;
                blend.AlphaFormat = Native.AC_SRC_ALPHA;

                Native.UpdateLayeredWindow(Handle, screenDc, ref dst, ref size, memDc, ref src, 0, ref blend, Native.ULW_ALPHA);
            }
            finally
            {
                Native.ReleaseDC(IntPtr.Zero, screenDc);
                if (hBitmap != IntPtr.Zero)
                {
                    Native.SelectObject(memDc, oldBitmap);
                    Native.DeleteObject(hBitmap);
                }
                Native.DeleteDC(memDc);
            }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing && _timer != null) _timer.Dispose();
            base.Dispose(disposing);
        }
    }
}
