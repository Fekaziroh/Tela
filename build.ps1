# Builds build\Tela-Setup-<version>.exe on a Windows PC (the same steps as the GitHub release workflow).
# Needs Python 3.13 and Inno Setup 6. Usage:  powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$pyExe, $pyArgs = 'python', @()
if (Get-Command py -ErrorAction SilentlyContinue) { $pyExe, $pyArgs = 'py', @('-3.13') }
function Py { & $pyExe @pyArgs @args; if ($LASTEXITCODE) { throw "python $args failed" } }

Py -m pip install --upgrade --quiet --disable-pip-version-check pyinstaller -r requirements.txt
Py tests/run_tests.py
& ./installer/fetch_components.ps1 -Out build\components
Py -c "from icon import save_ico; save_ico(r'build\tela.ico')"
Py installer/version_info.py build\version_info.txt
Py -m PyInstaller --noconfirm --clean --onedir --windowed --uac-admin --log-level ERROR --name Tela `
  --icon "$PWD\build\tela.ico" --version-file "$PWD\build\version_info.txt" --distpath build\dist --workpath build\work --specpath build `
  --hidden-import pystray._win32 --hidden-import webview.platforms.edgechromium --hidden-import webview.platforms.winforms `
  --collect-all pythonnet --collect-all clr_loader --collect-all winrt --collect-data webview app.py
$version = (& $pyExe @pyArgs -c "import engine; print(engine.VERSION)").Trim()
$pawn = Get-Content build\components\pawnio_url.txt -Raw
$iscc = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
& $iscc "/DAppVersion=$version" "/DPawnIOUrl=$pawn" installer\Tela.iss
if ($LASTEXITCODE) { throw 'Inno Setup failed' }
Write-Host "Done: build\Tela-Setup-$version.exe"
