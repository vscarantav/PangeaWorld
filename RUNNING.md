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
