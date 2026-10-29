; Inno Setup script for the MALT Windows installer.
;
; Produces a per-user installer: MALT-Setup-<version>-x64.exe
; Build with:  ISCC.exe /DAppVersion=<version> packaging\windows\malt-installer.iss
; (or via scripts/build-windows.ps1)

#define MyAppName "MALT"
#define MyAppPublisher "MALT contributors"
#define MyAppURL "https://github.com/NacreousDawn596/MALT"
; Paths are relative to this file (packaging\windows), so climb back to the
; repository root for dist/ and the icons directory.
#define RepoRoot "..\.."
#define IconPath "..\icons\malt.ico"
#ifndef AppVersion
  #define AppVersion "0.4.1"
#endif

[Setup]
AppId={{E8D0B0F4-8C62-4C2A-9F5D-2E0C4A7B1D23}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\MALT
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#RepoRoot}\dist
OutputBaseFilename=MALT-Setup-{#AppVersion}-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Per-user installation: no administrator privileges required.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesEnvironment=yes
SetupIconFile={#IconPath}
UninstallDisplayIcon={app}\malt-gui.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addtopath"; Description: "Add MALT to the user PATH"; GroupDescription: "PATH:"

[Files]
Source: "{#RepoRoot}\dist\malt.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#RepoRoot}\dist\malt-gui.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; REPL: a console session kept attached to the terminal.
Name: "{group}\MALT REPL"; Filename: "{app}\malt.exe"; Parameters: "repl"; \
  IconFilename: "{app}\malt.exe"; WorkingDir: "{userdocs}"
; GUI: the Qt6 notebook, launched without a console window.
Name: "{group}\MALT GUI"; Filename: "{app}\malt-gui.exe"; \
  IconFilename: "{app}\malt-gui.exe"; WorkingDir: "{userdocs}"
; CLI entry (falls through to the interactive help).
Name: "{group}\MALT"; Filename: "{app}\malt.exe"; IconFilename: "{app}\malt.exe"

[Run]
Filename: "{app}\malt.exe"; Parameters: "--version"; \
  Description: "Verify the installation"; Flags: nowait postinstall skipifsilent

[Code]
{ Append {app} to the user PATH only if it is not already present, and remove
  exactly that entry on uninstall — never touch unrelated entries. }
procedure EnvAddPath(Path: string);
var
  Paths: string;
begin
  if RegQueryStringValue(HKCU, 'Environment', 'Path', Paths) then
  begin
    if (Paths = '') then
      Paths := Path
    else if (Pos(';' + Path + ';', ';' + Paths + ';') = 0) then
      Paths := Paths + ';' + Path;
  end
  else
    Paths := Path;
  RegWriteStringValue(HKCU, 'Environment', 'Path', Paths);
end;

procedure EnvRemovePath(Path: string);
var
  Paths: string;
  P: Integer;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', Paths) then
    Exit;
  P := Pos(';' + Path + ';', ';' + Paths + ';');
  if P = 0 then
    Exit;
  if P = 1 then
    Paths := Copy(Paths, Length(Path) + 1, Length(Paths))
  else
    Paths := Copy(Paths, 1, P - 1) + Copy(Paths, P + Length(Path), Length(Paths));
  Paths := StringChange(Paths, ';;', ';');
  if (Paths <> '') and (Paths[Length(Paths)] = ';') then
    Paths := Copy(Paths, 1, Length(Paths) - 1);
  RegWriteStringValue(HKCU, 'Environment', 'Path', Paths);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('addtopath') then
    EnvAddPath(ExpandConstant('{app}'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    EnvRemovePath(ExpandConstant('{app}'));
end;
