/* oxlint-disable react/set-state-in-effect, react-hooks/exhaustive-deps -- Effects intentionally synchronize persisted drafts and valid route selections. */
import React, { useEffect, useMemo, useState } from 'react';
import NewsFeed from '../Widgets/NewsFeed';
import { useGame } from '../../../context/GameContext';

const controlStyle = {
  width: '100%', padding: '0.75rem', background: 'rgba(255,255,255,0.1)',
  border: '1px solid var(--border-light)', color: 'white', borderRadius: '8px',
};

export default function DecisionsTab() {
  const { company, session, market, resourceMarket, loadResourceMarket, saveCompanyDraft, submitCompany } = useGame();
  const resources = useMemo(() => Object.keys(market?.resources || {}), [market]);
  const [price, setPrice] = useState(Number(company?.products?.Widget?.price || 299));
  const [headcount, setHeadcount] = useState(20);
  const [productionUnits, setProductionUnits] = useState(1);
  const [rndInvestment, setRndInvestment] = useState(0);
  const [resourceType, setResourceType] = useState(resources[0] || 'Energy');
  const [supplierNationId, setSupplierNationId] = useState('');
  const [quantity, setQuantity] = useState(0);
  const [mode, setMode] = useState('rail');
  const [savedDecision, setSavedDecision] = useState(null);
  const [submittedSignature, setSubmittedSignature] = useState('');
  const [message, setMessage] = useState('');

  const decisionKey = session && company ? `pangeaworld.companyDecision.${session.id}.${session.current_round}.${company.id}` : null;
  const submittedKey = decisionKey ? `${decisionKey}.submitted` : null;
  const sessionId = session?.id;
  const currentRound = session?.current_round;
  const companyId = company?.id;
  const companyNationId = company?.nation_id;
  const productPrice = company?.products?.Widget?.price;
  const productProductionUnits = company?.products?.Widget?.production_units;

  useEffect(() => {
    if (!company || !session) return;
    const stored = window.localStorage.getItem(`pangeaworld.companyDecision.${session.id}.${session.current_round}.${company.id}`);
    if (stored) {
      try {
        const decision = JSON.parse(stored);
        const order = decision.sourcing?.[0];
        setPrice(Number(decision.price ?? productPrice ?? 299));
        setHeadcount(Number(decision.headcount ?? 20));
        setProductionUnits(Number(decision.production_units ?? 1));
        setRndInvestment(Number(decision.rnd_investment ?? 0));
        if (order) {
          setResourceType(order.resource_type);
          setSupplierNationId(String(order.supplier_nation_id));
          setQuantity(Number(order.quantity));
          setMode(order.mode);
        } else {
          setQuantity(0);
        }
        setSavedDecision(decision);
        setSubmittedSignature(window.localStorage.getItem(`${decisionKey}.submitted`) || '');
      } catch {
        window.localStorage.removeItem(decisionKey);
        window.localStorage.removeItem(`${decisionKey}.submitted`);
      }
    } else {
      setPrice(Number(productPrice || 299));
      setHeadcount(20);
      setProductionUnits(Number(productProductionUnits || 1));
      setRndInvestment(0);
      setResourceType(resources[0] || 'Energy');
      setSupplierNationId('');
      setQuantity(0);
      setMode('rail');
      setSavedDecision(null);
      setSubmittedSignature('');
    }
    setMessage('');
  }, [companyId, currentRound, decisionKey, productPrice, productProductionUnits, resources, sessionId]);

  useEffect(() => {
    if (resources.length && !resources.includes(resourceType)) setResourceType(resources[0]);
  }, [resources, resourceType]);

  useEffect(() => {
    if (session && company) loadResourceMarket(resourceType, company.nation_id).catch((error) => setMessage(error.message));
  }, [company, companyNationId, loadResourceMarket, resourceType, session]);

  const suppliers = resourceMarket?.resource_type === resourceType ? resourceMarket.suppliers || [] : [];
  useEffect(() => {
    if (!suppliers.length) return;
    if (!suppliers.some((supplier) => String(supplier.nation_id) === String(supplierNationId))) {
      const preferred = suppliers.find((supplier) => supplier.nation_id !== company?.nation_id) || suppliers[0];
      setSupplierNationId(String(preferred.nation_id));
    }
  }, [companyNationId, resourceMarket, resourceType, supplierNationId, suppliers]);

  const selectedSupplier = suppliers.find((supplier) => String(supplier.nation_id) === String(supplierNationId));
  const availableRoutes = selectedSupplier?.routes || [];
  useEffect(() => {
    if (availableRoutes.length && !availableRoutes.some((route) => route.mode === mode)) setMode(availableRoutes[0].mode);
  }, [availableRoutes, mode]);
  const selectedRoute = availableRoutes.find((route) => route.mode === mode);

  const currentDecision = useMemo(() => ({
    price,
    headcount,
    production_units: productionUnits,
    rnd_investment: rndInvestment,
    sourcing: quantity > 0 && supplierNationId ? [{
      resource_type: resourceType,
      supplier_nation_id: Number(supplierNationId),
      quantity,
      mode,
    }] : [],
  }), [price, headcount, productionUnits, rndInvestment, resourceType, supplierNationId, quantity, mode]);
  const currentSignature = JSON.stringify(currentDecision);
  const isSaved = savedDecision != null && JSON.stringify(savedDecision) === currentSignature;
  const isSubmitted = isSaved && submittedSignature === currentSignature;

  const saveDecisions = async () => {
    if (decisionKey) window.localStorage.setItem(decisionKey, currentSignature);
    try {
      await saveCompanyDraft(currentDecision);
      setSavedDecision(currentDecision);
      setMessage('Draft saved on the server. It is not submitted yet.');
    } catch (error) {
      setMessage(error.message);
    }
  };

  const submitDecisions = async () => {
    try {
      const receipt = await submitCompany(savedDecision);
      window.localStorage.setItem(submittedKey, currentSignature);
      setSubmittedSignature(currentSignature);
      setMessage(`Submitted to the server for Round ${session.current_round} (decision #${receipt.id}).`);
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-8">
          <div className="card-header">
            <h3 className="card-title"><i className="fa-solid fa-gavel"></i> Round {session?.current_round} Decisions</h3>
            <span style={{ fontSize: '0.8rem', background: 'rgba(59, 130, 246, 0.2)', color: 'var(--accent-primary)', padding: '0.25rem 0.75rem', borderRadius: '12px' }}>
              {session?.phase === 'company' ? 'Company phase' : `Server phase: ${session?.phase}`}
            </span>
          </div>
          <fieldset disabled={session?.phase !== 'company'} style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="input-group">
              <label>Product price ($)</label>
              <div className="range-slider-container">
                <span className="text-muted">$50</span>
                <input aria-label="Product price" type="range" min="50" max="600" value={price} onChange={(event) => setPrice(Number(event.target.value))} />
                <span className="range-value">${price}</span>
              </div>
            </div>
            <div className="input-group">
              <label>Hiring target</label>
              <div className="range-slider-container">
                <span className="text-muted">0</span>
                <input aria-label="Hiring target" type="range" min="0" max="100" value={headcount} onChange={(event) => setHeadcount(Number(event.target.value))} />
                <span className="range-value">{headcount} workers</span>
              </div>
            </div>
            <div className="input-group">
              <label>Production volume multiplier</label>
              <div className="range-slider-container">
                <span className="text-muted">0.5x</span>
                <input aria-label="Production volume" type="range" min="0.5" max="2" step="0.1" value={productionUnits} onChange={(event) => setProductionUnits(Number(event.target.value))} />
                <span className="range-value">{productionUnits.toFixed(1)}x</span>
              </div>
            </div>
            <div className="input-group">
              <label>R&amp;D investment ($)</label>
              <div className="range-slider-container">
                <span className="text-muted">$0</span>
                <input aria-label="R&D investment" type="range" min="0" max="2000" step="100" value={rndInvestment} onChange={(event) => setRndInvestment(Number(event.target.value))} />
                <span className="range-value">${rndInvestment.toLocaleString()}</span>
              </div>
              <p className="text-muted">R&amp;D reduces this round's profit and improves product quality.</p>
            </div>

            <div>
              <h4 style={{ marginBottom: '1rem' }}><i className="fa-solid fa-truck-ramp-box"></i> Resource sourcing order</h4>
              <div className="dashboard-grid">
                <div className="input-group col-6"><label>Resource</label><select style={controlStyle} value={resourceType} onChange={(event) => setResourceType(event.target.value)}>{resources.map((resource) => <option key={resource}>{resource}</option>)}</select></div>
                <div className="input-group col-6"><label>Supplier</label><select style={controlStyle} value={supplierNationId} onChange={(event) => setSupplierNationId(event.target.value)}>{suppliers.map((supplier) => <option key={supplier.nation_id} value={supplier.nation_id}>{supplier.nation_name} ({Number(supplier.stockpile).toFixed(0)} available)</option>)}</select></div>
                <div className="input-group col-6"><label>Shipping mode</label><select style={controlStyle} value={mode} onChange={(event) => setMode(event.target.value)}>{availableRoutes.map((route) => <option key={route.mode} value={route.mode}>{route.mode} · {route.distance_km} km · ${Number(route.unit_cost).toFixed(2)}/unit</option>)}</select></div>
                <div className="input-group col-6"><label>Quantity (0 skips sourcing)</label><input aria-label="Sourcing quantity" style={controlStyle} type="number" min="0" max={Math.floor(Number(selectedSupplier?.stockpile || 0))} value={quantity} onChange={(event) => setQuantity(Math.max(0, Number(event.target.value)))} /></div>
              </div>
              {quantity > 0 && selectedRoute && <p className="text-muted" style={{ marginTop: '0.75rem' }}>Estimated landed total: ${(Number(selectedRoute.unit_cost) * quantity).toFixed(2)} · transit {selectedRoute.transit_rounds === 0 ? 'this round' : `${selectedRoute.transit_rounds} round(s)`}</p>}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <button className="btn secondary" disabled={session?.phase !== 'company'} onClick={saveDecisions}>
                <i className="fa-solid fa-floppy-disk"></i> Save Decisions
              </button>
              <button className="btn" disabled={session?.phase !== 'company' || !isSaved || isSubmitted} onClick={submitDecisions}>
                <i className={`fa-solid ${isSubmitted ? 'fa-circle-check' : 'fa-paper-plane'}`}></i> {isSubmitted ? 'Submitted' : 'Submit Decisions'}
              </button>
              <strong className={isSubmitted ? 'positive' : isSaved ? 'text-yellow' : 'text-muted'}>{isSubmitted ? 'Server confirmed' : isSaved ? 'Saved locally' : 'Unsaved changes'}</strong>
            </div>
            {session?.phase === 'company' && !isSaved && <p className="text-muted">Save your changes before submitting.</p>}
            {message && <p className="text-muted">{message}</p>}
          </div>
          </fieldset>
        </div>
        <div className="card col-4"><NewsFeed /></div>
      </div>
    </div>
  );
}
