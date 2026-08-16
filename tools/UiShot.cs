using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Windows.Forms;

namespace KeystrokesOverlay
{
    /// <summary>Dev helper: renders the colour picker to PNG so its layout can be reviewed.</summary>
    internal static class UiShot
    {
        [STAThread]
        private static void Main(string[] args)
        {
            string dir = args.Length > 0 ? args[0] : ".";
            Directory.CreateDirectory(dir);
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            using (ColorPickerForm f = new ColorPickerForm(Color.FromArgb(0x5E, 0xE6, 0xA8)))
            {
                f.StartPosition = FormStartPosition.Manual;
                f.Location = new Point(80, 80);
                f.Show();
                for (int i = 0; i < 20; i++) { Application.DoEvents(); System.Threading.Thread.Sleep(30); }
                using (Bitmap bmp = new Bitmap(f.Width, f.Height))
                {
                    f.DrawToBitmap(bmp, new Rectangle(0, 0, f.Width, f.Height));
                    bmp.Save(Path.Combine(dir, "ui-colorpicker.png"), ImageFormat.Png);
                }
            }
            Console.WriteLine("ok");
        }
    }
}
