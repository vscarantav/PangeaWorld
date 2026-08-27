import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import InfrastructureTab from './Tabs/InfrastructureTab';
import IntelTab from './Tabs/IntelTab';
import IndexesTab from './Tabs/IndexesTab';
import FinancingTab from './Tabs/FinancingTab';
import DiplomacyTab from './Tabs/DiplomacyTab';
import AIAdvisor from './Widgets/AIAdvisor';
import ProjectModal from './Widgets/ProjectModal';

export default function PresidentDashboard() {
  const [activeTab, setActiveTab] = useState('infrastructure');
  const [budget, setBudget] = useState(2000);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);

  return (
    <div style={{ display: 'flex', width: '100%', height: '100%' }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        <Topbar budget={budget} />
        
        {activeTab === 'infrastructure' && <InfrastructureTab setBudget={setBudget} onOpenProjectModal={() => setIsProjectModalOpen(true)} />}
        {activeTab === 'intel' && <IntelTab setBudget={setBudget} onOpenProjectModal={() => setIsProjectModalOpen(true)} />}
        {activeTab === 'indexes' && <IndexesTab setBudget={setBudget} />}
        {activeTab === 'financing' && <FinancingTab setBudget={setBudget} />}
        {activeTab === 'diplomacy' && <DiplomacyTab />}
      </main>

      <AIAdvisor />
      
      {isProjectModalOpen && (
        <ProjectModal onClose={() => setIsProjectModalOpen(false)} />
      )}
    </div>
  );
}
