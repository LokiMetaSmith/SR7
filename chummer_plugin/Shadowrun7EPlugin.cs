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

        // Custom Initiative rolling for Shadowrun 7E: REA + INT + 1D6
        // This method provides the random 1D6 component.
        private static readonly Random _random = new Random();

        public int CalculateCustomInitiative()
        {
            return _random.Next(1, 7);
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
    }
}
