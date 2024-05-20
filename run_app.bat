@echo off

rem Run server.py in a separate PowerShell window with administrative privileges
echo Running server.py with administrative privileges...
powershell -Command "Start-Process 'python' -ArgumentList 'C:\Users\Roy\Documents\Supervise\Server\server.pyw' -Verb RunAs"

rem Run client_app.py in a separate command prompt window (hidden)
echo Running client_app.py with administrative privileges...
start /min cmd /c "cd C:\Users\Roy\Documents\Supervise\Client\ && pythonw client_app.py"

:prompt
echo.
echo What would you like to do next?
echo 1. Re-run the client
echo 2. Run another client simultaneously
echo 3. Exit

set /p choice="Enter your choice (1/2/3): "

if "%choice%"=="1" goto run_client
if "%choice%"=="2" goto run_client
if "%choice%"=="3" goto exit_script
echo Invalid choice. Please try again.
goto prompt

:run_client
rem Run client_app.py in a separate command prompt window (hidden)
echo Running client_app.py with administrative privileges...
start /min cmd /c "cd C:\Users\Roy\Documents\Supervise\Client\ && pythonw client_app.py"
goto prompt

:exit_script
rem Terminate the PowerShell process running the server
echo Terminating server process...
taskkill /f /fi "windowtitle eq Administrator:  python C:\Users\Roy\Documents\Supervise\Server\server.py"
rem Terminate the PowerShell window with the admin rights
echo Terminating PowerShell with admin rights...
taskkill /f /fi "windowtitle eq Administrator:  Command Prompt"
rem Terminate all Python processes running the clients
echo Terminating client processes...
taskkill /f /fi "imagename eq pythonw.exe"
echo Exiting script...
exit /b
