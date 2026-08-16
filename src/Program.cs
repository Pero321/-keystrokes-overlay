using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

namespace KeystrokesOverlay
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            bool created;
            using (Mutex mutex = new Mutex(true, "KeystrokesOverlay.SingleInstance", out created))
            {
                if (!created)
                {
                    MessageBox.Show("Keystrokes Overlay is already running — see the tray icon.", "Keystrokes Overlay",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }

                try { Native.SetProcessDPIAware(); }
                catch { }

                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new TrayContext());
            }
        }
    }

    internal class TrayContext : ApplicationContext
    {
        private readonly Config _cfg;
        private readonly OverlayForm _overlay;
        private readonly NotifyIcon _tray;
        private readonly MenuItem _showItem;
        private readonly MenuItem _moveItem;
        private SettingsForm _settings;

        public TrayContext()
        {
            _cfg = Config.Load();
            _cfg.Save(); // materialise config.json next to the exe on first run

            // keep the Run entry pointing at wherever the exe lives now
            if (_cfg.AutoStart)
            {
                try { SettingsForm.SetAutoStart(true); }
                catch { }
            }

            InputTracker.Start();

            _overlay = new OverlayForm(_cfg);
            _overlay.SettingsRequested += delegate { OpenSettings(); };
            _overlay.MoveModeChanged += delegate { _moveItem.Checked = _overlay.MoveMode; };

            _showItem = new MenuItem("Show overlay", OnToggleShow);
            _showItem.Checked = _cfg.Visible;
            _moveItem = new MenuItem("Move mode (F9)", delegate { _overlay.ToggleMoveMode(); });

            ContextMenu menu = new ContextMenu(new MenuItem[]
            {
                _showItem,
                _moveItem,
                new MenuItem("Settings… (F8)", delegate { OpenSettings(); }),
                new MenuItem("Reset counters", delegate { InputTracker.ResetCounters(); _overlay.ApplyConfig(); }),
                new MenuItem("-"),
                new MenuItem("Quit", delegate { ExitApp(); })
            });

            _tray = new NotifyIcon();
            _tray.Icon = LoadIcon();
            _tray.Text = "Keystrokes Overlay";
            _tray.ContextMenu = menu;
            _tray.DoubleClick += delegate { OpenSettings(); };
            _tray.Visible = true;

            _overlay.Show();
            if (!_cfg.Visible) _overlay.ShowOverlay(false);

            if (!_cfg.HintShown)
            {
                // first launch: say which keys do what, both on the overlay and from the tray
                _overlay.ShowFirstRunHint();
                try
                {
                    _tray.BalloonTipTitle = "Keystrokes Overlay is running";
                    _tray.BalloonTipText = "F8 — settings · F9 — move the overlay. Right-click this icon for the menu.";
                    _tray.BalloonTipIcon = ToolTipIcon.Info;
                    _tray.ShowBalloonTip(10000);
                }
                catch { }
            }
        }

        private static Icon LoadIcon()
        {
            try
            {
                using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream("app.ico"))
                {
                    if (s != null) return new Icon(s);
                }
            }
            catch { }
            return SystemIcons.Application;
        }

        private void OnToggleShow(object sender, EventArgs e)
        {
            bool show = !_showItem.Checked;
            _showItem.Checked = show;
            _overlay.ShowOverlay(show);
        }

        private void OpenSettings()
        {
            if (_settings != null && !_settings.IsDisposed)
            {
                _settings.Activate();
                return;
            }
            _settings = new SettingsForm(_cfg, _overlay);
            _settings.FormClosed += delegate { _settings = null; };
            // opened by hotkey from inside a game: without TopMost it would land behind it
            _settings.TopMost = true;
            _settings.Show();
            _settings.Activate();
            _settings.BringToFront();
        }

        private void ExitApp()
        {
            _tray.Visible = false;
            _tray.Dispose();
            InputTracker.Stop();
            if (_settings != null && !_settings.IsDisposed) _settings.Close();
            _overlay.Close();
            ExitThread();
        }
    }
}
