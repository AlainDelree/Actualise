; Installeur InnoSetup pour Actualise-Setup.exe (issue #44).
;
; Actualise est une instance UNIQUE partagée entre toutes les applications
; cibles (Scrabble, Rummikub, ...), installée dans C:\Actualise\ — voir
; INTEGRATION.md, section 2 "Architecture générale". Jusqu'ici Actualise
; était embarqué dans les setups Scrabble/Rummikub ; ce setup l'installe
; désormais séparément. Chaque application cible garde son propre setup,
; qui dépose uniquement son config_<nom>.json dans C:\Actualise\ (voir
; INTEGRATION.md, §3) — il ne réinstalle plus Actualise.exe lui-même.
;
; Pas de raccourci ici : Actualise est lancé par les jeux via
; "Actualise.exe --config <nom>", jamais directement par l'utilisateur
; (voir INTEGRATION.md, §3 "Raccourci").
;
; Compilation : ISCC installeur\actualise.iss /DActualiseVersion=<N>
; (voir build\rebuild_actualise_setup.bat). Sans /D, repli sur 9 — dernier
; build publié au moment de l'écriture de ce script (voir version.json).

#ifndef ActualiseVersion
  #define ActualiseVersion "9"
#endif

; Staging local CCW (même pattern que build\rebuild_actualise.bat et
; Scrabble/Rummikub) : PyInstaller/ISCC ne doivent jamais tourner
; directement sur le partage VirtualBox (\\VBOXSVR\...).
#define ActualiseSourceDir "C:\Temp\ActualiseBuild\dist\Actualise"
#define ActualiseUISourceDir "C:\Temp\ActualiseBuild\dist\ActualiseUI"

[Setup]
AppId={{8556F922-AD4A-4E8D-A7E9-08AD815D5552}
AppName=Actualise
AppVersion={#ActualiseVersion}
AppPublisher=Alain Delree
; Dossier partagé fixe, jamais un dossier par application cible (voir
; INTEGRATION.md, §3 "Dossier Actualise partagé") — pas de choix laissé à
; l'utilisateur, DisableDirPage=yes.
DefaultDirName=C:\Actualise
DisableDirPage=yes
DisableProgramGroupPage=yes
; C:\ est inaccessible en écriture aux utilisateurs standards ; admin est
; requis pour créer/écrire C:\Actualise\ (voir INTEGRATION.md, §3 "Droits
; d'installation" — incident réel documenté avec PrivilegesRequired=lowest).
PrivilegesRequired=admin
OutputDir=output
OutputBaseFilename=Actualise-Setup-v{#ActualiseVersion}
Compression=lzma
SolidCompression=yes

[Files]
Source: "{#ActualiseSourceDir}\Actualise.exe"; DestDir: "{app}"; Flags: ignoreversion
; Dossier _internal complet, jamais l'exe seul (incident réel documenté :
; "Failed to load Python DLL" si _internal\ manque — voir INTEGRATION.md).
Source: "{#ActualiseSourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ActualiseUISourceDir}\ActualiseUI.exe"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\attente"

[Code]
// config_actualise.json est une instance PARTAGÉE entre toutes les
// applications cibles (voir INTEGRATION.md, §4) : ne jamais l'écraser si
// une autre application l'a déjà créé, sous peine de perdre son
// build_installe / zone_attente déjà à jour.
procedure CurStepChanged(CurStep: TSetupStep);
var
  CheminConfig: string;
  Contenu: string;
begin
  if CurStep = ssPostInstall then
  begin
    CheminConfig := ExpandConstant('{app}\config_actualise.json');
    if not FileExists(CheminConfig) then
    begin
      Contenu := '{"build_installe": {#ActualiseVersion}, "depot_github": "AlainDelree/Actualise", "zone_attente": "C:\\Actualise\\attente\\"}';
      SaveStringToFile(CheminConfig, Contenu, False);
    end;
  end;
end;

// Vrai si un config_<nom>.json d'une AUTRE application cible subsiste
// encore dans {app} (config_actualise.json exclu de la recherche).
function AutresConfigsPresents(): Boolean;
var
  FindRec: TFindRec;
  Trouve: Boolean;
begin
  Trouve := False;
  if FindFirst(ExpandConstant('{app}\config_*.json'), FindRec) then
  begin
    try
      repeat
        if CompareText(FindRec.Name, 'config_actualise.json') <> 0 then
          Trouve := True;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
  Result := Trouve;
end;

// C:\Actualise\ ne doit être retiré que si aucune autre application cible
// n'y a encore de config_<nom>.json (même logique que Scrabble/Rummikub) :
// sinon on désinstallerait Actualise sous des applications qui en
// dépendent encore.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if not AutresConfigsPresents() then
    begin
      DeleteFile(ExpandConstant('{app}\config_actualise.json'));
      DelTree(ExpandConstant('{app}\attente'), True, True, True);
      RemoveDir(ExpandConstant('{app}'));
    end;
  end;
end;
