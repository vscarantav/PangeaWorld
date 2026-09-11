import React, { useState } from 'react';
import { Target, UserCheck, Skull, MapPin } from 'lucide-react';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';
import { Radar } from 'react-chartjs-2';
import GameMap from '../../GameMap';
import { useGame } from '../../../context/GameContext';
import Phase3Results from '../Widgets/Phase3Results';
import NewsFeed from '../../ExecutiveDashboard/Widgets/NewsFeed';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

export default function IntelTab({ onOpenProjectModal }) {
  const { nation, nations, session, saveMapSnapshot, savePresidentialReadiness } = useGame();
  const [troopBudget, setTroopBudget] = useState(300);
  const [intelBudget, setIntelBudget] = useState(150);
  const [covertBudget, setCovertBudget] = useState(50);
  const [posture, setPosture] = useState('defend');
  const [preparednessBudget, setPreparednessBudget] = useState(200);
  const [procurement, setProcurement] = useState({ infantry: 0, navy: 0, air_force: 0 });
  const [operationType, setOperationType] = useState('attack');
  const [engagementLimit, setEngagementLimit] = useState(1);
  const [retreatThreshold, setRetreatThreshold] = useState(0.5);
  const [launchAttack, setLaunchAttack] = useState(false);
  const [targetNationId, setTargetNationId] = useState('');
  const [attackUnits, setAttackUnits] = useState({ infantry: 0, navy: 0, air_force: 0 });
  const [message, setMessage] = useState('');
  const militaryInvestment = troopBudget + intelBudget + covertBudget;
  const procurementCost = procurement.infantry * 100 + procurement.navy * 250 + procurement.air_force * 350;
  const missionCost = launchAttack ? ({ blockade: 50, intelligence: 25 }[operationType] || 0) : 0;
  const totalCommitment = militaryInvestment + preparednessBudget + procurementCost + missionCost;
  const remainingTreasury = Math.max(0, (nation?.treasury || 0) - totalCommitment);
  const updateUnits = (setter, units, type, value) => setter({ ...units, [type]: Math.max(0, Number(value) || 0) });

  const radarData = {
    labels: ['Army Size', 'Naval Power', 'Air Superiority', 'Intel Network', 'Defense Infra', 'Cyber'],
    datasets: [
      {
        label: 'Valdoria (Us)',
        data: [nation?.military_atk || 0, nation?.military_def || 0, nation?.military_def || 0, 0, nation?.military_def || 0, 0],
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: '#3b82f6',
        pointBackgroundColor: '#3b82f6',
        borderWidth: 2
      },
      {
        label: 'Drakmoor (AI)',
        data: [nations.find((item) => item.name === 'Drakmoor')?.military_atk || 0, nations.find((item) => item.name === 'Drakmoor')?.military_def || 0, 0, 0, 0, 0],
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
        borderColor: '#ef4444',
        pointBackgroundColor: '#ef4444',
        borderWidth: 2
      }
    ]
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
        pointLabels: { color: '#94a3b8', font: { size: 11 } },
        ticks: { display: false, min: 0, max: 10 }
      }
    },
    plugins: {
      legend: { labels: { color: '#f8fafc' } }
    }
  };

  return (
    <section className="dashboard-grid">
      <Phase3Results />
      <details className="card col-12"><summary>Pangea Times: market reports and source exercises</summary><NewsFeed /></details>
      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><Target /> Threat Assessment</h3>
        </div>
        <div className="chart-container large">
          <Radar data={radarData} options={radarOptions} />
        </div>
      </div>

      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><UserCheck /> Intelligence Reports</h3>
        </div>
        <div className="data-list">{(nations || []).filter((item) => item.id !== nation?.id).map((item) => <div className="data-item" key={item.id}><div className="data-item-info"><h4>{item.name}</h4><p>Public military indices: ATK {item.military_atk} · DEF {item.military_def}</p><p>Public inventory: {item.military_inventory?.infantry || 0} infantry · {item.military_inventory?.navy || 0} navy · {item.military_inventory?.air_force || 0} air force</p></div><div className="data-item-value">PUBLIC</div></div>)}</div>
      </div>

      {/* NEW: Military Map Integration */}
      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><MapPin /> Deployment & Ops Map</h3>
        </div>
        <div className="map-widget" style={{ height: '350px' }}>
          {session && <GameMap seed={session.seed} mapSnapshot={session.map_snapshot} onSnapshotChange={saveMapSnapshot} />}
        </div>
      </div>
      
      <div className="card col-12">
        <div className="flex-between">
          <h3 className="card-title">Military Readiness Index (DEF/ATK)</h3>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="btn" style={{ width: 'auto' }} onClick={onOpenProjectModal}>
              <Target size={16} /> Plan Operation
            </button>
            <button className="btn danger" style={{ width: 'auto' }}>
              <Skull size={16} /> DEFCON Settings
            </button>
          </div>
        </div>
      </div>

      <div className="card col-12">
        <div className="card-header">
          <h3 className="card-title">Military & Intel Budget Allocation (Next Round)</h3>
        </div>
        <div className="dashboard-grid" style={{ gap: '2rem' }}>
          <div className="col-6">
            <div className="input-group">
              <label>Troop Deployments ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={troopBudget} onChange={(e) => setTroopBudget(Number(e.target.value))} />
                <span className="range-value">${troopBudget}M</span>
              </div>
            </div>
            <div className="input-group">
              <label>Intelligence Gathering ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={intelBudget} onChange={(e) => setIntelBudget(Number(e.target.value))} />
                <span className="range-value">${intelBudget}M</span>
              </div>
            </div>
          </div>
          <div className="col-6">
            <div className="input-group">
              <label>Covert Operations ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={covertBudget} onChange={(e) => setCovertBudget(Number(e.target.value))} />
                <span className="range-value">${covertBudget}M</span>
              </div>
            </div>
          </div>
          <div className="col-6">
            <div className="input-group">
              <label>Military posture</label>
              <select value={posture} onChange={(event) => setPosture(event.target.value)}>
                <option value="defend">Defend — protect domestic capacity</option>
                <option value="patrol">Patrol — secure routes</option>
                <option value="reconnaissance">Reconnaissance — improve awareness</option>
              </select>
            </div>
            <div className="input-group">
              <label>Emergency preparedness fund ($ Millions)</label>
              <div className="range-slider-container">
                <input aria-label="Emergency preparedness fund" type="range" min="0" max="1000" value={preparednessBudget} onChange={(event) => setPreparednessBudget(Number(event.target.value))} />
                <span className="range-value">${preparednessBudget}M</span>
              </div>
              <small className="text-muted">Natural-disaster recovery uses this public fund first. Uncovered companies pay costly private emergency financing, reducing approval and GDP.</small>
            </div>
            <div className="input-group">
              <label>Unit procurement ($100M infantry · $250M navy · $350M air force)</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {['infantry', 'navy', 'air_force'].map((type) => <label key={type} style={{ flex: 1, fontSize: 12 }}>{type.replace('_', ' ')}<input disabled={session?.phase !== 'presidential'} aria-label={`Procure ${type}`} type="number" min="0" max="1000" value={procurement[type]} onChange={(event) => updateUnits(setProcurement, procurement, type, event.target.value)} /></label>)}
              </div>
              <small className="text-muted">Inventory: infantry {nation?.military_inventory?.infantry || 0} · navy {nation?.military_inventory?.navy || 0} · air force {nation?.military_inventory?.air_force || 0}. Procurement cost: ${procurementCost}M.</small>
            </div>
            <div className="input-group">
              <label><input disabled={session?.phase !== 'presidential'} type="checkbox" checked={launchAttack} onChange={(event) => setLaunchAttack(event.target.checked)} /> Submit a direct attack order</label>
              {launchAttack && <>{session?.ruleset_version === 'phase3-closure-v1' && <><label>Operation<select aria-label="Operation type" value={operationType} onChange={(e) => setOperationType(e.target.value)}><option value="attack">Attack</option><option value="blockade">Naval blockade ($50M; requires navy)</option><option value="intelligence">Intelligence mission ($25M)</option></select></label>{operationType === 'attack' && <><label>Maximum engagements<input aria-label="Maximum engagements" type="number" min="1" max="3" value={engagementLimit} onChange={(e) => setEngagementLimit(Number(e.target.value))} /></label><label>Retreat after fraction lost<input aria-label="Retreat threshold" type="number" min="0" max="1" step="0.1" value={retreatThreshold} onChange={(e) => setRetreatThreshold(Number(e.target.value))} /></label></>}<p>One operation per round: a blockade or intelligence mission gives up an attack. Blockades stop foreign sea orders this round while a naval force survives. Intelligence reveals a private resolved-round observation. War raises consumer prices, insurance costs and displacement losses.</p></>}<select aria-label="Attack target" value={targetNationId} onChange={(event) => setTargetNationId(event.target.value)}><option value="">Select target nation</option>{nations.filter((item) => item.id !== nation?.id).map((item) => <option key={item.id} value={item.id}>{item.name} · ATK {item.military_atk} / DEF {item.military_def}</option>)}</select><div style={{ display: 'flex', gap: 8, marginTop: 8 }}>{['infantry', 'navy', 'air_force'].map((type) => <label key={type} style={{ flex: 1, fontSize: 12 }}>Deploy {type.replace('_', ' ')}<input aria-label={`Deploy ${type}`} type="number" min="0" max={nation?.military_inventory?.[type] || 0} value={attackUnits[type]} onChange={(event) => updateUnits(setAttackUnits, attackUnits, type, event.target.value)} /></label>)}</div><small className="text-muted">Attack deployments use existing inventory; newly procured units arrive after this round's operation. Attacks resolve by nation ID. Earlier losses reduce committed forces; an order with no surviving committed units is cancelled.</small></>}
            </div>
            <p className="text-muted">Military + preparedness + procurement + mission: ${totalCommitment}M · Remaining treasury: ${remainingTreasury.toFixed(0)}M</p>
            <p className="text-muted">This plan leaves ${remainingTreasury.toFixed(0)}M for civilian services, infrastructure, and tax relief this round.</p>
            <button className="btn" disabled={session?.phase !== 'presidential' || totalCommitment > (nation?.treasury || 0) || (launchAttack && (!targetNationId || !Object.values(attackUnits).some(Boolean)))} onClick={async () => {
              try {
                const receipt = await savePresidentialReadiness({ military_posture: posture, military_investment: militaryInvestment, emergency_preparedness_investment: preparednessBudget, military_procurement: procurement, military_operation: launchAttack ? { operation_type: operationType, engagement_limit: engagementLimit, retreat_threshold: retreatThreshold, target_nation_id: Number(targetNationId), units: attackUnits } : null });
                setMessage(`Readiness plan saved for Round ${receipt.round_id}.`);
              } catch (error) { setMessage(error.message); }
            }}>Save readiness plan</button>
            {message && <p className="text-muted" style={{ marginTop: 8 }}>{message}</p>}
          </div>
        </div>
      </div>
    </section>
  );
}
