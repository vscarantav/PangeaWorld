import React, { useState } from 'react';

export default function SupplyChainMap() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <div 
        className="map-widget"
        onClick={() => setIsModalOpen(true)}
      >
        <iframe 
          src="/map_prototype.html" 
          className="map-iframe"
          title="Supply Chain Map Preview"
        />
        <div className="map-overlay">
          <i className="fa-solid fa-maximize"></i>
          <span>Expand Map</span>
        </div>
      </div>

      {/* Expanded Modal */}
      <div className={`modal-overlay ${isModalOpen ? 'active' : ''}`} onClick={() => setIsModalOpen(false)}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <button className="modal-close" onClick={() => setIsModalOpen(false)}>
            <i className="fa-solid fa-xmark"></i>
          </button>
          {isModalOpen && (
            <iframe 
              src="/map_prototype.html" 
              className="modal-iframe"
              title="Full Supply Chain Map"
            />
          )}
        </div>
      </div>
    </>
  );
}
