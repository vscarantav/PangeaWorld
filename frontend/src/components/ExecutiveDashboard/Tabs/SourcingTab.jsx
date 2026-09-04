import React, { useEffect, useState } from 'react';
import SupplyChainMap from '../Widgets/SupplyChainMap';
import { useGame } from '../../../context/GameContext';

export default function SourcingTab() {
  const { market, nations, session, resourceMarket, loadResourceMarket } = useGame();
  const resources = Object.keys(market?.resources || {});
  const [resourceType, setResourceType] = useState(resources[0] || 'Energy');

  useEffect(() => {
    if (resources.length && !resources.includes(resourceType)) setResourceType(resources[0]);
  }, [market, resourceType]);
  useEffect(() => { if (session) loadResourceMarket(resourceType).catch(() => {}); }, [resourceType, session]);

  const nationName = (id) => nations.find((nation) => nation.id === id)?.name || `Nation ${id}`;
  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-8"><div className="card-header"><h3 className="card-title"><i className="fa-solid fa-map-location-dot"></i> Global Supply Chain</h3></div><SupplyChainMap /></div>

        <div className="card col-4">
          <div className="card-header"><h3 className="card-title"><i className="fa-solid fa-boxes-stacked"></i> Supplier Marketplace</h3></div>
          <div className="input-group"><label>Required Resource</label><select value={resourceType} onChange={(event) => setResourceType(event.target.value)} style={{ width: '100%', padding: '0.75rem', background: 'rgba(255,255,255,0.1)', border: '1px solid var(--border-light)', color: 'white', borderRadius: '8px' }}>{resources.map((resource) => <option key={resource}>{resource}</option>)}</select></div>
          <div className="data-list" style={{ marginTop: '1rem' }}>
            {(resourceMarket?.suppliers || []).map((supplier) => <div className="data-item" key={supplier.nation_id}>
              <div className="data-item-info"><h4>{nationName(supplier.nation_id)}</h4><p>{Number(supplier.stockpile || 0).toFixed(1)} units available</p></div>
              <span className="data-item-value">${Number(supplier.estimated_rail_unit_cost || 0).toFixed(2)} landed</span>
            </div>)}
            {!resourceMarket?.suppliers?.length && <p className="text-muted">No suppliers currently report this resource.</p>}
          </div>
        </div>

        <div className="card col-12"><div className="card-header"><h3 className="card-title"><i className="fa-solid fa-truck-fast"></i> Logistics Breakdown</h3></div>
          <p className="text-muted">Phase 1 estimates use one rail edge; route selection and trade execution are planned for the logistics layer.</p>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}><thead><tr style={{ borderBottom: '1px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}><th style={{ padding: '1rem' }}>Supplier</th><th style={{ padding: '1rem' }}>Mode</th><th style={{ padding: '1rem' }}>Base Price</th><th style={{ padding: '1rem' }}>Landed Cost</th></tr></thead>
            <tbody>{(resourceMarket?.suppliers || []).map((supplier) => <tr key={supplier.nation_id}><td style={{ padding: '1rem' }}>{nationName(supplier.nation_id)}</td><td style={{ padding: '1rem' }}>Rail</td><td style={{ padding: '1rem' }}>${Number(market?.resources?.[resourceType]?.base_price || 0).toFixed(2)}</td><td style={{ padding: '1rem', fontWeight: 'bold' }}>${Number(supplier.estimated_rail_unit_cost || 0).toFixed(2)}</td></tr>)}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
