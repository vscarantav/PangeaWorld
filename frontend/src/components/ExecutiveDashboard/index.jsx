import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import FinancialsTab from './Tabs/FinancialsTab';
import SourcingTab from './Tabs/SourcingTab';
import MarketTab from './Tabs/MarketTab';
import DecisionsTab from './Tabs/DecisionsTab';
import AIAdvisor from './Widgets/AIAdvisor';

export default function ExecutiveDashboard() {
  const [activeTab, setActiveTab] = useState('financials');

  return (
    <div style={{ display: 'flex', width: '100%', height: '100%' }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        <Topbar />
        
        {activeTab === 'financials' && <FinancialsTab />}
        {activeTab === 'sourcing' && <SourcingTab />}
        {activeTab === 'market' && <MarketTab />}
        {activeTab === 'decisions' && <DecisionsTab />}
      </main>

      <AIAdvisor />
    </div>
  );
}
