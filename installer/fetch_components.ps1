# Downloads what the setup ships or points to, from the official GitHub releases:
#   <Out>\lhm\          LibreHardwareMonitorLib (.NET Framework 4.7.2 build)  - sensors (required)
#   <Out>\presentmon\   PresentMon console (Intel)                            - FPS (optional)
#   <Out>\pawnio_url.txt  download link of the PawnIO installer (downloaded by the setup only when missing)
param([string]$Out = "build\components")
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$head = @{ 'User-Agent' = 'Tela-build' }
if ($env:GITHUB_TOKEN) { $head['Authorization'] = "Bearer $($env:GITHUB_TOKEN)" }
New-Item $Out -ItemType Directory -Force | Out-Null

# ---- LibreHardwareMonitorLib
$rel = Invoke-RestMethod 'https://api.github.com/repos/LibreHardwareMonitor/LibreHardwareMonitor/releases/latest' -Headers $head
$zips = $rel.assets | Where-Object { $_.name -like '*.zip' }
$asset = $zips | Where-Object { $_.name -match '472|framework|net4' } | Select-Object -First 1
if (-not $asset) { $asset = $zips | Where-Object { $_.name -notmatch '\.NET\.?\d|net\d|netcore|linux|mac|source' } | Select-Object -First 1 }
if (-not $asset) { throw "No .NET Framework zip in LibreHardwareMonitor $($rel.tag_name): $($zips.name -join ', ')" }
$tmp = Join-Path $env:TEMP 'tela_lhm'
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
New-Item $tmp -ItemType Directory | Out-Null
Invoke-WebRequest $asset.browser_download_url -OutFile (Join-Path $tmp 'lhm.zip') -UseBasicParsing
Expand-Archive (Join-Path $tmp 'lhm.zip') -DestinationPath (Join-Path $tmp 'x') -Force
$dll = Get-ChildItem (Join-Path $tmp 'x') -Recurse -Filter 'LibreHardwareMonitorLib.dll' | Select-Object -First 1
if (-not $dll) { throw 'LibreHardwareMonitorLib.dll is not in the zip' }
$lhm = Join-Path $Out 'lhm'
Remove-Item $lhm -Recurse -Force -ErrorAction SilentlyContinue
New-Item $lhm -ItemType Directory | Out-Null
Copy-Item (Join-Path $dll.DirectoryName '*.dll') $lhm
Set-Content (Join-Path $lhm 'version.txt') $rel.tag_name
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "LibreHardwareMonitor $($rel.tag_name) ($($asset.name))"

# ---- PresentMon (console build)
$pmDir = Join-Path $Out 'presentmon'
Remove-Item $pmDir -Recurse -Force -ErrorAction SilentlyContinue
try {
  $rels = Invoke-RestMethod 'https://api.github.com/repos/GameTechDev/PresentMon/releases?per_page=15' -Headers $head
  foreach ($r in $rels) {
    if ($r.prerelease) { continue }
    $a = $r.assets | Where-Object { $_.name -match '^PresentMon-[\d\.]+-x64\.exe$' } | Select-Object -First 1
    if ($a) {
      New-Item $pmDir -ItemType Directory | Out-Null
      Invoke-WebRequest $a.browser_download_url -OutFile (Join-Path $pmDir 'PresentMon.exe') -UseBasicParsing
      Set-Content (Join-Path $pmDir 'version.txt') $r.tag_name
      Write-Host "PresentMon $($r.tag_name)"
      break
    }
  }
} catch { Write-Warning "PresentMon not downloaded: $($_.Exception.Message)" }

# ---- PawnIO installer link (fixed per build, so the setup always gets the same file)
try {
  $p = Invoke-RestMethod 'https://api.github.com/repos/namazso/PawnIO.Setup/releases/latest' -Headers $head
  $a = $p.assets | Where-Object { $_.name -match '\.exe$' } | Select-Object -First 1
  if (-not $a) { throw 'no installer in the latest release' }
  Set-Content (Join-Path $Out 'pawnio_url.txt') $a.browser_download_url -NoNewline
  Write-Host "PawnIO $($p.tag_name): $($a.browser_download_url)"
} catch {
  Write-Warning "PawnIO link not found: $($_.Exception.Message)"
  Set-Content (Join-Path $Out 'pawnio_url.txt') '' -NoNewline
}
