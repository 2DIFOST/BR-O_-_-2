@echo off
set PYTHONPATH=%~dp0src
where py >nul 2>&1
if %errorlevel%==0 (
    py -m depgraph %*
) else (
    python -m depgraph %*
)
