import React from 'react';
import { Globe, Users, Vote } from 'lucide-react';
import { useGame } from '../../../context/GameContext';

export default function DiplomacyTab() {
  const { nations } = useGame();
  return <section className="dashboard-grid">
    <div className="card col-8"><div className="card-header"><h3 className="card-title"><Globe /> Pangea Assembly</h3><span className="text-muted">Global Communications Forum</span></div><p className="text-muted">No assembly messages have been recorded for this session. Messaging and treaty proposals are planned for the multiplayer phase.</p></div>
    <div className="card col-4"><div className="card-header"><h3 className="card-title"><Users /> Nations in Session</h3></div><div className="data-list">{(nations || []).map((nation) => <div className="data-item" key={nation.id}><span>{nation.name}</span><span className="data-item-value">No treaty data</span></div>)}</div></div>
    <div className="card col-12"><div className="card-header"><h3 className="card-title"><Vote /> FMI Voting</h3></div><p className="text-muted">Sanctions voting is not yet connected to the Phase 1 decision ledger.</p></div>
  </section>;
}
