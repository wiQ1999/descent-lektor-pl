using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;

namespace LektorPL.Core
{
    /// <summary>
    /// Uruchamia companion razem z grą (D59). Companion sam kończy się po zamknięciu gry (--parent-pid),
    /// więc plugin niczego nie zamyka przy wyjściu (D40).
    /// </summary>
    internal static class Launcher
    {
        /// <summary>Zwraca stan do dziennika: dziala, uruchomiony, brak_pliku albo blad.</summary>
        public static string EnsureRunning(Options o, out string detail)
        {
            detail = null;
            if (PortBusy(o.CompanionPort))
                return "dziala";
            if (!File.Exists(o.CompanionExe))
            {
                detail = o.CompanionExe;
                return "brak_pliku";
            }
            try
            {
                var psi = new ProcessStartInfo(o.CompanionExe, o.CompanionArgs)
                {
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = o.CompanionWorkDir ?? Path.GetDirectoryName(o.CompanionExe),
                };
                // Bez zmiennych loadera: na Macu DYLD_INSERT_LIBRARIES wstrzyknąłby Doorstop (i overlay Steama) także do Pythona.
                var drop = new List<string>();
                foreach (string key in psi.Environment.Keys)
                    if (key.StartsWith("DOORSTOP_", StringComparison.OrdinalIgnoreCase) || key.StartsWith("DYLD_", StringComparison.OrdinalIgnoreCase))
                        drop.Add(key);
                foreach (string key in drop)
                    psi.Environment.Remove(key);
                using (Process.Start(psi)) { }
                return "uruchomiony";
            }
            catch (Exception e)
            {
                detail = e.GetType().Name + ": " + e.Message;
                return "blad";
            }
        }

        /// <summary>Port zajęty oznacza działający companion (on sam też nie startuje drugi raz).</summary>
        private static bool PortBusy(int port)
        {
            var probe = new TcpListener(IPAddress.Loopback, port);
            try
            {
                probe.Start();
                return false;
            }
            catch (SocketException)
            {
                return true;
            }
            finally
            {
                try { probe.Stop(); } catch (Exception) { }
            }
        }
    }
}
