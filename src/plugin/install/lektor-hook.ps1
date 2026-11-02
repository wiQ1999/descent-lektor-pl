<#
.SYNOPSIS
  Instaluje lub usuwa BepInEx 5 (x86) i plugin Lektor PL w folderze gry (D11). Uruchamia użytkownik.

.DESCRIPTION
  -Install    sprawdza SHA-256 paczki BepInEx, zapisuje listę plików gry (przed), kopiuje loader i plugin,
              nakłada poprawkę MonoMod (D54, jak -MonoModFix), zapisuje listę po instalacji i pokazuje różnice
              (powinny być tylko dodane pliki).
              Z -LoaderOnly kopiuje sam BepInEx, bez pluginu (test wyjścia, D40).
  -Uninstall  kopiuje BepInEx\LogOutput.log do analysis\work\install\logs, usuwa tylko pliki dodane przez -Install,
              porównuje folder gry z listą sprzed instalacji.
  -Status     pokazuje, czy loader jest zainstalowany, wersję i etap pluginu oraz najnowszy dziennik pluginu.
  -Stage N    ustawia etap diagnostyczny pluginu w BepInEx\config\pl.lektor.descent.cfg (D40): 0 nic, 1 pusty Runner,
              2 + dziennik, 3 + Tracker, 4 całość (domyślnie). Także razem z -Install.
  -MonoModFix podmienia w istniejącej instalacji BepInEx\core\MonoMod.Utils.dll na kopię bez zapisu flagi
              corlib_internal (crash przy wyjściu, D54). Kopię tworzy monomod-fix.ps1. Także razem z -Stage;
              -Uninstall usuwa ją z całym BepInEx.
  Gra nie może być uruchomiona. Listy plików i kopie logów trafiają do analysis\work\install (poza repozytorium).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Install
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Install', Mandatory)] [switch] $Install,
    [Parameter(ParameterSetName = 'Install')] [switch] $LoaderOnly,
    [Parameter(ParameterSetName = 'Install')] [Parameter(ParameterSetName = 'Stage', Mandatory)] [ValidateRange(0, 4)] [int] $Stage,
    [Parameter(ParameterSetName = 'Stage')] [Parameter(ParameterSetName = 'Fix', Mandatory)] [switch] $MonoModFix,
    [Parameter(ParameterSetName = 'Uninstall', Mandatory)] [switch] $Uninstall,
    [Parameter(ParameterSetName = 'Status')] [switch] $Status,
    [string] $GameDir = 'E:\SteamLibrary\steamapps\common\Legends of the Dark'
)
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Work = Join-Path $RepoRoot 'analysis\work\install'
$Zip = Join-Path $RepoRoot 'analysis\work\bin\BepInEx-5.4.23.5\BepInEx_win_x86_5.4.23.5.zip'
$ZipSha256 = '37651C79E40D6F909572A4F461AC25350BB3EF8FE7FBD29F1AA8791A33B84C82'
$PluginBin = Join-Path $RepoRoot 'build\plugin\LektorPL.BepInEx\bin\Release'
$PluginFiles = 'LektorPL.Core.dll', 'LektorPL.Core.pdb', 'LektorPL.BepInEx.dll', 'LektorPL.BepInEx.pdb'
$LoaderFiles = 'winhttp.dll', 'doorstop_config.ini', '.doorstop_version'
$Baseline = Join-Path $Work 'snapshot-before-install.csv'
$Installed = Join-Path $Work 'installed-files.txt'
$PluginLogs = Join-Path $env:LOCALAPPDATA 'LektorPL\logs'
$PluginCfg = Join-Path $GameDir 'BepInEx\config\pl.lektor.descent.cfg'
$MonoModDll = Join-Path $GameDir 'BepInEx\core\MonoMod.Utils.dll'
$MonoModFixDll = Join-Path $RepoRoot 'analysis\work\bin\BepInEx-5.4.23.5\monomod-fix\MonoMod.Utils.dll'
$MonoModSha256 = '9D1495F147AC93C4F81F84538C1A326E8F8A6AEFC78D6289D798F3CE1162C5E9'
$MonoModFixSha256 = '92844571CF832B239FBBBE0F0A6DBB81148A3BD1FC42EA1BA7C5AF34B9E46AF8'

