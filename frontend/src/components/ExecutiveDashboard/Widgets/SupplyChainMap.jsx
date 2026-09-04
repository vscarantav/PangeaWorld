import React, { useState } from 'react';
import GameMap from '../../GameMap';
import { useGame } from '../../../context/GameContext';

export default function SupplyChainMap() {
  const { session, saveMapSnapshot } = useGame();
  const [isModalOpen, setIsModalOpen] = useState(false);
  if (!session) return null;
  return (
    <>
      <div className="map-widget" onClick={() => setIsModalOpen(true)}><GameMap seed={session.seed} mapSnapshot={session.map_snapshot} onSnapshotChange={saveMapSnapshot} /></div>
      <div className={`modal-overlay ${isModalOpen ? 'active' : ''}`} onClick={() => setIsModalOpen(false)}>
        <div className="modal-content" onClick={(event) => event.stopPropagation()}>
          <button className="modal-close" onClick={() => setIsModalOpen(false)}><i className="fa-solid fa-xmark"></i></button>
          {isModalOpen && <GameMap seed={session.seed} mapSnapshot={session.map_snapshot} onSnapshotChange={saveMapSnapshot} />}
        </div>
      </div>
    </>
  );
}
