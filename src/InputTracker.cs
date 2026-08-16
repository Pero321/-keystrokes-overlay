using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

namespace KeystrokesOverlay
{
    /// <summary>
    /// Global low-level keyboard/mouse hooks running on their own thread with its
    /// own message pump, so overlay repainting can never stall the input chain.
    /// </summary>
    internal static class InputTracker
    {
        public const int K_W = 0, K_A = 1, K_S = 2, K_D = 3, K_LMB = 4, K_RMB = 5;

        // scan codes — layout independent (works on any keyboard layout)
        private const uint SC_W = 0x11, SC_A = 0x1E, SC_S = 0x1F, SC_D = 0x20;
        private const uint VK_W = 0x57, VK_A = 0x41, VK_S = 0x53, VK_D = 0x44;
        private const uint LLKHF_EXTENDED = 0x01;

        private static readonly bool[] _down = new bool[6];
        private static readonly List<long> _lClicks = new List<long>(64);
        private static readonly List<long> _rClicks = new List<long>(64);
        private static readonly object _sync = new object();
        private static readonly Stopwatch _clock = Stopwatch.StartNew();

        private static long _totalL, _totalR;

        private static IntPtr _kbHook, _msHook;
        private static Native.HookProc _kbProc, _msProc; // kept alive against the GC
        private static Thread _thread;
        private static uint _threadId;

        public static IntPtr NotifyHwnd = IntPtr.Zero;

        public static bool IsDown(int key) { return _down[key]; }
        public static long TotalLeft { get { return Interlocked.Read(ref _totalL); } }
        public static long TotalRight { get { return Interlocked.Read(ref _totalR); } }

        public static void Start()
        {
            if (_thread != null) return;
            _thread = new Thread(HookLoop);
            _thread.IsBackground = true;
            _thread.Name = "input-hooks";
            _thread.Priority = ThreadPriority.AboveNormal;
            _thread.Start();
        }

        public static void Stop()
        {
            if (_thread == null) return;
            Native.PostThreadMessage(_threadId, Native.WM_QUIT, IntPtr.Zero, IntPtr.Zero);
            _thread.Join(1000);
            _thread = null;
        }

        private static void HookLoop()
        {
            _threadId = Native.GetCurrentThreadId();
            _kbProc = KeyboardProc;
            _msProc = MouseProc;
            IntPtr hMod = Native.GetModuleHandle(null);
            _kbHook = Native.SetWindowsHookEx(Native.WH_KEYBOARD_LL, _kbProc, hMod, 0);
            _msHook = Native.SetWindowsHookEx(Native.WH_MOUSE_LL, _msProc, hMod, 0);

            Native.MSG msg;
            while (Native.GetMessage(out msg, IntPtr.Zero, 0, 0) > 0)
            {
                Native.TranslateMessage(ref msg);
                Native.DispatchMessage(ref msg);
            }

            if (_kbHook != IntPtr.Zero) Native.UnhookWindowsHookEx(_kbHook);
            if (_msHook != IntPtr.Zero) Native.UnhookWindowsHookEx(_msHook);
            _kbHook = IntPtr.Zero;
            _msHook = IntPtr.Zero;
        }

        private static IntPtr KeyboardProc(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0)
            {
                Native.KBDLLHOOKSTRUCT d = (Native.KBDLLHOOKSTRUCT)
                    System.Runtime.InteropServices.Marshal.PtrToStructure(lParam, typeof(Native.KBDLLHOOKSTRUCT));
                int idx = MapKey(d);
                if (idx >= 0)
                {
                    int m = wParam.ToInt32();
                    if (m == Native.WM_KEYDOWN || m == Native.WM_SYSKEYDOWN) SetState(idx, true);
                    else if (m == Native.WM_KEYUP || m == Native.WM_SYSKEYUP) SetState(idx, false);
                }
            }
            return Native.CallNextHookEx(IntPtr.Zero, nCode, wParam, lParam);
        }

        private static int MapKey(Native.KBDLLHOOKSTRUCT d)
        {
            if ((d.flags & LLKHF_EXTENDED) == 0)
            {
                switch (d.scanCode)
                {
                    case SC_W: return K_W;
                    case SC_A: return K_A;
                    case SC_S: return K_S;
                    case SC_D: return K_D;
                }
            }
            // synthetic events sometimes carry no scan code
            if (d.scanCode == 0)
            {
                switch (d.vkCode)
                {
                    case VK_W: return K_W;
                    case VK_A: return K_A;
                    case VK_S: return K_S;
                    case VK_D: return K_D;
                }
            }
            return -1;
        }

        private static IntPtr MouseProc(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0)
            {
                int m = wParam.ToInt32();
                switch (m)
                {
                    case Native.WM_LBUTTONDOWN:
                        RecordClick(_lClicks, ref _totalL);
                        SetState(K_LMB, true);
                        break;
                    case Native.WM_LBUTTONUP:
                        SetState(K_LMB, false);
                        break;
                    case Native.WM_RBUTTONDOWN:
                        RecordClick(_rClicks, ref _totalR);
                        SetState(K_RMB, true);
                        break;
                    case Native.WM_RBUTTONUP:
                        SetState(K_RMB, false);
                        break;
                }
            }
            return Native.CallNextHookEx(IntPtr.Zero, nCode, wParam, lParam);
        }

        private static void RecordClick(List<long> bucket, ref long total)
        {
            long now = _clock.ElapsedMilliseconds;
            lock (_sync)
            {
                bucket.Add(now);
                if (bucket.Count > 512) bucket.RemoveRange(0, 256);
            }
            Interlocked.Increment(ref total);
        }

        private static void SetState(int idx, bool value)
        {
            if (_down[idx] == value) return; // ignore auto-repeat
            _down[idx] = value;
            IntPtr h = NotifyHwnd;
            if (h != IntPtr.Zero) Native.PostMessage(h, Native.WM_APP_REDRAW, IntPtr.Zero, IntPtr.Zero);
        }

        /// <summary>Clicks within the last <paramref name="windowMs"/> milliseconds.</summary>
        public static void GetCps(int windowMs, out int left, out int right)
        {
            long cutoff = _clock.ElapsedMilliseconds - windowMs;
            lock (_sync)
            {
                left = CountFrom(_lClicks, cutoff);
                right = CountFrom(_rClicks, cutoff);
            }
        }

        private static int CountFrom(List<long> bucket, long cutoff)
        {
            int n = 0;
            for (int i = bucket.Count - 1; i >= 0; i--)
            {
                if (bucket[i] >= cutoff) n++;
                else break;
            }
            // drop entries that can never count again
            if (bucket.Count - n > 128) bucket.RemoveRange(0, bucket.Count - n);
            return n;
        }

        public static void ResetCounters()
        {
            lock (_sync)
            {
                _lClicks.Clear();
                _rClicks.Clear();
            }
            Interlocked.Exchange(ref _totalL, 0);
            Interlocked.Exchange(ref _totalR, 0);
        }
    }
}
