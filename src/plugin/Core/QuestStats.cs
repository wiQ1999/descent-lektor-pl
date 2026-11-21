using System;
using System.Collections.Generic;
using FFG.D3;
using FFG.D3.Extension;
using UnityEngine;

namespace LektorPL.Core
{
    /// <summary>
    /// Statystyki misji do panelu podsumowania (E20, D114), wyłącznie z danych, które gra zapisuje sama:
    /// <c>SerializedGame.QuestSummary</c>, <c>ActivePlayers</c>, <c>GameDifficulty</c> i <c>FeatProgresses</c>.
    ///
    /// Liczymy raz, gdy gra pokazuje okno podsumowania. Ataki według klasy broni gra sumuje dla całej drużyny
    /// (<c>CoreWeaponClassUsage</c>, klasa z <c>PartA</c> broni, którą bohater atakował), więc klasę przypisujemy
    /// bohaterom, którzy na koniec misji mają w ekwipunku broń tej klasy; wspólna klasa ma wspólną liczbę.
    /// Ataki runą gra liczy osobno dla bohatera (<c>UniqueWeaponClassUsage</c>).
    /// Postęp wyzwań liczymy wzorem z <c>UIQuestSummary.SyncTo</c>.
    /// </summary>
    internal sealed class QuestStats
    {
        internal const int ActionInteract = 1, ActionCombat = 2;   // ActionIconType: Generic, Interact, Combat

        internal sealed class WeaponRow
        {
            public WeaponClasses Class;
            public string NameKey;                 // WEAPON_<KLASA>, jak w UIInventoryDialog
            public int Attacks;
            public readonly List<int> Heroes = new List<int>();   // indeksy w Heroes; pusta = nikt jej nie nosi na końcu
        }

        internal sealed class HeroRow
        {
            public int Index;
            public string HeroId, NameKey, PortraitPath;
            public Color ColorLight, ColorDark;
            public HeroHealth Health;
            public readonly List<WeaponClasses> Classes = new List<WeaponClasses>();
            public int Attacks;                    // suma klas bohatera (wspólne liczone w całości) + runa
            public int RuneAttacks;
            public WeaponClasses? Favorite;        // klasa z największą liczbą ataków
            public readonly List<int> SharedWith = new List<int>();   // bohaterowie ze wspólną klasą
            public int FeatsCompleted;
            public float FeatStart, FeatGained;    // pasek gry: część ułamkowa na starcie i przyrost w misji
        }

        public string QuestId;
        public float Seconds;
        public int Rounds, Gold, Interactions, CombatActions, Attacks;
        public DifficultySetting Difficulty;
        public int LootItems, LootMaterials, LootRecipes, LootConsumables;
        public readonly List<WeaponRow> Weapons = new List<WeaponRow>();    // tylko klasy z atakami, malejąco
        public readonly List<HeroRow> Heroes = new List<HeroRow>();

        public float SecondsPerRound { get { return Rounds > 0 ? Seconds / Rounds : 0f; } }
        public float GoldPerRound { get { return Rounds > 0 ? (float)Gold / Rounds : 0f; } }

        public static QuestStats Read(SerializedGame data, string questId)
        {
            var q = data != null ? data.QuestSummary : null;
            if (q == null) return null;
            var s = new QuestStats
            {
                QuestId = questId,
                Seconds = q.QuestTotalTime,
                Rounds = q.CurrentRound,
                Gold = q.ObtainedGold,
                Difficulty = data.GameDifficulty,
            };
            if (q.ActionsPerformed != null)
            {
                if (q.ActionsPerformed.Length > ActionInteract) s.Interactions = q.ActionsPerformed[ActionInteract];
                if (q.ActionsPerformed.Length > ActionCombat) s.CombatActions = q.ActionsPerformed[ActionCombat];
            }
            s.ReadHeroes(data, q);
            s.ReadWeapons(q);
            s.ReadLoot(q);
            s.ReadFeats(data, q);
            return s;
        }

        private void ReadHeroes(SerializedGame data, SerializedQuestSummary q)
        {
            var players = data.ActivePlayers;
            if (players == null) return;
            for (int i = 0; i < players.Count; i++)
            {
                var p = players[i];
                var m = p != null ? p.Model : null;
                if (m == null) continue;
                var h = new HeroRow
                {
                    Index = i,
                    HeroId = m.Id,
                    NameKey = m.KeyName,
                    PortraitPath = string.IsNullOrEmpty(m.TextureAssetPath) ? m.TextureCropAssetPath : m.TextureAssetPath,   // okrągły portret jak w UIHeroProgress
                    ColorLight = m.ColorLight,
                    ColorDark = m.ColorDark,
                    Health = p.HealthState,
                };
                if (p.EquippedWeapons != null)
                    foreach (var w in p.EquippedWeapons)
                    {
                        var part = w != null ? w.PartA : null;
                        if (part == null || part.Class == WeaponClasses.Rune || h.Classes.Contains(part.Class)) continue;
                        h.Classes.Add(part.Class);
                    }
                if (q.UniqueWeaponClassUsage != null && i < q.UniqueWeaponClassUsage.Length)
                    h.RuneAttacks = q.UniqueWeaponClassUsage[i];
                Heroes.Add(h);
            }
        }

