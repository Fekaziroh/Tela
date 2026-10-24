; Tela! setup (Inno Setup 6). Built by .github/workflows/release.yml or build.ps1:
;   ISCC /DAppVersion=1.4.0 /DPawnIOUrl=<url> installer\Tela.iss
; Expects build\dist\Tela (PyInstaller), build\components\lhm and build\components\presentmon, build\tela.ico.

#ifndef AppVersion
  #define AppVersion "1.4.9"
#endif
#ifndef PawnIOUrl
  #define PawnIOUrl ""
#endif
#define WebView2Url "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
#define Root ".."
#define Build "..\build"

[Setup]
AppId={{8C1F6C2E-7A1B-4E7B-9C55-3F2D6B9E1A40}
AppName=Tela!
AppVersion={#AppVersion}
AppVerName=Tela! {#AppVersion}
AppPublisher=Tela!
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\Tela
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\Tela.exe
UninstallDisplayName=Tela!
OutputDir={#Build}
OutputBaseFilename=Tela-Setup-{#AppVersion}
SetupIconFile={#Build}\tela.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
CloseApplications=no
SetupMutex=TelaSetupMutex
ChangesAssociations=yes

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
en.TaskStartup=Start Tela! with Windows
pt.TaskStartup=Iniciar a Tela! com o Windows
es.TaskStartup=Iniciar Tela! con Windows
en.TaskPawnIO=Install PawnIO (needed for CPU and motherboard temperatures)
pt.TaskPawnIO=Instalar o PawnIO (necessário para as temperaturas do CPU e da placa-mãe)
es.TaskPawnIO=Instalar PawnIO (necesario para las temperaturas de la CPU y de la placa base)
en.InstallingWebView2=Installing Microsoft WebView2...
pt.InstallingWebView2=Instalando o Microsoft WebView2...
es.InstallingWebView2=Instalando Microsoft WebView2...
en.InstallingPawnIO=Installing PawnIO...
pt.InstallingPawnIO=Instalando o PawnIO...
es.InstallingPawnIO=Instalando PawnIO...
en.CompTitle=What gets installed
pt.CompTitle=O que vai ser instalado
es.CompTitle=Qué se va a instalar
en.CompDesc=Tela! uses free components. The setup downloads only the ones missing on this PC.
pt.CompDesc=A Tela! usa componentes gratuitos. O instalador baixa só os que faltam neste PC.
es.CompDesc=Tela! usa componentes gratuitos. El instalador descarga solo los que faltan en este PC.
en.CompIntro=Besides Tela! itself, this PC needs:
pt.CompIntro=Além da própria Tela!, este PC precisa de:
es.CompIntro=Además de Tela!, este PC necesita:
en.CompWebView2=• Microsoft WebView2: the engine that draws the Tela! window, the same one the Edge browser uses. It already comes with Windows 11 and most copies of Windows 10.
pt.CompWebView2=• Microsoft WebView2: o motor que desenha a janela da Tela!, o mesmo do navegador Edge. Já vem no Windows 11 e na maioria dos Windows 10.
es.CompWebView2=• Microsoft WebView2: el motor que dibuja la ventana de Tela!, el mismo del navegador Edge. Ya viene con Windows 11 y con la mayoría de los Windows 10.
en.CompPawnIO=• PawnIO: a small driver that lets Tela! read the temperatures, clocks and fans of the processor and the motherboard. Without it those values stay blank. You can uncheck it on the next page and install it later.
pt.CompPawnIO=• PawnIO: um driver pequeno que deixa a Tela! ler temperaturas, clocks e ventoinhas do processador e da placa-mãe. Sem ele esses valores ficam em branco. Dá para desmarcar na próxima página e instalar depois.
es.CompPawnIO=• PawnIO: un driver pequeño que permite a Tela! leer temperaturas, frecuencias y ventiladores del procesador y de la placa base. Sin él esos valores quedan en blanco. Puedes desmarcarlo en la página siguiente e instalarlo después.
en.OpenTela=Open Tela!
pt.OpenTela=Abrir a Tela!
es.OpenTela=Abrir Tela!
en.DeleteData=Also delete your Tela! settings, layouts, themes and logos?
pt.DeleteData=Apagar também as suas configurações, layouts, temas e logos da Tela!?
es.DeleteData=¿Borrar también tus ajustes, diseños, temas y logos de Tela!?
en.NeedNet=Tela! needs .NET Framework 4.7.2 or newer. Install it with Windows Update and run the setup again.
pt.NeedNet=A Tela! precisa do .NET Framework 4.7.2 ou mais novo. Instale pelo Windows Update e rode o instalador de novo.
es.NeedNet=Tela! necesita .NET Framework 4.7.2 o posterior. Instálalo con Windows Update y vuelve a ejecutar el instalador.
en.DownloadFailed=A component could not be downloaded. Tela! will be installed anyway; you can install it later.
pt.DownloadFailed=Um componente não pôde ser baixado. A Tela! será instalada mesmo assim; ele pode ser instalado depois.
es.DownloadFailed=No se pudo descargar un componente. Tela! se instalará de todos modos; puedes instalarlo después.

[Tasks]
Name: "startup"; Description: "{cm:TaskStartup}"
Name: "pawnio"; Description: "{cm:TaskPawnIO}"; Check: NeedsPawnIO
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; program files of the previous version (settings live in %APPDATA%\Tela and are kept)
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\ui"
Type: filesandordirs; Name: "{app}\layouts"
Type: filesandordirs; Name: "{app}\themes"
Type: filesandordirs; Name: "{app}\lhm"
Type: filesandordirs; Name: "{app}\presentmon"

[Files]
Source: "{#Build}\dist\Tela\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Root}\ui\*"; DestDir: "{app}\ui"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Root}\layouts\*.yaml"; DestDir: "{app}\layouts"; Flags: ignoreversion
Source: "{#Root}\themes\*.yaml"; DestDir: "{app}\themes"; Flags: ignoreversion
Source: "{#Root}\config_default.yaml"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\THIRD-PARTY-NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Build}\components\lhm\*"; DestDir: "{app}\lhm"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Build}\components\presentmon\*"; DestDir: "{app}\presentmon"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Registry]
; .tela-theme files open in Tela! (double click adds the theme to Appearance › Screen themes)
Root: HKA; Subkey: "Software\Classes\.tela-theme"; ValueType: string; ValueName: ""; ValueData: "Tela.Theme"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\Tela.Theme"; ValueType: string; ValueName: ""; ValueData: "Tela! theme"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Tela.Theme\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\Tela.exe,0"
Root: HKA; Subkey: "Software\Classes\Tela.Theme\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Tela.exe"" --import-theme ""%1"""

[Icons]
Name: "{autoprograms}\Tela!"; Filename: "{app}\Tela.exe"
Name: "{autodesktop}\Tela!"; Filename: "{app}\Tela.exe"; Tasks: desktopicon

[Run]
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "{cm:InstallingWebView2}"; Check: WebView2Downloaded; Flags: waituntilterminated
Filename: "{tmp}\PawnIO_setup.exe"; StatusMsg: "{cm:InstallingPawnIO}"; Check: PawnIODownloaded; Flags: waituntilterminated
Filename: "{app}\Tela.exe"; Parameters: "--autostart on"; Tasks: startup; Flags: runhidden waituntilterminated
Filename: "{app}\Tela.exe"; Parameters: "--autostart off"; Tasks: not startup; Flags: runhidden waituntilterminated
Filename: "{app}\Tela.exe"; Description: "{cm:OpenTela}"; Flags: nowait postinstall skipifsilent runascurrentuser
; an update started from Tela! runs the setup with /SILENT: open Tela! again when it finishes
Filename: "{app}\Tela.exe"; Check: WizardSilent; Flags: nowait runascurrentuser

[UninstallRun]
Filename: "{app}\Tela.exe"; Parameters: "--quit"; RunOnceId: "QuitTela"; Flags: runhidden waituntilterminated
Filename: "{app}\Tela.exe"; Parameters: "--autostart off"; RunOnceId: "AutostartOff"; Flags: runhidden waituntilterminated
Filename: "{sys}\taskkill.exe"; Parameters: "/f /im PresentMon.exe"; RunOnceId: "StopPresentMon"; Flags: runhidden

[Code]
var
  DownloadPage: TDownloadWizardPage;
  InfoPage: TOutputMsgWizardPage;

function NeedsPawnIO: Boolean;
begin
  Result := (not RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\PawnIO')) and ('{#PawnIOUrl}' <> '');
end;

function WebView2Version(Root: Integer; Key: String): String;
begin
  if not RegQueryStringValue(Root, Key, 'pv', Result) then
    Result := '';
end;

function HasWebView2: Boolean;
var
  v: String;
begin
  v := WebView2Version(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}');
  if (v = '') or (v = '0.0.0.0') then
    v := WebView2Version(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}');
  Result := (v <> '') and (v <> '0.0.0.0');
end;

function WebView2Downloaded: Boolean;
begin
  Result := FileExists(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'));
end;

function PawnIODownloaded: Boolean;
begin
  Result := FileExists(ExpandConstant('{tmp}\PawnIO_setup.exe'));
end;

function InitializeSetup: Boolean;
var
  Release: Cardinal;
begin
  Result := RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full', 'Release', Release)
            and (Release >= 461808);
  if not Result then
    MsgBox(CustomMessage('NeedNet'), mbError, MB_OK);
end;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  Result := True;
end;

procedure InitializeWizard;
var
  Msg: String;
begin
  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), @OnDownloadProgress);
  { first install (or a component still missing): say in plain words what each component is for }
  Msg := CustomMessage('CompIntro');
  if not HasWebView2 then
    Msg := Msg + #13#10#13#10 + CustomMessage('CompWebView2');
  if NeedsPawnIO then
    Msg := Msg + #13#10#13#10 + CustomMessage('CompPawnIO');
  InfoPage := CreateOutputMsgPage(wpSelectDir, CustomMessage('CompTitle'), CustomMessage('CompDesc'), Msg);
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (InfoPage <> nil) and (PageID = InfoPage.ID) and HasWebView2 and (not NeedsPawnIO);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Count: Integer;
begin
  Result := True;
  if CurPageID <> wpReady then
    exit;
  DownloadPage.Clear;
  Count := 0;
  if not HasWebView2 then begin
    DownloadPage.Add('{#WebView2Url}', 'MicrosoftEdgeWebview2Setup.exe', '');
    Count := Count + 1;
  end;
  if WizardIsTaskSelected('pawnio') then begin
    DownloadPage.Add('{#PawnIOUrl}', 'PawnIO_setup.exe', '');
    Count := Count + 1;
  end;
  if Count = 0 then
    exit;
  DownloadPage.Show;
  try
    try
      DownloadPage.Download;
    except
      SuppressibleMsgBox(CustomMessage('DownloadFailed'), mbInformation, MB_OK, IDOK);
    end;
  finally
    DownloadPage.Hide;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  { a running Tela! closes properly (black screen); older versions are stopped }
  if FileExists(ExpandConstant('{app}\Tela.exe')) then
    Exec(ExpandConstant('{app}\Tela.exe'), '--quit', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im Tela.exe /im TelaV3.exe /im TelaV2.exe /im PresentMon.exe', '',
       SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DeleteData: Boolean;
begin
  if CurUninstallStep <> usPostUninstall then
    exit;
  DeleteData := Pos('/DELETEDATA', Uppercase(GetCmdTail)) > 0;
  if (not DeleteData) and (not UninstallSilent) then
    DeleteData := MsgBox(CustomMessage('DeleteData'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
  if DeleteData then
    DelTree(ExpandConstant('{userappdata}\Tela'), True, True, True);
end;
