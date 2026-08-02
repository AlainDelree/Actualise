@echo off
setlocal enabledelayedexpansion
pushd "%~dp0.."
set "ORIGDIR=%CD%"

echo ============================================
echo   Rebuild Actualise.exe
echo ============================================
echo.

REM --- 1. Copier les sources vers un repertoire local de la VM ---------------
REM Staging local IMPERATIF (issue #297) : PyInstaller produit des fichiers
REM tronques quand le build tourne directement sur le partage VirtualBox
REM (\\VBOXSVR\...). On copie donc tout ce qui est necessaire au build vers un
REM dossier local (C:\Temp\ActualiseBuild), on construit entierement la-bas,
REM puis on ne recopie vers le partage QUE le dossier dist\Actualise\ final
REM (pas d'installeur : Actualise se distribue en dist\ nu via Release
REM GitHub, voir issue #328).
echo [1/5] Copie des sources vers le repertoire de build local...
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
robocopy "%ORIGDIR%" "%LOCALBUILD%" /E /XD ".git" "venv" ".venv_build" "dist" "build" "__pycache__" ".pytest_cache" "logs" /NFL /NDL /NJH /NJS /NC /NS /NP >nul
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
echo [2/5] Verification de l'environnement virtuel de build...
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

REM --- 3. Fermer Actualise.exe s'il tourne encore ---------------------------
echo [3/5] Fermeture d'Actualise.exe si necessaire...
tasklist /fi "imagename eq Actualise.exe" 2>nul | find /i "Actualise.exe" >nul
if not errorlevel 1 (
    echo Actualise.exe est en cours d'execution : fermeture...
    taskkill /im Actualise.exe /f >nul 2>&1
    timeout /t 2 >nul
) else (
    echo Aucune instance en cours. OK.
)
echo.

REM --- 4. Lancer le build PyInstaller ---------------------------------------
echo [4/5] Build PyInstaller en cours (peut prendre plusieurs minutes)...
call ".venv_build\Scripts\pyinstaller.exe" actualise.spec -y
if errorlevel 1 (
    echo.
    echo ERREUR : le build PyInstaller a echoue. Voir les messages ci-dessus.
    popd
    popd
    exit /b 1
)
echo.
echo Build termine avec succes.
echo.

REM --- 5. Verifier le resultat, recopier vers le partage, nettoyer le local --
echo [5/5] Verification du resultat et recopie vers le partage...
if exist "dist\Actualise\Actualise.exe" (
    echo.
    echo dist\Actualise\ genere :
    dir "dist\Actualise" | find "Actualise.exe"
    echo.
    for /f "usebackq" %%s in (`powershell -NoProfile -Command "'{0:N2} Mo' -f ((Get-ChildItem -Recurse 'dist\Actualise' | Measure-Object -Property Length -Sum).Sum / 1MB)"`) do (
        echo Taille totale du dossier dist\Actualise : %%s
    )
    echo.
) else (
    echo.
    echo ERREUR : Actualise.exe introuvable dans dist\Actualise apres le build.
    popd
    popd
    exit /b 1
)

echo Recopie de dist\Actualise\ vers le partage (pas d'installeur, distribution
echo en dossier nu via Release GitHub, voir issue #328)...
robocopy "dist\Actualise" "%ORIGDIR%\dist\Actualise" /MIR /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 (
    echo.
    echo ERREUR : la recopie de dist\Actualise vers le partage a echoue.
    popd
    popd
    exit /b 1
)
echo [OK] dist\Actualise\ copie vers %ORIGDIR%\dist\Actualise\

popd
rmdir /s /q "%LOCALBUILD%"
echo [OK] Repertoire de build local nettoye ^(%LOCALBUILD%^)
echo.
echo dist\Actualise\Actualise.exe genere.
echo.
echo ============================================
echo   REBUILD TERMINE AVEC SUCCES
echo ============================================
echo.
echo Rappel : lancez Actualise.exe --help (ou equivalent) vous-meme depuis
echo cette session interactive pour verifier qu'il demarre sans crash immediat
echo avant toute publication en Release GitHub.
echo.
popd
exit /b 0
