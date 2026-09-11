import React, { useCallback, useEffect, useState } from 'react';
import * as api from '../../api/client';

export default function BackfillPanel({ sessionId, phase }) {
  const [data, setData] = useState(null); const [message, setMessage] = useState('');
  const load = useCallback(() => api.getBackfillStatus(sessionId).then(setData).catch((err) => setMessage(err.message)), [sessionId]);
  useEffect(() => { load(); }, [load, phase]);
  const takeOver = async (seatId, userId) => { try { await api.takeOverBackfill(sessionId, seatId, Number(userId)); setMessage('Human takeover recorded; automatic backfill stops immediately.'); load(); } catch (err) { setMessage(err.message); } };
  return <details><summary>AI seat backfill</summary>{message && <p>{message}</p>}{!data ? <p>Loading seats…</p> : <><p>{data.note}</p><table><thead><tr><th>Seat</th><th>Control</th><th>Take over</th></tr></thead><tbody>{data.seats.map((seat) => <tr key={seat.seat_id}><td>{seat.role} · {seat.name}</td><td>{seat.control === 'ai' ? 'AI-controlled' : 'Human-controlled'}</td><td>{seat.control === 'ai' && <select defaultValue="" onChange={(event) => event.target.value && takeOver(seat.seat_id, event.target.value)}><option value="">Assign waiting player…</option>{data.eligible_members.map((member) => <option value={member.user_id} key={member.user_id}>{member.display_name}</option>)}</select>}</td></tr>)}</tbody></table></>}</details>;
}
