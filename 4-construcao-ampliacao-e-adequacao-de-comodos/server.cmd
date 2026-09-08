@echo off
cd /d "%~dp0"
ontobdc server --container . --host 127.0.0.1 --port 8080
