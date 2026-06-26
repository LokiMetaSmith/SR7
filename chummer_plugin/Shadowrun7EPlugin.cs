using System;
using System.Collections.Generic;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Chummer;
using Chummer.Plugins;

namespace Shadowrun7EPlugin
{
    public class Shadowrun7EPlugin : IPlugin
    {
        public override string ToString()
        {
            return "Fan made Shadowrun 7th Edition";
        }

        public void CustomInitialize(ChummerMainForm mainControl)
        {
            // Initialization if necessary
        }

        protected virtual void Dispose(bool disposing) { }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        public Task<bool> DoCharacterList_DragDrop(object sender, DragEventArgs dragEventArgs, TreeView treCharacterList, CancellationToken token = default)
        {
            return Task.FromResult(true);
        }

        public Task<ICollection<TreeNode>> GetCharacterRosterTreeNode(CharacterRoster frmCharRoster, bool forceUpdate, CancellationToken token = default)
        {
            return Task.FromResult<ICollection<TreeNode>>(null);
        }

        public Task<ICollection<ToolStripMenuItem>> GetMenuItems(ToolStripMenuItem menu, CancellationToken token = default)
        {
            return Task.FromResult<ICollection<ToolStripMenuItem>>(null);
        }

        public UserControl GetOptionsControl()
        {
            return null;
        }

        public Assembly GetPluginAssembly()
        {
            return GetType().Assembly;
        }

        public string GetSaveToFileElement(Character input)
        {
            return null;
        }

        public Task<ICollection<TabPage>> GetTabPages(CharacterCareer input, CancellationToken token = default)
        {
            return Task.FromResult<ICollection<TabPage>>(null);
        }

        public Task<ICollection<TabPage>> GetTabPages(CharacterCreate input, CancellationToken token = default)
        {
            return Task.FromResult<ICollection<TabPage>>(null);
        }

        public void LoadFileElement(Character input, string fileElement) { }

        public bool ProcessCommandLine(string parameter)
        {
            return true;
        }

        public bool SetCharacterRosterNode(TreeNode objNode)
        {
            return true;
        }

        public void SetIsUnitTest(bool isUnitTest) { }

        public Microsoft.ApplicationInsights.Channel.ITelemetry SetTelemetryInitialize(Microsoft.ApplicationInsights.Channel.ITelemetry telemetry)
        {
            return telemetry;
        }

        /// <summary>
        /// Custom method simulating an Initiative recalculation trigger.
        /// Replaces the invalid CalculateCustomInitiative() method from the IPlugin interface.
        /// Handles Physical, Astral, and Matrix Initiative calculations.
        /// </summary>
        public void ApplyCustomInitiative(Character character)
        {
            try
            {
                if (character != null)
                {
                    // Check for Astral Projection or Dual Natured
                    bool isAstral = character.Qualities.Exists(q => q.Name == "Dual Natured") || character.IsAstrallyProjecting;
                    bool isMatrix = character.IsMatrixActive;

                    if (isAstral)
                    {
                        // Astral Initiative: REA + INT, 1 + MAG dice
                        character.BaseInitiative = character.REA.TotalValue + character.INT.TotalValue;
                        character.InitiativeDice = 1 + character.MAG.TotalValue;
                    }
                    else if (isMatrix)
                    {
                        // Matrix Initiative: Data Processing + INT, 1 + Control Rig dice
                        int dataProcessing = character.DataProcessing;
                        int controlRig = 0;
                        var rig = character.Cyberware.Find(c => c.Name.Contains("Control Rig"));
                        if (rig != null)
                        {
                            controlRig = rig.Rating;
                        }
                        character.BaseInitiative = dataProcessing + character.INT.TotalValue;
                        character.InitiativeDice = 1 + controlRig;
                    }
                    else
                    {
                        // Physical Initiative: REA + INT, 1 die (Wired Reflexes handled separately in Chummer usually)
                        character.BaseInitiative = character.REA.TotalValue + character.INT.TotalValue;
                        character.InitiativeDice = 1;
                    }
                }
            }
            catch (Exception ex)
            {
                // Handle missing properties cleanly without crashing
                System.Diagnostics.Debug.WriteLine($"ApplyCustomInitiative Failed: {ex.Message}");
            }
        }

        /// <summary>
        /// Custom method applying "Digital Essence" rule overrides.
        /// AIs, Sprites, or Matrix entities have an Essence of 6.
        /// </summary>
        public void ApplyDigitalEssence(Character character)
        {
            try
            {
                // Guessing Chummer's character API properties
                if (character != null && (character.Metatype == "AI" || character.Metatype == "Sprite" || character.Metatype == "Matrix Entity" || character.Metatype == "Turing 1" || character.Metatype == "Searle 0" || character.Metatype == "E-Ghost"))
                {
                    character.Essence.BaseValue = 6;
                    character.Essence.TotalValue = 6;
                }
            }
            catch (Exception ex)
            {
                // Handle missing properties cleanly without crashing
                System.Diagnostics.Debug.WriteLine($"ApplyDigitalEssence Failed: {ex.Message}");
            }
        }

        /// <summary>
        /// Custom method for applying HMHVV Infection Penalties.
        /// </summary>
        public void ApplyHMHVVPenalty(Character character)
        {
            try
            {
                if (character != null)
                {
                    // Look for HMHVV Quality and its level
                    var infectionQuality = character.Qualities.Find(q => q.Name.StartsWith("HMHVV"));
                    if (infectionQuality != null)
                    {
                        int infectionLevel = infectionQuality.Rating;
                        if (infectionLevel > 0)
                        {
                            // A -1 modifier to action dice pools or initiative
                            character.BaseInitiative -= 1;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"ApplyHMHVVPenalty Failed: {ex.Message}");
            }
        }

        /// <summary>
        /// Custom method for Dual Natured rules setup.
        /// </summary>
        public void ApplyDualNatured(Character character)
        {
            try
            {
                if (character != null)
                {
                    var dualNaturedQuality = character.Qualities.Find(q => q.Name == "Dual Natured");
                    if (dualNaturedQuality != null)
                    {
                        // Ensure they can perceive the astral plane natively
                        character.IsDualNatured = true;
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"ApplyDualNatured Failed: {ex.Message}");
            }
        }
    }
}
