@echo off
setlocal enabledelayedexpansion
pushd "%~dp0.."
set "ORIGDIR=%CD%"

echo ============================================
echo   Publier Actualise (zip de self-update)
echo ============================================
echo.

REM Ce script ne fait QUE construire installeur\output\actualise-v<N>.zip a
REM partir de dist\ (deja recopie sur le partage par
REM rebuild_actualise_setup.bat, issue #62). Il ne relance jamais
REM PyInstaller/ISCC lui-meme. Nommage actualise-v<N>.zip conforme au
REM gabarit lu par actualise.py (_GABARIT_URL_RELEASE), pas au nom
REM actualise_v<N>.zip effectivement uploade a la main sur les Releases
REM precedentes (source du bug corrige par les issues #57/#59).

REM --- 1. Verifications prealables : parametre et version.json courant ------
echo [1/6] Verifications prealables...
if "%~1"=="" (
    echo.
    echo ERREUR : numero de build a publier manquant.
    echo Usage  : publier_actualise.bat ^<numero_de_build^>
    echo Exemple: publier_actualise.bat 11
    popd
    exit /b 1
)
set "BUILD=%~1"
echo %BUILD%| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo.
    echo ERREUR : "%BUILD%" n'est pas un numero de build valide ^(entier positif attendu^).
    popd
    exit /b 1
)

if not exist "version.json" (
    echo.
    echo ERREUR : version.json introuvable a la racine du depot.
    popd
    exit /b 1
)
set "BUILD_ACTUEL="
for /f "usebackq delims=" %%b in (`python -c "import json; print(json.load(open('version.json', encoding='utf-8'))['build'])"`) do set "BUILD_ACTUEL=%%b"
if not defined BUILD_ACTUEL (
    echo.
    echo ERREUR : impossible de lire le champ "build" de version.json.
    popd
    exit /b 1
)
if %BUILD% leq %BUILD_ACTUEL% (
    echo.
    echo ERREUR : le build %BUILD% n'est pas superieur au build deja publie ^(%BUILD_ACTUEL%^).
    echo Indiquez un numero de build strictement superieur a %BUILD_ACTUEL%.
    popd
    exit /b 1
)
echo Build deja publie : %BUILD_ACTUEL%. Build a publier : %BUILD%. OK.
echo.

REM --- 2. Verifier la presence des artefacts de build dans dist\ ------------
echo [2/6] Verification des artefacts de build dans dist\...
if not exist "dist\Actualise\Actualise.exe" (
    echo.
    echo ERREUR : dist\Actualise\Actualise.exe introuvable.
    echo Lancez d'abord build\rebuild_actualise_setup.bat.
    popd
    exit /b 1
)
if not exist "dist\Actualise\_internal\" (
    echo.
    echo ERREUR : dist\Actualise\_internal\ introuvable.
    echo Lancez d'abord build\rebuild_actualise_setup.bat.
    popd
    exit /b 1
)
if not exist "dist\ActualiseUI.exe" (
    echo.
    echo ERREUR : dist\ActualiseUI.exe introuvable.
    echo Lancez d'abord build\rebuild_actualise_setup.bat.
    popd
    exit /b 1
)
echo Artefacts presents ^(Actualise.exe, _internal\, ActualiseUI.exe^). OK.
echo.

REM --- 3. Preparer un staging flat dedie et jetable --------------------------
echo [3/6] Preparation du staging de publication...
set "STAGING=%ORIGDIR%\build\_staging_publication"
if exist "%STAGING%" (
    rmdir /s /q "%STAGING%"
)
mkdir "%STAGING%"
if errorlevel 1 (
    echo.
    echo ERREUR : impossible de creer %STAGING%.
    popd
    exit /b 1
)

