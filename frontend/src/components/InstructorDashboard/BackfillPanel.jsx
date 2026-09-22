import React, { useCallback, useEffect, useState } from 'react';
import { Bot, UserRoundCog } from 'lucide-react';
import * as api from '../../api/client';
import { useSessionEvents } from '../../hooks/useSessionEvents';

export default function BackfillPanel({ sessionId, phase }) {
  const [data, setData] = useState(null); const [message, setMessage] = useState('');
  const load = useCallback(() => api.getBackfillStatus(sessionId).then(setData).catch((err) => setMessage(err.message)), [sessionId]);
  useEffect(() => { load(); }, [load, phase]);
  useSessionEvents(sessionId, load);
  const takeOver = async (seatId, userId) => { try { await api.takeOverBackfill(sessionId, seatId, Number(userId)); setMessage('Human takeover recorded; automatic backfill stops immediately.'); load(); } catch (err) { setMessage(err.message); } };
  return <details className="instructor-panel instructor-control-panel"><summary><span className="instructor-summary-icon"><Bot aria-hidden="true" /></span><span><small>Seat management</small><strong>AI seat backfill</strong></span></summary><div className="instructor-panel-body">
    {message && <p className="instructor-form-message">{message}</p>}{!data ? <div className="instructor-loading"><span /><p>Loading seats…</p></div> : <><p className="backfill-note">{data.note}</p><div className="backfill-list">{data.seats.map((seat) => <div className="backfill-seat" key={seat.seat_id}><span><UserRoundCog aria-hidden="true" /></span><div><strong>{seat.role} · {seat.name}</strong><small>{seat.control === 'ai' ? 'AI-controlled' : 'Human-controlled'}</small></div>{seat.control === 'ai' && <select defaultValue="" onChange={(event) => event.target.value && takeOver(seat.seat_id, event.target.value)}><option value="">Take over…</option>{data.eligible_members.map((member) => <option value={member.user_id} key={member.user_id}>{member.display_name}</option>)}</select>}</div>)}</div></>}
  </div></details>;
}
