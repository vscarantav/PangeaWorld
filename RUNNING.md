# Running PangeaWorld locally

From the project root, run:

```powershell
.\start-game.ps1
```

The launcher starts the backend and frontend, configures the frontend to use the backend automatically, and prints the URLs. Press `Ctrl+C` in the launcher terminal to stop both servers.

If PowerShell blocks local scripts for the current session, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-game.ps1
```

The browser keeps the active session ID so refreshing the page reloads the same
game and map snapshot. To deliberately start a fresh local game, open the
browser developer console and run:

```js
localStorage.removeItem('pangeaworld.sessionId');
```
