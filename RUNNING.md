# Running PangeaWorld locally

From the project root, run:

```powershell
.\start-game.ps1
```

On a fresh checkout, install the backend and frontend dependencies first:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
Set-Location frontend
npm install
Set-Location ..
```

The launcher starts the backend and frontend, configures the frontend to use the backend automatically, and prints the URLs. Press `Ctrl+C` in the launcher terminal to stop both servers.

If PowerShell blocks local scripts for the current session, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-game.ps1
```

The browser keeps the active session ID so refreshing the page reloads the same
game and hydrates the canonical React map from the persisted snapshot. The
standalone `/map_prototype.html` page is a design reference only and is not
used by a real game. To deliberately start a fresh local game, open the
browser developer console and run:

```js
localStorage.removeItem('pangeaworld.sessionId');
```

The first registered local account becomes the instructor. Existing Phase 1
games appear as recoverable games on that instructor's welcome screen; mapless
legacy games are returned to a lobby and receive a new validated map before
they can restart.

## Multiplayer setup and accelerated deadlines

1. Register or sign in as the instructor, select a phase deadline, and choose
   **Create instructor game**. The normal setting is 48 hours; 5 minutes and
   30 seconds are available for local testing, and 5 seconds is reserved for
   automated acceptance testing.
2. Open four separate browser profiles or private contexts. Register each
   player and join with the instructor's code.
3. Assign two President seats and two Company Executive seats across two
   nations, then start the game.
4. Wait for each dashboard to show **Live**. Phase, assignment, readiness, and
   result notifications carry identifiers only; each browser reloads canonical
   game state from the authenticated REST API.

Late decision and draft writes are rejected by the server. When the instructor
advances an expired decision phase, missing assigned seats receive conservative
automatic decisions recorded as `automatic (deadline missed)`. Repeated or
simultaneous phase-advance requests are idempotent and cannot process a round
twice.

If a client disconnects, it shows **Reconnecting…**, retries the WebSocket every
two seconds, and continues polling authoritative state every 15 seconds. A
successful reconnect immediately reloads canonical state. Reloading the page is
also safe; authentication, membership, role, phase, and persisted React map are
restored from the server.

To run the isolated four-browser acceptance path with the installed Chrome:

```powershell
Set-Location frontend
npm run test:e2e
```
