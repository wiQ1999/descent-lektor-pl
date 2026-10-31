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