        private void ReadWeapons(SerializedQuestSummary q)
        {
            var usage = q.CoreWeaponClassUsage;
            if (usage != null)
                for (int c = 0; c < usage.Length; c++)
                {
                    Attacks += usage[c];
                    if (usage[c] <= 0) continue;
                    var row = new WeaponRow { Class = (WeaponClasses)c, NameKey = ClassKey((WeaponClasses)c), Attacks = usage[c] };
                    foreach (var h in Heroes)
                        if (h.Classes.Contains(row.Class)) row.Heroes.Add(Heroes.IndexOf(h));
                    Weapons.Add(row);
                }
            Weapons.Sort((a, b) => b.Attacks != a.Attacks ? b.Attacks.CompareTo(a.Attacks) : ((int)a.Class).CompareTo((int)b.Class));

            foreach (var h in Heroes)
            {
                Attacks += h.RuneAttacks;
                int best = h.RuneAttacks;
                if (h.RuneAttacks > 0) h.Favorite = WeaponClasses.Rune;
                h.Attacks = h.RuneAttacks;
                foreach (var row in Weapons)
                {
                    if (!row.Heroes.Contains(Heroes.IndexOf(h))) continue;
                    h.Attacks += row.Attacks;
                    if (row.Attacks > best) { best = row.Attacks; h.Favorite = row.Class; }
                    foreach (int other in row.Heroes)
                        if (other != Heroes.IndexOf(h) && !h.SharedWith.Contains(other)) h.SharedWith.Add(other);
                }
            }
        }

        private void ReadLoot(SerializedQuestSummary q)
        {
            if (q.ObtainedTreasureIDs == null) return;
            for (int i = 0; i < q.ObtainedTreasureIDs.Count; i++)
            {
                int qty = q.ObtainedTreasureQty != null && i < q.ObtainedTreasureQty.Count ? q.ObtainedTreasureQty[i] : 1;
                ItemModel item = null;
                try { item = UserCollectionManager.GetItem(q.ObtainedTreasureIDs[i], ownedOnly: true); } catch (Exception) { }
                if (item is CraftingMaterialModel) LootMaterials += qty;
                else if (item is RecipeModel) LootRecipes += qty;
                else if (item is ConsumableModel) LootConsumables += qty;
                else LootItems += qty;                                   // broń, pancerz, talizmany i nieznane
            }
        }

        private void ReadFeats(SerializedGame data, SerializedQuestSummary q)
        {
            foreach (var h in Heroes)
            {
                var model = data.ActivePlayers[h.Index].Model;
                float points = 0f;
                if (q.CompletedFeatsInQuest != null)
                    foreach (var id in q.CompletedFeatsInQuest)
                    {
                        var feat = UserCollectionManager.GetFeat(id, ownedOnly: true);
                        if (feat != null && model.IsEqualTo(feat.HeroSource)) { h.FeatsCompleted++; points++; }
                    }
                if (data.FeatProgresses != null)
                    foreach (var fp in data.FeatProgresses)
                    {
                        var feat = UserCollectionManager.GetFeat(fp.RealFeatId, ownedOnly: true);
                        if (feat == null || !model.IsEqualTo(feat.HeroSource)) continue;
                        if (feat.Goal > 0) points += (float)fp.Count / feat.Goal;
                        break;
                    }
                float start = q.StartingFeatPoints != null && h.Index < q.StartingFeatPoints.Length ? q.StartingFeatPoints[h.Index] : 0f;
                h.FeatStart = (float)((decimal)start % 1.0m);
                h.FeatGained = points - h.FeatStart;
            }
        }

        internal static string ClassKey(WeaponClasses c)
        {
            return "WEAPON_" + c.GetStringValue();
        }

        /// <summary>Wiersz dziennika: same liczby i klucze, bez tekstów gry.</summary>
        public JsonLine Describe(JsonLine line)
        {
            line.Str("quest", QuestId).Num("seconds", Seconds).Int("rounds", Rounds).Int("gold", Gold)
                .Int("attacks", Attacks).Int("interactions", Interactions).Int("combat", CombatActions)
                .Str("difficulty", Difficulty.ToString())
                .Raw("loot", new JsonLine().Int("items", LootItems).Int("materials", LootMaterials)
                    .Int("recipes", LootRecipes).Int("consumables", LootConsumables).ToString());
            var weapons = new JsonArray();
            foreach (var w in Weapons)
            {
                var heroes = new JsonArray();
                foreach (int i in w.Heroes) heroes.Add(Heroes[i].HeroId);
                weapons.Add(new JsonLine().Str("class", w.Class.ToString()).Int("attacks", w.Attacks).Raw("heroes", heroes.ToString()));
            }
            line.Raw("weapons", weapons.ToString());
            var heroesArr = new JsonArray();
            foreach (var h in Heroes)
            {
                var shared = new JsonArray();
                foreach (int i in h.SharedWith) shared.Add(Heroes[i].HeroId);
                heroesArr.Add(new JsonLine().Str("hero", h.HeroId).Str("health", h.Health.ToString()).Int("attacks", h.Attacks)
                    .Int("rune", h.RuneAttacks).Str("favorite", h.Favorite.HasValue ? h.Favorite.Value.ToString() : null)
                    .Raw("shared", shared.ToString()).Int("feats", h.FeatsCompleted)
                    .Num("feat_start", h.FeatStart).Num("feat_gained", h.FeatGained));
            }
            return line.Raw("heroes", heroesArr.ToString());
        }
    }
}
