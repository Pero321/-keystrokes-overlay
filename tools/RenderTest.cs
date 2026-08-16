using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;

namespace KeystrokesOverlay
{
    /// <summary>Dev helper: renders sample frames to PNG so the visuals can be eyeballed.</summary>
    internal static class RenderTest
    {
        [STAThread]
        private static void Main(string[] args)
        {
            string dir = args.Length > 0 ? args[0] : ".";
            Directory.CreateDirectory(dir);

            Save(dir, "idle.png", Model(false, false, false, false, false, false, 0, 0, true, false, 1f));
            Save(dir, "pressed.png", Model(true, false, true, false, true, false, 7, 2, true, false, 1f));
            Save(dir, "all.png", Model(true, true, true, true, true, true, 12, 9, true, true, 1f));
            Save(dir, "scaled150.png", Model(true, false, false, true, false, true, 5, 3, true, false, 1.5f));
            Save(dir, "move.png", MoveModel());
            SaveContrast(dir, "contrast-0.png", 0f);
            SaveContrast(dir, "contrast-55.png", 0.55f);
            SaveContrast(dir, "contrast-100.png", 1f);

            Benchmark();
            Console.WriteLine("ok");
        }

        private static void Benchmark()
        {
            RenderModel noBd = Model(false, false, false, false, false, false, 0, 0, true, false, 1f);
            noBd.Backdrop = 0f;
            Bench("idle, 100 %, backdrop 0", noBd);
            Bench("idle, 100 %", Model(false, false, false, false, false, false, 0, 0, true, false, 1f));
            Bench("all pressed, 100 %", Model(true, true, true, true, true, true, 15, 12, true, true, 1f));
            Bench("all pressed, 200 %", Model(true, true, true, true, true, true, 15, 12, true, true, 2f));
        }

        private static void Bench(string label, RenderModel m)
        {
            using (Bitmap warm = Renderer.Render(m)) { }
            System.Diagnostics.Stopwatch sw = System.Diagnostics.Stopwatch.StartNew();
            const int n = 300;
            for (int i = 0; i < n; i++) using (Bitmap b = Renderer.Render(m)) { }
            sw.Stop();
            Console.WriteLine("render (" + label + "): " + (sw.Elapsed.TotalMilliseconds / n).ToString("0.00") + " ms/frame");
        }

        private static RenderModel Model(bool w, bool a, bool s, bool d, bool l, bool r, int lc, int rc,
            bool showCps, bool showCounters, float scale)
        {
            RenderModel m = new RenderModel();
            m.Down[InputTracker.K_W] = w;
            m.Down[InputTracker.K_A] = a;
            m.Down[InputTracker.K_S] = s;
            m.Down[InputTracker.K_D] = d;
            m.Down[InputTracker.K_LMB] = l;
            m.Down[InputTracker.K_RMB] = r;
            m.LeftCps = lc;
            m.RightCps = rc;
            m.LeftTotal = 1234;
            m.RightTotal = 87;
            m.ShowCps = showCps;
            m.ShowCounters = showCounters;
            m.Scale = scale;
            return m;
        }

        private static RenderModel MoveModel()
        {
            RenderModel m = Model(false, false, false, false, false, false, 0, 0, true, false, 1f);
            m.MoveMode = true;
            return m;
        }

        /// <summary>The same frame over a bright scene and a dark one, at a given backdrop strength.</summary>
        private static void SaveContrast(string dir, string name, float backdrop)
        {
            RenderModel m = Model(true, false, false, false, true, false, 6, 1, true, false, 1f);
            m.Backdrop = backdrop;
            using (Bitmap bmp = Renderer.Render(m))
            {
                int pad = 20;
                using (Bitmap canvas = new Bitmap(bmp.Width * 2 + pad * 3, bmp.Height + pad * 2, PixelFormat.Format32bppArgb))
                using (Graphics g = Graphics.FromImage(canvas))
                {
                    // bright snow-ish scene | dark cave-ish scene
                    using (SolidBrush b = new SolidBrush(Color.FromArgb(255, 0xEE, 0xF3, 0xF8)))
                        g.FillRectangle(b, 0, 0, canvas.Width / 2, canvas.Height);
                    using (SolidBrush b = new SolidBrush(Color.FromArgb(255, 0x1B, 0x23, 0x18)))
                        g.FillRectangle(b, canvas.Width / 2, 0, canvas.Width / 2, canvas.Height);
                    g.DrawImage(bmp, pad, pad);
                    g.DrawImage(bmp, canvas.Width / 2 + pad / 2, pad);
                    canvas.Save(Path.Combine(dir, name), ImageFormat.Png);
                }
            }
        }

        private static void Save(string dir, string name, RenderModel m)
        {
            using (Bitmap bmp = Renderer.Render(m))
            using (Bitmap onGrass = OnBackdrop(bmp))
            {
                onGrass.Save(Path.Combine(dir, name), ImageFormat.Png);
            }
        }

        /// <summary>Composites the overlay over a game-ish backdrop, the way it will really be seen.</summary>
        private static Bitmap OnBackdrop(Bitmap overlay)
        {
            int pad = 24;
            Bitmap bg = new Bitmap(overlay.Width + pad * 2, overlay.Height + pad * 2, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(bg))
            {
                using (SolidBrush sky = new SolidBrush(Color.FromArgb(255, 0x8B, 0xB8, 0xD8)))
                    g.FillRectangle(sky, 0, 0, bg.Width, bg.Height);
                using (SolidBrush grass = new SolidBrush(Color.FromArgb(255, 0x4C, 0x7A, 0x36)))
                    g.FillRectangle(grass, 0, bg.Height / 2, bg.Width, bg.Height / 2);
                using (SolidBrush dark = new SolidBrush(Color.FromArgb(90, 0, 0, 0)))
                    g.FillRectangle(dark, 0, bg.Height * 3 / 4, bg.Width, bg.Height / 4);
                g.DrawImage(overlay, pad, pad);
            }
            return bg;
        }
    }
}
