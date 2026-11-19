@echo off
rem Starts the React frontend for local testing. Open http://localhost:5173 in the browser.
rem Run it in its own terminal window, after run-backend.cmd is running in another.
cd /d "%~dp0frontend"
echo Frontend: http://localhost:5173   (press Ctrl+C to stop)
npm run dev
