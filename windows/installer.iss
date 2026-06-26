; Inno Setup script — нормальний setup.exe для Adaptive Coffee Wallpaper.
; Збирає standalone-білд Nuitka (dist\run.dist) + 48 шпалер у per-user
; інсталятор (без прав адміністратора), ярлики, опційний автозапуск.
; Компіляція в CI:  iscc /DMyAppVersion=X.Y.Z windows\installer.iss
; Оновлення: той самий AppId+DefaultDirName → апгрейд на місці (запущений
; застосунок закривається). Видалення: авто-uninstaller прибирає файли, ярлики,
; автозапуск і per-user дані/конфіг.

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppName "Adaptive Coffee Wallpaper"
#define MyAppExe "adaptive-wallpaper.exe"
#define MyAppPublisher "dz-vadim"
#define MyAppURL "https://github.com/dz-vadim/adaptive-wallpapers"

[Setup]
AppId={{8F1C9A2E-4D3B-4E6A-9C77-AD7C0FFEE001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\AdaptiveWallpaper
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; per-user інсталяція — без UAC, менше тертя з антивірусом
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=adaptive-wallpaper-setup
SetupIconFile=..\app\adaptive_wallpaper\assets\adaptive-wallpaper.ico
UninstallDisplayIcon={app}\{#MyAppExe}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
; оновлення поверх: той самий AppId+DefaultDirName → апгрейд на місці.
; Закрити запущений застосунок (інакше exe заблокований і апгрейд впаде).
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "uk"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked
Name: "startup"; Description: "{cm:AutoStartProgram,{#MyAppName}}"

[Files]
; standalone-папка Nuitka (exe + усі бібліотеки/дані, включно з іконкою)
Source: "..\dist\run.dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
; шпалери поряд з exe — застосунок знаходить їх автоматично
Source: "..\wallpapers\*"; DestDir: "{app}\wallpapers"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Registry]
; автозапуск при вході (per-user), знімається при видаленні
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "AdaptiveWallpaper"; \
  ValueData: """{app}\{#MyAppExe}"""; Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; закрити застосунок перед видаленням, щоб файли не були заблоковані
Filename: "{sys}\taskkill.exe"; Parameters: "/IM {#MyAppExe} /F"; \
  Flags: runhidden; RunOnceId: "KillApp"

[UninstallDelete]
; прибрати per-user конфіг і скопійовані застосунком дані (шпалери/гліфи)
Type: filesandordirs; Name: "{userappdata}\AdaptiveWallpaper"
Type: filesandordirs; Name: "{localappdata}\AdaptiveWallpaper"

[Code]
// Перед оновленням/встановленням закрити запущений екземпляр (інакше exe
// заблокований і апгрейд впаде). CloseApplications не завжди ловить трей без вікна.
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/IM {#MyAppExe} /F', '',
       SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;
