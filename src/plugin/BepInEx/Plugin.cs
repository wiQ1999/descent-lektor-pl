using System;
using BepInEx;
using BepInEx.Configuration;
using LektorPL.Core;

namespace LektorPL.BepInEx
{
    [BepInPlugin("pl.lektor.descent", "Lektor PL", Bootstrap.Version)]
    public sealed class Plugin : BaseUnityPlugin
    {
        private void Awake()
        {
            try
            {
                var options = new Options();
                options.LogDirectory = Config.Bind("Log", "Directory", options.LogDirectory,
                    "Katalog dzienników JSONL.").Value;
                options.SniffText = Config.Bind("Log", "SniffText", options.SniffText,
                    "Zapisuj nowe teksty widocznych pól TextMeshPro (pomiar pokrycia).").Value;
                options.SniffInterval = Config.Bind("Log", "SniffInterval", options.SniffInterval,
                    "Co ile sekund przeglądać pola TextMeshPro.").Value;
                options.CompanionPort = Config.Bind("Companion", "Port", options.CompanionPort,
                    "Port companiona na localhost; 0 wyłącza wysyłkę zdarzeń.").Value;
                options.DiagnosticStage = Config.Bind("Diagnostics", "Stage", options.DiagnosticStage,
                    "Diagnoza crasha przy wyjściu (D40): 0 nic, 1 pusty Runner, 2 + dziennik, 3 + Tracker, 4 całość.").Value;
                options.Info = s => Logger.LogInfo(s);
                Bootstrap.Start(options);
            }
            catch (Exception e)
            {
                Logger.LogError("Lektor PL nie wystartował: " + e);
            }
        }
    }
}