function Assert-GameClosed {
    if (Get-Process -Name 'Legends of the Dark' -ErrorAction SilentlyContinue) {
        throw 'Gra jest uruchomiona. Zamknij ją i uruchom skrypt ponownie.'
    }
}

function Get-Snapshot {
    $root = (Resolve-Path $GameDir).Path.TrimEnd('\')
    Get-ChildItem -LiteralPath $root -Recurse -Force -File | ForEach-Object {
        [pscustomobject]@{
            Path  = $_.FullName.Substring($root.Length + 1)
            Size  = [string]$_.Length
            Mtime = [string]$_.LastWriteTimeUtc.Ticks
        }
    } | Sort-Object Path
}

function Save-Snapshot([string] $name) {
    $path = Join-Path $Work $name
    Get-Snapshot | Export-Csv -LiteralPath $path -NoTypeInformation -Encoding UTF8
    $path
}

function Show-Diff([string] $beforeCsv, [string] $afterCsv, [string] $title) {
    $before = @{}; foreach ($x in Import-Csv -LiteralPath $beforeCsv) { $before[$x.Path] = $x }
    $after = @{}; foreach ($x in Import-Csv -LiteralPath $afterCsv) { $after[$x.Path] = $x }
    $added = @($after.Keys | Where-Object { -not $before.ContainsKey($_) } | Sort-Object)
    $removed = @($before.Keys | Where-Object { -not $after.ContainsKey($_) } | Sort-Object)
    $changed = @($after.Keys | Where-Object {
            $before.ContainsKey($_) -and ($before[$_].Size -ne $after[$_].Size -or $before[$_].Mtime -ne $after[$_].Mtime)
        } | Sort-Object)
    Write-Host ''
    Write-Host "== $title" -ForegroundColor Cyan
    Write-Host ("dodane: {0}, usunięte: {1}, zmienione: {2}" -f $added.Count, $removed.Count, $changed.Count)
    foreach ($p in $added) { Write-Host "  + $p$(Note $p)" }
    foreach ($p in $removed) { Write-Host "  - $p$(Note $p)" }
    foreach ($p in $changed) { Write-Host "  * $p$(Note $p)" }
}

function Note([string] $path) {
    if ($path -like 'Legends of the Dark_Data\SavedGames\*') { return '   (zapis gry, oczekiwane)' }
    ''
}

function Install-Hook {
    Assert-GameClosed
    if (-not (Test-Path -LiteralPath (Join-Path $GameDir 'Legends of the Dark.exe'))) { throw "Nie znaleziono gry w $GameDir" }
    $present = @($LoaderFiles + 'BepInEx' | Where-Object { Test-Path -LiteralPath (Join-Path $GameDir $_) })
    if ($present) { throw "W folderze gry już są pliki loadera: $($present -join ', '). Najpierw -Uninstall albo usuń je ręcznie." }
    $hash = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash
    if ($hash -ne $ZipSha256) { throw "Zła suma SHA-256 paczki BepInEx: $hash" }
    Assert-MonoModFixReady
    foreach ($f in $PluginFiles | Where-Object { $_ -like '*.dll' -and -not $LoaderOnly }) {
        if (-not (Test-Path -LiteralPath (Join-Path $PluginBin $f))) { throw "Brak $f w $PluginBin. Zbuduj plugin: dotnet build src\plugin\BepInEx -c Release" }
    }

    New-Item -ItemType Directory -Force -Path $Work | Out-Null
    $before = Save-Snapshot 'snapshot-before-install.csv'
    Write-Host "Lista plików przed instalacją: $before"

    $staging = Join-Path $Work 'staging'
    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
    Expand-Archive -LiteralPath $Zip -DestinationPath $staging

    $created = New-Object System.Collections.Generic.List[string]
    foreach ($f in $LoaderFiles) {
        Copy-Item -LiteralPath (Join-Path $staging $f) -Destination (Join-Path $GameDir $f)
        $created.Add($f)
    }
    Copy-Item -LiteralPath (Join-Path $staging 'BepInEx') -Destination (Join-Path $GameDir 'BepInEx') -Recurse
    $created.Add('BepInEx\')
    if (-not $LoaderOnly) {
        $pluginDir = Join-Path $GameDir 'BepInEx\plugins\LektorPL'
        New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null
        foreach ($f in $PluginFiles) {
            $src = Join-Path $PluginBin $f
            if (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination $pluginDir }
        }
    }
    $winhttp = (Get-FileHash -LiteralPath (Join-Path $GameDir 'winhttp.dll') -Algorithm SHA256).Hash
    @("# Pliki dodane przez lektor-hook.ps1 -Install, $(Get-Date -Format s)", "winhttp.sha256=$winhttp") + $created |
        Set-Content -LiteralPath $Installed -Encoding UTF8
    Remove-Item -LiteralPath $staging -Recurse -Force

    $after = Save-Snapshot 'snapshot-after-install.csv'
    Show-Diff $before $after 'Zmiany po instalacji (oczekiwane: tylko dodane pliki loadera i pluginu)'
    Write-Host ''
    $what = if ($LoaderOnly) { 'Zainstalowano sam BepInEx, bez pluginu.' } else { 'Zainstalowano BepInEx i plugin.' }
    Write-Host "$what Uruchom grę normalnie ze Steama." -ForegroundColor Green
    Write-Host "Dziennik pluginu: $PluginLogs\hook-*.jsonl; log loadera: $GameDir\BepInEx\LogOutput.log"
}

function Uninstall-Hook {
    Assert-GameClosed
    if (-not (Test-Path -LiteralPath $Installed)) { throw "Brak $Installed — nie wiem, które pliki dodała instalacja." }
    $lines = Get-Content -LiteralPath $Installed -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith('#') }
    $expectedWinhttp = ($lines | Where-Object { $_ -like 'winhttp.sha256=*' }) -replace '^winhttp.sha256=', ''
    $paths = $lines | Where-Object { $_ -notlike '*=*' }

    $log = Join-Path $GameDir 'BepInEx\LogOutput.log'
    if (Test-Path -LiteralPath $log) {
        $dest = Join-Path $Work 'logs'
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        $copy = Join-Path $dest ("LogOutput-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
        Copy-Item -LiteralPath $log -Destination $copy
        Write-Host "Kopia logu loadera: $copy"
    }

    foreach ($p in $paths) {
        $full = Join-Path $GameDir $p.TrimEnd('\')
        if (-not (Test-Path -LiteralPath $full)) { continue }
        if ($p -eq 'winhttp.dll') {
            $h = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
            if ($h -ne $expectedWinhttp) { Write-Warning "winhttp.dll ma inną sumę niż zainstalowana — zostawiam: $full"; continue }
        }
        Remove-Item -LiteralPath $full -Recurse -Force
        Write-Host "usunięto: $p"
    }
    Remove-Item -LiteralPath $Installed

    $after = Save-Snapshot 'snapshot-after-uninstall.csv'
    if (Test-Path -LiteralPath $Baseline) {
        Show-Diff $Baseline $after 'Folder gry względem stanu sprzed instalacji (oczekiwane: brak różnic poza zapisami gry)'
    }
}

function Show-Status {
    $present = @($LoaderFiles + 'BepInEx' | Where-Object { Test-Path -LiteralPath (Join-Path $GameDir $_) })
    if ($present) { Write-Host "Loader w folderze gry: $($present -join ', ')" } else { Write-Host 'Loader nie jest zainstalowany.' }
    $plugin = Join-Path $GameDir 'BepInEx\plugins\LektorPL\LektorPL.BepInEx.dll'
    if (Test-Path -LiteralPath $plugin) { Write-Host "Plugin: $((Get-Item -LiteralPath $plugin).VersionInfo.FileVersion)" } elseif ($present) { Write-Host 'Plugin nie jest zainstalowany (sam loader).' }
    if (Test-Path -LiteralPath $MonoModDll) {
        $h = (Get-FileHash -LiteralPath $MonoModDll -Algorithm SHA256).Hash
        $state = if ($h -eq $MonoModFixSha256) { 'z poprawką D54' } elseif ($h -eq $MonoModSha256) { 'oryginał' } else { "nieznana wersja ($h)" }
        Write-Host "MonoMod.Utils.dll: $state"
    }
    $stageLine = if (Test-Path -LiteralPath $PluginCfg) { Get-Content -LiteralPath $PluginCfg -Encoding UTF8 | Where-Object { $_ -match '^\s*Stage\s*=' } }
    if ($stageLine) { Write-Host "Etap diagnostyczny: $(($stageLine -split '=')[1].Trim())" }
    $last = Get-ChildItem -LiteralPath $PluginLogs -Filter 'hook-*.jsonl' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($last) { Write-Host "Najnowszy dziennik pluginu: $($last.FullName) ($([math]::Round($last.Length / 1KB)) KB)" }
}

function Set-Stage([int] $value) {
    Assert-GameClosed
    if (-not (Test-Path -LiteralPath (Join-Path $GameDir 'BepInEx\plugins\LektorPL'))) { throw 'Plugin nie jest zainstalowany. Najpierw -Install.' }
    New-Item -ItemType Directory -Force -Path (Split-Path $PluginCfg) | Out-Null
    $lines = @(if (Test-Path -LiteralPath $PluginCfg) { Get-Content -LiteralPath $PluginCfg -Encoding UTF8 })
    $found = $false
    $lines = @($lines | ForEach-Object { if ($_ -match '^\s*Stage\s*=') { $found = $true; "Stage = $value" } else { $_ } })
    if (-not $found) { $lines += @('', '[Diagnostics]', '', "Stage = $value") }
    [System.IO.File]::WriteAllLines($PluginCfg, [string[]] $lines, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "Etap diagnostyczny pluginu: $value. Uruchom grę ze Steama." -ForegroundColor Green
}

function Assert-MonoModFixReady {
    if (-not (Test-Path -LiteralPath $MonoModFixDll)) { throw "Brak $MonoModFixDll. Najpierw: powershell -ExecutionPolicy Bypass -File src\plugin\install\monomod-fix.ps1" }
    $h = (Get-FileHash -LiteralPath $MonoModFixDll -Algorithm SHA256).Hash
    if ($h -ne $MonoModFixSha256) { throw "Zła suma SHA-256 poprawionego MonoMod.Utils.dll: $h" }
}

function Set-MonoModFix {
    Assert-GameClosed
    Assert-MonoModFixReady
    if (-not (Test-Path -LiteralPath $MonoModDll)) { throw 'BepInEx nie jest zainstalowany. Najpierw -Install.' }
    $h = (Get-FileHash -LiteralPath $MonoModDll -Algorithm SHA256).Hash
    if ($h -eq $MonoModFixSha256) { Write-Host 'MonoMod.Utils.dll ma już poprawkę D54.'; return }
    if ($h -ne $MonoModSha256) { throw "Nieoczekiwana wersja $MonoModDll ($h). Nie podmieniam." }
    Copy-Item -LiteralPath $MonoModFixDll -Destination $MonoModDll -Force
    Write-Host 'MonoMod.Utils.dll: podmieniono na kopię z poprawką D54 (bez zapisu flagi corlib_internal).' -ForegroundColor Green
}

if ($Install) {
    Install-Hook
    Set-MonoModFix
    if ($PSBoundParameters.ContainsKey('Stage')) { Set-Stage $Stage }
}
elseif ($Uninstall) { Uninstall-Hook }
elseif ($MonoModFix -or $PSBoundParameters.ContainsKey('Stage')) {
    if ($MonoModFix) { Set-MonoModFix }
    if ($PSBoundParameters.ContainsKey('Stage')) { Set-Stage $Stage }
}
else { Show-Status }
