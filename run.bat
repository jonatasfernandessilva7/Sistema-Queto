@echo off
echo ola, teste

cd src\backend

uvicorn server:app --reload --host 0.0.0.0 --port 8000