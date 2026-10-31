<#
.SYNOPSIS
  Instaluje lub usuwa BepInEx 5 (x86) i plugin Lektor PL w folderze gry (D11). Uruchamia użytkownik.

.DESCRIPTION
  -Install    sprawdza SHA-256 paczki BepInEx, zapisuje listę plików gry (przed), kopiuje loader i plugin,
              zapisuje listę po instalacji i pokazuje różnice (powinny być tylko dodane pliki).
  -Uninstall  kopiuje BepInEx\LogOutput.log do analysis\work\install\logs, usuwa tylko pliki dodane przez -Install,
              porównuje folder gry z listą sprzed instalacji.
  -Status     pokazuje, czy loader jest zainstalowany, i najnowszy dziennik pluginu.
  Gra nie może być uruchomiona. Listy plików i kopie logów trafiają do analysis\work\install (poza repozytorium).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Install
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Install', Mandatory)] [switch] $Install,
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
    foreach ($f in $PluginFiles | Where-Object { $_ -like '*.dll' }) {
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
    $pluginDir = Join-Path $GameDir 'BepInEx\plugins\LektorPL'
    New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null
    foreach ($f in $PluginFiles) {
        $src = Join-Path $PluginBin $f
        if (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination $pluginDir }
    }
    $winhttp = (Get-FileHash -LiteralPath (Join-Path $GameDir 'winhttp.dll') -Algorithm SHA256).Hash
    @("# Pliki dodane przez lektor-hook.ps1 -Install, $(Get-Date -Format s)", "winhttp.sha256=$winhttp") + $created |
        Set-Content -LiteralPath $Installed -Encoding UTF8
    Remove-Item -LiteralPath $staging -Recurse -Force

    $after = Save-Snapshot 'snapshot-after-install.csv'
    Show-Diff $before $after 'Zmiany po instalacji (oczekiwane: tylko dodane pliki loadera i pluginu)'
    Write-Host ''
    Write-Host 'Zainstalowano. Uruchom grę normalnie ze Steama.' -ForegroundColor Green
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
    $last = Get-ChildItem -LiteralPath $PluginLogs -Filter 'hook-*.jsonl' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($last) { Write-Host "Najnowszy dziennik pluginu: $($last.FullName) ($([math]::Round($last.Length / 1KB)) KB)" }
}

if ($Install) { Install-Hook }
elseif ($Uninstall) { Uninstall-Hook }
else { Show-Status }
