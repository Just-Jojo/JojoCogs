@echo off
call .venv\Scripts\activate.bat

if [%1] == [] goto help

REM This allows us to expand variables at execution
setlocal ENABLEDELAYEDEXPANSION

goto %1

:reformat
isort --line-length 90 .
black -l 90 .
exit /B %ERRORLEVEL%

:help
echo Usage:
echo   make ^<command^>
echo.
echo Commands:
echo   reformat                   Reformat all .py files being tracked by git.
REM I may or may not have ripped this off of kreusada's make file so... lol