@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build

REM Set Sphinx Options
REM supply graphviz dot path
SET GVDOT_OPT=-D graphviz_dot="C:\Program Files (x86)\Graphviz2.38\bin\dot.exe"
SET SPHINXOPTS=%GVDOT_OPT% %SPHINXOPTS%

REM Copy the README to here

ECHO F | XCOPY /Y ..\README.md README.md

REM Copy other files to here
ECHO F | XCOPY /Y ..\systemd\flfm.service flfm.service
ECHO F | XCOPY /Y ..\nginx\example_nginx.conf example_nginx.conf

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.http://sphinx-doc.org/
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
