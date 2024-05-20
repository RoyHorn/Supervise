@echo off

rem Run server.py in a separate PowerShell window with administrative privileges
echo Running server.py with administrative privileges...
powershell -Command "Start-Process 'python' -ArgumentList 'C:\Users\Roy\Documents\Supervise\Server\server.pyw' -Verb RunAs"