@echo off
for %%P in (8010 5173 5174) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>nul
)
echo stopped
