@echo off
REM ============================================================================
REM  rebuild_actualise_unifie.bat -- Reconstruction complete d'Actualise
REM  (Windows), sur le modele de build\rebuild_rummikub.bat (issue #67).
REM
REM  Nom PROVISOIRE : le nom final rebuild_actualise.bat est deja pris par le
REM  script a conserver (voir build\rebuild_actualise.bat) ; le renommage sera
REM  une issue ulterieure. Ce script ne remplace pour l'instant aucun des
REM  trois scripts existants (rebuild_actualise.bat, rebuild_actualise_setup.bat,
REM  publier_actualise.bat), conserves sans modification.
REM
REM  10 etapes (0 a 9) :
REM    0. Localiser ISCC.exe (Inno Setup 6)
REM    1. Determiner le numero de build (version.json + 1, ou --build N)
REM    2. Copier le projet vers C:\Temp\ActualiseBuild
REM    3. Environnement virtuel .venv_build + dependances
REM    4. Signaler (sans les arreter) Actualise.exe / ActualiseUI.exe en cours
REM    5. PyInstaller (actualise.spec puis actualise_ui.spec)
REM    6. Verifier dist\Actualise\Actualise.exe + dist\ActualiseUI.exe + tailles
REM    7. ISCC (installeur Actualise-Setup-v<N>.exe) + copie vers le worktree
REM    8. manifest.json + archive actualise-v<N>.zip + copie vers le worktree
REM    9. Copie vers le dossier fixe, --publier (version.json + commit), nettoyage
REM ============================================================================
setlocal EnableExtensions EnableDelayedExpansion

REM --- Analyse des arguments ------------------------------------------------
REM  Sans argument : construit les 4 artefacts (Actualise.exe, ActualiseUI.exe,
REM  l'installeur et l'archive) mais n'ecrit jamais version.json et ne commite
REM  rien.
REM  --publier      : en plus de la construction, met a jour version.json
REM                   (build + SHA-256 de l'archive FINALE) et fait un commit
REM                   local dans le worktree. Jamais de git push ni de
REM                   gh release create (etapes manuelles, cf. rappel final).
REM  --build N      : force le numero de build (sinon = build de version.json
REM                   + 1). S'applique a l'installeur, a l'archive, au
REM                   manifeste et a version.json, quel que soit le mode.
set "PUBLIER=0"
set "BUILD_OVERRIDE="
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--publier" ( set "PUBLIER=1" & shift /1 & goto parse_args )
if /i "%~1"=="--build" ( set "BUILD_OVERRIDE=%~2" & shift /1 & shift /1 & goto parse_args )
echo [ATTENTION] Argument inconnu ignore : %~1
shift /1
goto parse_args
:args_done

REM --- Racine du depot = dossier parent de ce .bat (build\ -> ..) -----------
pushd "%~dp0.." || (echo [ERREUR] Impossible d'atteindre la racine du projet. & exit /b 1)
set "ORIGDIR=%CD%"
popd

set "BUILDDIR=C:\Temp\ActualiseBuild"
set "FIXEDSHARE=C:\CCW_Share\_derniers_builds\actualise"

echo ============================================================================
echo   Reconstruction d'Actualise
echo   Projet source : %ORIGDIR%
echo ============================================================================

REM ===========================================================================
REM  ETAPE 0 : localiser ISCC.exe
REM  Ordre de recherche (issue #67) : C:\CCW\tools\InnoSetup6 (installe hors
REM  des depots, accessible depuis n'importe quel worktree) ; puis les
REM  emplacements deja utilises par rebuild_actualise_setup.bat (PATH, Program
REM  Files (x86)/Program Files, C:\.tools\InnoSetup6) ; puis .tools\InnoSetup6
REM  du depot lui-meme (comme Rummikub), absent dans un worktree frais.
REM ===========================================================================
echo.
echo [0/9] Recherche de ISCC.exe (Inno Setup 6)...
set "ISCC="
if exist "C:\CCW\tools\InnoSetup6\ISCC.exe" (
    set "ISCC=C:\CCW\tools\InnoSetup6\ISCC.exe"
) else (
    where ISCC >nul 2>&1
    if not errorlevel 1 (
        set "ISCC=ISCC"
    ) else if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
        set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    ) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
        set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
    ) else if exist "C:\.tools\InnoSetup6\ISCC.exe" (
        set "ISCC=C:\.tools\InnoSetup6\ISCC.exe"
    ) else if exist "%ORIGDIR%\.tools\InnoSetup6\ISCC.exe" (
        set "ISCC=%ORIGDIR%\.tools\InnoSetup6\ISCC.exe"
    )
)
if not defined ISCC (
    echo [ERREUR] ISCC.exe introuvable dans aucun des emplacements suivants :
    echo            - C:\CCW\tools\InnoSetup6\ISCC.exe
    echo            - PATH ^(where ISCC^)
    echo            - %ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
    echo            - %ProgramFiles%\Inno Setup 6\ISCC.exe
    echo            - C:\.tools\InnoSetup6\ISCC.exe
    echo            - %ORIGDIR%\.tools\InnoSetup6\ISCC.exe
    echo          Installez Inno Setup 6 dans l'un de ces emplacements avant de relancer le build.
    exit /b 1
)
echo       ISCC : %ISCC%

REM ===========================================================================
REM  ETAPE 1 : determiner le numero de build
REM ===========================================================================
echo.
echo [1/9] Determination du numero de build...
if not exist "%ORIGDIR%\version.json" (
    echo [ERREUR] version.json introuvable a la racine du depot ^(%ORIGDIR%^).
    exit /b 1
)
set "CURBUILD="
for /f "usebackq delims=" %%B in (`powershell -NoProfile -Command "[int]((ConvertFrom-Json (Get-Content -Raw '%ORIGDIR%\version.json')).build)"`) do set "CURBUILD=%%B"
if not defined CURBUILD (
    echo [ERREUR] Lecture du build courant impossible depuis %ORIGDIR%\version.json
    exit /b 1
)
if defined BUILD_OVERRIDE (
    set "BUILD=%BUILD_OVERRIDE%"
    echo       Build impose via --build : !BUILD!
) else (
    set /a BUILD=CURBUILD+1
    echo       Build courant ^(version.json^) : %CURBUILD% -- nouveau build : !BUILD!
)

REM ===========================================================================
REM  ETAPE 2 : copie du projet vers le repertoire de build local
REM  Staging local (meme raison que les trois scripts existants) : un build
REM  lance directement dans un dossier partage a produit des fichiers
REM  tronques. On copie donc tout vers un dossier local (%BUILDDIR%), on
REM  construit entierement la, puis on ne recopie vers le worktree QUE les
REM  artefacts finaux (installeur et archive).
REM ===========================================================================
echo.
echo [2/9] Copie du projet vers %BUILDDIR% ...
robocopy "%ORIGDIR%" "%BUILDDIR%" /MIR /XD ".git" "venv" ".venv_build" "dist" "build" "__pycache__" ".pytest_cache" "logs" "installeur\output" /NFL /NDL /NJH /NJS /NC /NS /NP
if errorlevel 8 (
    echo [ERREUR] Echec de la copie du projet vers %BUILDDIR%
    exit /b 1
)
echo       Sources copiees vers %BUILDDIR%. OK.

pushd "%BUILDDIR%" || (echo [ERREUR] Impossible d'atteindre %BUILDDIR% & exit /b 1)

REM ===========================================================================
REM  ETAPE 3 : environnement virtuel de build + dependances
REM ===========================================================================
echo.
echo [3/9] Preparation de l'environnement virtuel .venv_build ...
if not exist ".venv_build\Scripts\python.exe" (
    python -m venv .venv_build
    if errorlevel 1 ( echo [ERREUR] Echec de la creation de .venv_build & popd & exit /b 1 )
)
call ".venv_build\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 ( echo [ERREUR] Echec de la mise a jour de pip & popd & exit /b 1 )
call ".venv_build\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERREUR] Echec de pip install -r requirements.txt & popd & exit /b 1 )
call ".venv_build\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 ( echo [ERREUR] Echec de pip install pyinstaller & popd & exit /b 1 )

REM ===========================================================================
REM  ETAPE 4 : signaler (sans les arreter) Actualise.exe / ActualiseUI.exe
REM  Ce script ne lance jamais Actualise.exe ni ActualiseUI.exe : il ne les
REM  arrete donc jamais de force non plus (contrairement aux trois scripts
REM  existants). Une instance en cours est seulement signalee ici.
REM ===========================================================================
echo.
echo [4/9] Verification des processus en cours (signalement uniquement)...
set "PROCESSUS_DETECTES=0"
tasklist /fi "imagename eq Actualise.exe" 2>nul | find /i "Actualise.exe" >nul
if not errorlevel 1 (
    echo       [ATTENTION] Actualise.exe est en cours d'execution. Ce script ne
    echo       l'arrete pas ^(il ne l'a pas lance^) ; le build continue normalement.
    set "PROCESSUS_DETECTES=1"
)
tasklist /fi "imagename eq ActualiseUI.exe" 2>nul | find /i "ActualiseUI.exe" >nul
if not errorlevel 1 (
    echo       [ATTENTION] ActualiseUI.exe est en cours d'execution. Meme remarque.
    set "PROCESSUS_DETECTES=1"
)
if "%PROCESSUS_DETECTES%"=="0" echo       Aucune instance en cours. OK.

REM ===========================================================================
REM  ETAPE 5 : build PyInstaller (les deux executables)
REM ===========================================================================
echo.
echo [5/9] Construction avec PyInstaller (actualise.spec puis actualise_ui.spec)...
call ".venv_build\Scripts\python.exe" -m PyInstaller actualise.spec -y
if errorlevel 1 ( echo [ERREUR] Echec de PyInstaller ^(actualise.spec^). & popd & exit /b 1 )
call ".venv_build\Scripts\python.exe" -m PyInstaller actualise_ui.spec -y
if errorlevel 1 ( echo [ERREUR] Echec de PyInstaller ^(actualise_ui.spec^). & popd & exit /b 1 )

REM ===========================================================================
REM  ETAPE 6 : verifier les executables produits et mesurer leur taille
REM  Mesures faites ICI, dans le dossier de build local, avant son nettoyage
REM  (l'agent ne liste pas ce dossier : ces valeurs sont affichees en fin de
REM  script, point 10 du contrat de l'issue #67).
REM ===========================================================================
echo.
echo [6/9] Verification des executables generes et mesure des tailles...
if not exist "dist\Actualise\Actualise.exe" (
    echo [ERREUR] dist\Actualise\Actualise.exe introuvable apres le build.
    popd & exit /b 1
)
if not exist "dist\ActualiseUI.exe" (
    echo [ERREUR] dist\ActualiseUI.exe introuvable apres le build.
    popd & exit /b 1
)
set "TAILLE_DIST_ACTUALISE=0"
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "(Get-ChildItem -Recurse -File 'dist\Actualise' | Measure-Object -Sum Length).Sum"`) do set "TAILLE_DIST_ACTUALISE=%%S"
set "TAILLE_ACTUALISEUI=0"
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "(Get-Item 'dist\ActualiseUI.exe').Length"`) do set "TAILLE_ACTUALISEUI=%%S"
echo       dist\Actualise\Actualise.exe present. OK.
echo       dist\ActualiseUI.exe present. OK.
echo       Taille non compressee dist\Actualise ^(dossier^) : %TAILLE_DIST_ACTUALISE% octets
echo       Taille non compressee ActualiseUI.exe             : %TAILLE_ACTUALISEUI% octets

REM ===========================================================================
REM  ETAPE 7 : compiler l'installeur Inno Setup et le recopier vers le worktree
REM  Meme numero de build (%BUILD%) passe a ISCC : il determine le nom de
REM  l'installeur ET le build_installe ecrit dans config_actualise.json a
REM  l'installation (voir installeur\actualise.iss, [Code]).
REM ===========================================================================
echo.
echo [7/9] Compilation de l'installeur avec Inno Setup...
if not exist "installeur\output" mkdir "installeur\output"
"%ISCC%" /DActualiseVersion=%BUILD% "installeur\actualise.iss"
if errorlevel 1 ( echo [ERREUR] Echec de la compilation ISCC. & popd & exit /b 1 )
set "SETUPNAME=Actualise-Setup-v%BUILD%.exe"
if not exist "installeur\output\%SETUPNAME%" (
    echo [ERREUR] %SETUPNAME% introuvable dans installeur\output apres compilation ISCC.
    popd & exit /b 1
)
echo       Installeur compile : installeur\output\%SETUPNAME%
if not exist "%ORIGDIR%\installeur\output" mkdir "%ORIGDIR%\installeur\output"
copy /y "installeur\output\%SETUPNAME%" "%ORIGDIR%\installeur\output\%SETUPNAME%" >nul
if errorlevel 1 ( echo [ERREUR] Echec de la copie de l'installeur vers le worktree. & popd & exit /b 1 )
echo       Copie vers %ORIGDIR%\installeur\output\%SETUPNAME%. OK.

REM ===========================================================================
REM  ETAPE 8 : construire l'archive de self-update et la recopier vers le
REM  worktree. Structure identique a la Release v10 (racine : Actualise.exe,
REM  ActualiseUI.exe, manifest.json sans BOM, dossier _internal). Le manifeste
REM  contient en plus le champ "build" (comme Rummikub et Scrabble) : le
REM  client ne lit que "supprimer", ce n'est pas un ecart.
REM ===========================================================================
echo.
echo [8/9] Construction de l'archive actualise-v%BUILD%.zip...
set "STAGING=%BUILDDIR%\_staging_publication"
if exist "%STAGING%" rmdir /s /q "%STAGING%"
mkdir "%STAGING%"
if errorlevel 1 ( echo [ERREUR] Impossible de creer %STAGING%. & popd & exit /b 1 )
robocopy "dist\Actualise" "%STAGING%" "Actualise.exe" /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 ( echo [ERREUR] Echec de la copie de Actualise.exe vers le staging. & popd & exit /b 1 )
robocopy "dist\Actualise\_internal" "%STAGING%\_internal" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 ( echo [ERREUR] Echec de la copie de _internal vers le staging. & popd & exit /b 1 )
robocopy "dist" "%STAGING%" "ActualiseUI.exe" /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if %errorlevel% geq 8 ( echo [ERREUR] Echec de la copie de ActualiseUI.exe vers le staging. & popd & exit /b 1 )
python -c "import json; json.dump({'build': %BUILD%, 'supprimer': []}, open(r'%STAGING%\manifest.json', 'w', encoding='utf-8'))"
if errorlevel 1 ( echo [ERREUR] Echec de la generation de manifest.json. & popd & exit /b 1 )
set "ZIPNAME=actualise-v%BUILD%.zip"
if exist "installeur\output\%ZIPNAME%" del /f /q "installeur\output\%ZIPNAME%"
powershell -NoProfile -Command "Compress-Archive -Path '%STAGING%\*' -DestinationPath 'installeur\output\%ZIPNAME%' -Force"
if errorlevel 1 ( echo [ERREUR] Echec de la construction de %ZIPNAME%. & popd & exit /b 1 )
if not exist "installeur\output\%ZIPNAME%" ( echo [ERREUR] %ZIPNAME% introuvable apres Compress-Archive. & popd & exit /b 1 )
rmdir /s /q "%STAGING%"
echo       Archive construite : installeur\output\%ZIPNAME%
if not exist "%ORIGDIR%\installeur\output" mkdir "%ORIGDIR%\installeur\output"
copy /y "installeur\output\%ZIPNAME%" "%ORIGDIR%\installeur\output\%ZIPNAME%" >nul
if errorlevel 1 ( echo [ERREUR] Echec de la copie de l'archive vers le worktree. & popd & exit /b 1 )
echo       Copie vers %ORIGDIR%\installeur\output\%ZIPNAME%. OK.

popd

REM ===========================================================================
REM  ETAPE 9 : copie vers le dossier fixe, publication (--publier), nettoyage
REM  Dossier fixe (issue #63 pour le setup, issue #67 pour l'archive) : chemin
REM  identique quel que soit le worktree. Noms reels (SETUPNAME/ZIPNAME),
REM  jamais de nom ni de numero code en dur (decision Alain, issue #67).
REM ===========================================================================
echo.
echo [9/9] Recopie vers %FIXEDSHARE% et finalisation...
if not exist "%FIXEDSHARE%" mkdir "%FIXEDSHARE%"
copy /y "%ORIGDIR%\installeur\output\%SETUPNAME%" "%FIXEDSHARE%\%SETUPNAME%" >nul
if errorlevel 1 ( echo [ERREUR] Echec de la copie de l'installeur vers %FIXEDSHARE%. & exit /b 1 )
copy /y "%ORIGDIR%\installeur\output\%ZIPNAME%" "%FIXEDSHARE%\%ZIPNAME%" >nul
if errorlevel 1 ( echo [ERREUR] Echec de la copie de l'archive vers %FIXEDSHARE%. & exit /b 1 )

set "TAILLE_SETUP_PARTAGE=0"
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "(Get-Item '%FIXEDSHARE%\%SETUPNAME%').Length"`) do set "TAILLE_SETUP_PARTAGE=%%S"
set "TAILLE_ZIP_PARTAGE=0"
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "(Get-Item '%FIXEDSHARE%\%ZIPNAME%').Length"`) do set "TAILLE_ZIP_PARTAGE=%%S"
echo       Copie vers %FIXEDSHARE% terminee.

if not "%PUBLIER%"=="1" goto fin_publier

echo.
echo       Mode --publier : calcul du SHA-256 de l'archive finale et ecriture de version.json...
set "ZIPSHA="
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash '%ORIGDIR%\installeur\output\%ZIPNAME%' -Algorithm SHA256).Hash.ToLower()"`) do set "ZIPSHA=%%H"
if not defined ZIPSHA (
    echo [ERREUR] Calcul du SHA-256 de %ZIPNAME% impossible.
    exit /b 1
)
echo       SHA-256 : %ZIPSHA%
> "%ORIGDIR%\version.json" echo {"build": %BUILD%, "sha256": "%ZIPSHA%"}
echo       version.json ecrit : %ORIGDIR%\version.json
git -C "%ORIGDIR%" add version.json
git -C "%ORIGDIR%" commit -m "Actualise v%BUILD% : version.json (build %BUILD% + SHA-256 de l'archive)" -- version.json
if errorlevel 1 echo       [ATTENTION] git commit n'a rien commite ^(version.json inchange ?^).
:fin_publier

echo.
echo       Nettoyage de %BUILDDIR% ...
rmdir /s /q "%BUILDDIR%"
echo       Repertoire de build local nettoye.

echo.
echo ============================================================================
echo   TERMINE
echo   Installeur : %ORIGDIR%\installeur\output\%SETUPNAME%
echo   Archive    : %ORIGDIR%\installeur\output\%ZIPNAME%
echo ============================================================================
echo.
echo   --- Informations hors du worktree (mesurees par ce script, pas par l'agent) ---
echo   Inno Setup utilise                    : %ISCC%
echo   Taille non compressee dist\Actualise  : %TAILLE_DIST_ACTUALISE% octets
echo   Taille non compressee ActualiseUI.exe : %TAILLE_ACTUALISEUI% octets
echo   Copie vers %FIXEDSHARE% :
echo     %SETUPNAME% : %TAILLE_SETUP_PARTAGE% octets
echo     %ZIPNAME% : %TAILLE_ZIP_PARTAGE% octets
echo.
if "%PUBLIER%"=="1" (
    echo   --- PUBLICATION ^(--publier^) : etapes MANUELLES restantes ---
    echo   version.json a ete mis a jour ^(build %BUILD%, SHA-256 de l'archive^) et
    echo   COMMITE EN LOCAL dans %ORIGDIR%.
    echo.
    echo   Le script ne fait JAMAIS de git push ni de gh release create. A la main :
    echo     1^) git -C "%ORIGDIR%" push
    echo     2^) Creer la Release GitHub ^(tag v%BUILD%^) avec DEUX fichiers attaches :
    echo          - installeur\output\%SETUPNAME%
    echo          - installeur\output\%ZIPNAME%
    echo   ============================================================================
)
endlocal
exit /b 0
