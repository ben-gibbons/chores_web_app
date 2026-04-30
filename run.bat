@echo off
pushd "%~dp0"
call npm --prefix frontend run build || goto :error
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
popd
exit /b 0

:error
echo Build failed.
popd
exit /b 1
