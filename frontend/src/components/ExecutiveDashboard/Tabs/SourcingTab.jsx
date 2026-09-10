/* oxlint-disable react/set-state-in-effect -- The selected resource must track a replaced market catalog. */
import React, { useEffect, useMemo, useState } from 'react';
import SupplyChainMap from '../Widgets/SupplyChainMap';
import { useGame } from '../../../context/GameContext';

export default function SourcingTab() {
  const { market, nations, company, session, resourceMarket, loadResourceMarket } = useGame();
  const resources = useMemo(() => Object.keys(market?.resources || {}), [market]);
  const [resourceType, setResourceType] = useState(resources[0] || 'Energy');

  useEffect(() => {
    if (resources.length && !resources.includes(resourceType)) setResourceType(resources[0]);
  }, [resources, resourceType]);
  useEffect(() => { if (session && company) loadResourceMarket(resourceType, company.nation_id).catch(() => {}); }, [resourceType, session, company, loadResourceMarket]);

  const nationName = (id) => nations.find((nation) => nation.id === id)?.name || `Nation ${id}`;
  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-8"><div className="card-header"><h3 className="card-title"><i className="fa-solid fa-map-location-dot"></i> Global Supply Chain</h3></div><SupplyChainMap />
          <div className="data-list" style={{ marginTop: '1rem' }}>
            {(company?.supply_chain_config?.suppliers || []).map((route, index) => <div className="data-item" key={`${route.supplier_nation_id}-${route.resource_type}-${index}`}>
              <span><i className="fa-solid fa-route positive"></i> {route.resource_type} from {nationName(route.supplier_nation_id)} via {route.mode}</span>
              <span className="data-item-value positive">{route.status === 'filled' ? 'Active' : route.status} · {route.quantity} units</span>
            </div>)}
            {!company?.supply_chain_config?.suppliers?.length && <p className="text-muted">No active sourcing route. Submit one from the Decisions tab.</p>}
          </div>
        </div>

        <div className="card col-4">
          <div className="card-header"><h3 className="card-title"><i className="fa-solid fa-boxes-stacked"></i> Supplier Marketplace</h3></div>
          <div className="input-group"><label>Required Resource</label><select value={resourceType} onChange={(event) => setResourceType(event.target.value)} style={{ width: '100%', padding: '0.75rem', background: 'rgba(255,255,255,0.1)', border: '1px solid var(--border-light)', color: 'white', borderRadius: '8px' }}>{resources.map((resource) => <option key={resource}>{resource}</option>)}</select></div>
          <div className="data-list" style={{ marginTop: '1rem' }}>
            {(resourceMarket?.suppliers || []).map((supplier) => <div className="data-item" key={supplier.nation_id}>
              <div className="data-item-info"><h4>{nationName(supplier.nation_id)}</h4><p>{Number(supplier.stockpile || 0).toFixed(1)} units available</p></div>
              <span className="data-item-value">from ${Math.min(...supplier.routes.map((route) => Number(route.unit_cost))).toFixed(2)}/unit</span>
            </div>)}
            {!resourceMarket?.suppliers?.length && <p className="text-muted">No suppliers currently report this resource.</p>}
          </div>
        </div>

        <div className="card col-12"><div className="card-header"><h3 className="card-title"><i className="fa-solid fa-truck-fast"></i> Logistics Breakdown</h3></div>
          <p className="text-muted">These server-calculated routes use the saved world map, current scarcity, tariffs, insurance, and port fees. Choose an order in the Decisions tab.</p>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}><thead><tr style={{ borderBottom: '1px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}><th style={{ padding: '1rem' }}>Supplier</th><th style={{ padding: '1rem' }}>Mode</th><th style={{ padding: '1rem' }}>Distance</th><th style={{ padding: '1rem' }}>Transit</th><th style={{ padding: '1rem' }}>Landed Cost</th></tr></thead>
            <tbody>{(resourceMarket?.suppliers || []).flatMap((supplier) => supplier.routes.map((route) => <tr key={`${supplier.nation_id}-${route.mode}`}><td style={{ padding: '1rem' }}>{nationName(supplier.nation_id)}</td><td style={{ padding: '1rem', textTransform: 'capitalize' }}>{route.mode}</td><td style={{ padding: '1rem' }}>{route.distance_km} km</td><td style={{ padding: '1rem' }}>{route.transit_rounds === 0 ? 'Immediate' : `${route.transit_rounds} round(s)`}</td><td style={{ padding: '1rem', fontWeight: 'bold' }}>${Number(route.unit_cost).toFixed(2)}</td></tr>))}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
