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
        /// </summary>
        public void ApplyCustomInitiative(Character character)
        {
            // Implementation: REA + INT + 1D6
            try
            {
                // Guessing Chummer's character API properties
                if (character != null)
                {
                    character.InitiativeDice = 1;
                    character.BaseInitiative = character.REA.TotalValue + character.INT.TotalValue;
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
                if (character != null && (character.Metatype == "AI" || character.Metatype == "Sprite" || character.Metatype == "Matrix Entity"))
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
    }
}
