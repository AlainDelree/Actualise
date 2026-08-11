@echo off
setlocal enabledelayedexpansion
pushd "%~dp0.."
set "ORIGDIR=%CD%"

echo ============================================
echo   Rebuild Actualise-Setup.exe
echo ============================================
echo.

REM --- 1. Copier les sources vers un repertoire local de la VM ---------------
REM Staging local IMPERATIF (meme raison que rebuild_actualise.bat, issue
REM #297) : PyInstaller/ISCC produisent des resultats corrompus quand ils
REM tournent directement sur le partage VirtualBox (\\VBOXSVR\...). On copie
REM donc tout ce qui est necessaire vers un dossier local
REM (C:\Temp\ActualiseBuild), on construit et on compile l'installeur
REM entierement la-bas, puis on ne recopie vers le partage QUE le setup final
REM (installeur\output\Actualise-Setup-v<N>.exe).
echo [1/8] Copie des sources vers le repertoire de build local...
set "LOCALBUILD=C:\Temp\ActualiseBuild"
if exist "%LOCALBUILD%" (
    echo Nettoyage de l'ancien repertoire de build local...
    rmdir /s /q "%LOCALBUILD%"
)
mkdir "%LOCALBUILD%"
if errorlevel 1 (
    echo.
    echo ERREUR : impossible de creer %LOCALBUILD%.
    echo Rappel ^(issue #328^) : ce chemin doit figurer dans le PERIMETRE de
    echo configs\ccw.conf pour que CCW puisse y ecrire.
    popd
    exit /b 1
)
robocopy "%ORIGDIR%" "%LOCALBUILD%" /E /XD ".git" "venv" ".venv_build" "dist" "build" "__pycache__" ".pytest_cache" "logs" "installeur\output" /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 (
    echo.
    echo ERREUR : la copie des sources vers %LOCALBUILD% a echoue.
    popd
    exit /b 1
)
echo Sources copiees vers %LOCALBUILD%. OK.
echo.

pushd "%LOCALBUILD%"

REM --- 2. Preparer l'environnement virtuel de build -------------------------
echo [2/8] Verification de l'environnement virtuel de build...
if not exist ".venv_build\Scripts\python.exe" (
    echo .venv_build introuvable : creation en cours...
    python -m venv .venv_build
    if errorlevel 1 (
        echo.
        echo ERREUR : impossible de creer .venv_build. Verifiez l'installation Python.
        popd
        popd
        exit /b 1
    )
    call ".venv_build\Scripts\python.exe" -m pip install --upgrade pip >nul
    call ".venv_build\Scripts\pip.exe" install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERREUR : l'installation de requirements.txt a echoue.
        popd
        popd
        exit /b 1
    )
    call ".venv_build\Scripts\pip.exe" install pyinstaller
    if errorlevel 1 (
        echo.
        echo ERREUR : l'installation de pyinstaller a echoue.
        popd
        popd
        exit /b 1
    )
) else (
    echo .venv_build present. OK.
)
echo.

REM --- 3. Fermer Actualise.exe / ActualiseUI.exe s'ils tournent encore ------
echo [3/8] Fermeture d'Actualise.exe / ActualiseUI.exe si necessaire...
tasklist /fi "imagename eq Actualise.exe" 2>nul | find /i "Actualise.exe" >nul
if not errorlevel 1 (
    echo Actualise.exe est en cours d'execution : fermeture...
    taskkill /im Actualise.exe /f >nul 2>&1
)
tasklist /fi "imagename eq ActualiseUI.exe" 2>nul | find /i "ActualiseUI.exe" >nul
if not errorlevel 1 (
    echo ActualiseUI.exe est en cours d'execution : fermeture...
    taskkill /im ActualiseUI.exe /f >nul 2>&1
)
timeout /t 2 >nul
echo.

REM --- 4. Build PyInstaller : Actualise.exe ---------------------------------
echo [4/8] Build PyInstaller Actualise.exe en cours...
call ".venv_build\Scripts\pyinstaller.exe" actualise.spec -y
if errorlevel 1 (
    echo.
    echo ERREUR : le build PyInstaller d'Actualise.exe a echoue.
    popd
    popd
    exit /b 1
)
echo.

REM --- 5. Build PyInstaller : ActualiseUI.exe -------------------------------
echo [5/8] Build PyInstaller ActualiseUI.exe en cours...
call ".venv_build\Scripts\pyinstaller.exe" actualise_ui.spec -y
if errorlevel 1 (
    echo.
    echo ERREUR : le build PyInstaller d'ActualiseUI.exe a echoue.
    popd
    popd
    exit /b 1
)
echo.
echo Builds PyInstaller termines avec succes.
echo.

REM --- 6. Verifier les deux executables produits ----------------------------
echo [6/8] Verification des executables generes...
if not exist "dist\Actualise\Actualise.exe" (
    echo.
    echo ERREUR : Actualise.exe introuvable dans dist\Actualise apres le build.
    popd
    popd
    exit /b 1
)
if not exist "dist\ActualiseUI.exe" (
    echo.
    echo ERREUR : ActualiseUI.exe introuvable dans dist apres le build.
    popd
    popd
    exit /b 1
)
echo dist\Actualise\Actualise.exe et dist\ActualiseUI.exe presents. OK.
echo.

REM --- 7. Compiler l'installeur InnoSetup ------------------------------------
REM ActualiseVersion en dur a 9 pour l'instant (sera dynamise plus tard,
REM voir issue #44) : valeur du dernier build publie (voir version.json).
echo [7/8] Compilation de l'installeur InnoSetup (ISCC)...
set "ISCC=ISCC"
where ISCC >nul 2>&1
if errorlevel 1 (
    if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
        set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    ) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
        set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
    ) else if exist "C:\.tools\InnoSetup6\ISCC.exe" (
        set "ISCC=C:\.tools\InnoSetup6\ISCC.exe"
    ) else (
        echo.
        echo ERREUR : ISCC.exe introuvable ^(ni sur le PATH, ni dans
        echo "Program Files\Inno Setup 6", ni dans C:\.tools\InnoSetup6^).
        echo Verifiez l'installation d'Inno Setup.
        popd
        popd
        exit /b 1
    )
)
"%ISCC%" "installeur\actualise.iss" /DActualiseVersion=9
if errorlevel 1 (
    echo.
    echo ERREUR : la compilation ISCC a echoue. Voir les messages ci-dessus.
    popd
    popd
    exit /b 1
)
if not exist "installeur\output\Actualise-Setup-v9.exe" (
    echo.
    echo ERREUR : Actualise-Setup-v9.exe introuvable dans installeur\output
    echo apres compilation ISCC.
    popd
    popd
    exit /b 1
)
echo Installeur compile avec succes : installeur\output\Actualise-Setup-v9.exe
echo.

REM --- 8. Recopier le setup vers le partage, nettoyer le local --------------
echo [8/8] Recopie du setup vers le partage et nettoyage...
robocopy "installeur\output" "%ORIGDIR%\installeur\output" "Actualise-Setup-v9.exe" /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 (
    echo.
    echo ERREUR : la recopie du setup vers le partage a echoue.
    popd
    popd
    exit /b 1
)
echo [OK] installeur\output\Actualise-Setup-v9.exe copie vers %ORIGDIR%\installeur\output\

popd
rmdir /s /q "%LOCALBUILD%"
echo [OK] Repertoire de build local nettoye ^(%LOCALBUILD%^)
echo.
echo ============================================
echo   REBUILD TERMINE AVEC SUCCES
echo ============================================
echo.
echo Rappel : testez Actualise-Setup-v9.exe sur une VM propre avant toute
echo publication ^(Release GitHub ou distribution manuelle^).
echo.
popd
exit /b 0