REM Copie positive et nominative des 3 seuls elements a publier (jamais de
REM copie large suivie d'exclusion a posteriori). Layout flat : Actualise.exe
REM et _internal\ cote a cote a la racine du staging, pas dans un sous-dossier
REM "Actualise\" (meme layout que l'installation InnoSetup, voir actualise.iss).
robocopy "dist\Actualise" "%STAGING%" "Actualise.exe" /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 (
    echo.
    echo ERREUR : la copie de dist\Actualise\Actualise.exe a echoue.
    popd
    exit /b 1
)
robocopy "dist\Actualise\_internal" "%STAGING%\_internal" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 (
    echo.
    echo ERREUR : la copie de dist\Actualise\_internal\ a echoue.
    popd
    exit /b 1
)
robocopy "dist" "%STAGING%" "ActualiseUI.exe" /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 (
    echo.
    echo ERREUR : la copie de dist\ActualiseUI.exe a echoue.
    popd
    exit /b 1
)
echo Staging pret : %STAGING%
echo.

REM --- 4. Generer manifest.json et construire le zip -------------------------
echo [4/6] Generation de manifest.json...
python -c "import json; json.dump({'build': %BUILD%, 'supprimer': []}, open(r'%STAGING%\manifest.json', 'w', encoding='utf-8'))"
if errorlevel 1 (
    echo.
    echo ERREUR : la generation de manifest.json a echoue.
    rmdir /s /q "%STAGING%"
    popd
    exit /b 1
)
if not exist "%STAGING%\manifest.json" (
    echo.
    echo ERREUR : manifest.json absent du staging apres generation.
    rmdir /s /q "%STAGING%"
    popd
    exit /b 1
)
echo manifest.json genere : {"build": %BUILD%, "supprimer": []}
echo.

echo [5/6] Construction du zip installeur\output\actualise-v%BUILD%.zip...
if not exist "installeur\output" (
    mkdir "installeur\output"
)
set "ZIPPATH=installeur\output\actualise-v%BUILD%.zip"
if exist "%ZIPPATH%" (
    del /f /q "%ZIPPATH%"
)
powershell -NoProfile -Command "Compress-Archive -Path '%STAGING%\*' -DestinationPath '%ZIPPATH%' -Force"
if errorlevel 1 (
    echo.
    echo ERREUR : la construction du zip a echoue.
    rmdir /s /q "%STAGING%"
    popd
    exit /b 1
)
if not exist "%ZIPPATH%" (
    echo.
    echo ERREUR : %ZIPPATH% introuvable apres Compress-Archive.
    rmdir /s /q "%STAGING%"
    popd
    exit /b 1
)
echo [OK] %ZIPPATH% cree.
echo.

REM --- 5. Calculer et afficher le SHA-256 -------------------------------------
echo [6/6] Calcul du SHA-256...
set "SHA256="
for /f "usebackq delims=" %%h in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -Path '%ZIPPATH%').Hash.ToLower()"`) do set "SHA256=%%h"
if not defined SHA256 (
    echo.
    echo ERREUR : impossible de calculer le SHA-256 de %ZIPPATH%.
    rmdir /s /q "%STAGING%"
    popd
    exit /b 1
)

REM --- 6. Nettoyage du staging -------------------------------------------------
rmdir /s /q "%STAGING%"
echo [OK] Staging de publication nettoye.
echo.

echo ============================================
echo   PUBLICATION PREPAREE AVEC SUCCES
echo ============================================
echo.
echo Zip genere : %ZIPPATH%
echo SHA-256    : %SHA256%
echo.
echo A copier dans version.json :
echo {"build": %BUILD%, "sha256": "%SHA256%"}
echo.
echo ------------------------------------------------------------------
echo ETAPES RESTANT VOLONTAIREMENT MANUELLES (non faites par ce script) :
echo ------------------------------------------------------------------
echo 1. Mettre a jour version.json ^(build + sha256 ci-dessus^), commit, puis
echo    git push ^(Alain pousse lui-meme apres verification^).
echo 2. Publier la Release GitHub :
echo    gh release create v%BUILD% %ZIPPATH%
echo.
popd
exit /b 0
