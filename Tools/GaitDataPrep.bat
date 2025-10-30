@echo off
setlocal EnableExtensions DisableDelayedExpansion

REM =========================================================
REM ExportGAR.bat
REM Usage:
REM   ExportGAR.bat "C:\Projects\MyProj.cmz" "C:\Scripts\SubScript.v3s"
REM =========================================================

if "%~1"=="" goto :USAGE
if "%~2"=="" goto :USAGE

set "PROJECT=%~1"
set "CALLSCRIPT=%~2"

REM 1) get dir of CMZ
set "PROJ_DIR=%~dp1"

REM 2) ensure Export dir exists
set "EXPORT_DIR=%PROJ_DIR%Export"
if not exist "%EXPORT_DIR%" (
    mkdir "%EXPORT_DIR%"
)

REM 3) build temp pipeline
set "TEMPFILE=%TEMP%\_AutoRun.v3s"
> "%TEMPFILE%" echo File_New
>>"%TEMPFILE%" echo ;
>>"%TEMPFILE%" echo.
>>"%TEMPFILE%" echo File_Open
>>"%TEMPFILE%" echo /FILE_NAME=%PROJECT%
>>"%TEMPFILE%" echo ! /FILE_PATH=
>>"%TEMPFILE%" echo ! /SEARCH_SUBFOLDERS=FALSE
>>"%TEMPFILE%" echo ! /SUFFIX=
>>"%TEMPFILE%" echo ! /SET_PROMPT=File_Open
>>"%TEMPFILE%" echo ! /ON_FILE_NOT_FOUND=PROMPT
>>"%TEMPFILE%" echo ! /FILE_TYPES_ON_PROMPT=
>>"%TEMPFILE%" echo ;
>>"%TEMPFILE%" echo.
>>"%TEMPFILE%" echo Call_Script
>>"%TEMPFILE%" echo /SCRIPT_FILE_NAME=%CALLSCRIPT%
>>"%TEMPFILE%" echo ! /SCRIPT_PATH=
>>"%TEMPFILE%" echo ;
>>"%TEMPFILE%" echo.
>>"%TEMPFILE%" echo Exit_Workspace
>>"%TEMPFILE%" echo ;

REM 4) run Visual3D
set "V3D_EXE=C:\Program Files\Visual3D x64\Visual3D.exe"
echo Running Visual3D...
"%V3D_EXE%" -s "%TEMPFILE%"
set "V3D_RC=%ERRORLEVEL%"

echo Visual3D finished with code %V3D_RC%.

REM 5) zip Export folder 
echo Zipping "%EXPORT_DIR%" ...
pushd "%EXPORT_DIR%"
tar -a -c -f "%PROJ_DIR%GaitData.zip" *
popd

REM OPTIONAL: delete original files after zipping
rmdir /s /q "%EXPORT_DIR%"
mkdir "%EXPORT_DIR%"

echo Done.
exit /b 0

:USAGE
echo Usage:
echo   %~nx0 "C:\Path\Project.cmz" "C:\Path\SubScript.v3s"
exit /b 1
