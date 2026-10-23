#define MyAppName "Rogue Compressor For EVO"
#define MyAppVersion "0.9.0-beta.1"
#define MyAppPublisher "Rogue Software"
#define MyAppExeName "RogueCompressorForEVO.exe"
[Setup]
AppId={{2BD12448-8E52-4CDB-AC7F-F73E80232B08}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Rogue Software\Rogue Compressor For EVO Beta
DefaultGroupName=Rogue Software Beta
UninstallDisplayName=Rogue Compressor For EVO 0.9.0-beta.1
OutputDir=../artifacts
OutputBaseFilename=Rogue_Compressor_For_EVO_Setup_0.9.0-beta.1_win64
SetupIconFile=rogue_compressor.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0
VersionInfoVersion=0.9.0.1
VersionInfoProductVersion=0.9.0.1
SetupLogging=yes
LicenseFile=LICENSE
[Files]
Source: "..\portable\RogueCompressorForEVO\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\{#MyAppName} Beta"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName} Beta"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Rogue Compressor For EVO"; Flags: nowait postinstall skipifsilent


