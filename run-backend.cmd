@echo off
rem Starts the Django backend for local testing at http://127.0.0.1:8000
rem Run it in its own terminal window, and start run-frontend.cmd in another.
rem Developer mode is on (test accounts, sample menus). Emails are printed here, never sent.
cd /d "%~dp0"
set DJANGO_DEBUG=true
set DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
echo Checking the database...
".venv\Scripts\python.exe" manage.py migrate --noinput
echo.
echo Backend: http://127.0.0.1:8000   (press Ctrl+C to stop)
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
