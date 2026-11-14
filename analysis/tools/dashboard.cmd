@echo off
rem Dashboard stanu dialogow: serwer lokalny z biezacym stanem i strona w przegladarce. Zamkniecie okna konczy serwer.
cd /d "%~dp0..\.."
start "" http://127.0.0.1:47811/
".venv\Scripts\python.exe" -I -m lektor dashboard --serve
