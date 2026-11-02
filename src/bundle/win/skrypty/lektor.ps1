<#
.SYNOPSIS
  Lektor PL dla Descent: Legends of the Dark (Windows). Uruchamiany z plików .cmd w folderze paczki.

.DESCRIPTION
  -Install    znajduje grę w Steam, kopiuje do folderu gry Doorstop 4.6 (winhttp.dll, .doorstop_version) i zapisuje
              doorstop_config.ini ze ścieżką do plugin\LektorPL.Loader.dll w tym folderze (D58). Przed instalacją
              i po niej zapisuje listę plików gry i pokazuje różnice. Ponowne uruchomienie odświeża ścieżkę
              (np. po przeniesieniu folderu paczki).
  -Uninstall  usuwa z folderu gry tylko pliki dodane przez -Install i porównuje folder ze stanem sprzed instalacji.
  -Disable    wyłącza lektora (enabled=false w doorstop_config.ini); gra startuje bez niego.
  -Enable     włącza lektora z powrotem.
  -Test       odtwarza jedną kwestię narratora z ustawieniami z ustawienia.toml (Test dźwięku).
  -Status     stan instalacji i najnowsze dzienniki.
  Stan instalacji leży w folderze paczki (stan\), dzienniki w logs\.
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Install', Mandatory)] [switch] $Install,
    [Parameter(ParameterSetName = 'Uninstall', Mandatory)] [switch] $Uninstall,
    [Parameter(ParameterSetName = 'Disable', Mandatory)] [switch] $Disable,
    [Parameter(ParameterSetName = 'Enable', Mandatory)] [switch] $Enable,
    [Parameter(ParameterSetName = 'Test', Mandatory)] [switch] $Test,
    [Parameter(ParameterSetName = 'Status')] [switch] $Status,
    [string] $GameDir
)
$ErrorActionPreference = 'Stop'

$Bundle = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$StateDir = Join-Path $Bundle 'stan'
$StateFile = Join-Path $StateDir 'instalacja.txt'
$Baseline = Join-Path $StateDir 'przed-instalacja.csv'
$Settings = Join-Path $Bundle 'ustawienia.toml'
$Logs = Join-Path $Bundle 'logs'
$LoaderDll = Join-Path $Bundle 'plugin\LektorPL.Loader.dll'
$DoorstopDir = Join-Path $Bundle 'loader'
$DoorstopFiles = 'winhttp.dll', '.doorstop_version'
$ConfigName = 'doorstop_config.ini'
$AppId = '1611070'
$GameExe = 'Legends of the Dark.exe'
$GameProcess = 'Legends of the Dark'

function Say([string] $msg, [string] $color = 'Gray') { Write-Host $msg -ForegroundColor $color }

function Assert-GameClosed {
    if (Get-Process -Name $GameProcess -ErrorAction SilentlyContinue) {
        throw 'Gra jest uruchomiona. Zamknij ją i uruchom ten plik ponownie.'
    }
}

function Find-Game {
    $steam = $null
    foreach ($key in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam') {
        $p = Get-ItemProperty -Path $key -ErrorAction SilentlyContinue
        if ($p -and $p.SteamPath) { $steam = $p.SteamPath; break }
        if ($p -and $p.InstallPath) { $steam = $p.InstallPath; break }
    }
    $libs = New-Object System.Collections.Generic.List[string]
    if ($steam) {
        $libs.Add($steam)
        $vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf) {
            foreach ($m in [regex]::Matches((Get-Content -LiteralPath $vdf -Raw -Encoding UTF8), '"path"\s+"([^"]+)"')) {
                $libs.Add(($m.Groups[1].Value -replace '\\\\', '\'))
            }
        }
    }
    foreach ($lib in $libs | Select-Object -Unique) {
        $acf = Join-Path $lib "steamapps\appmanifest_$AppId.acf"
        if (-not (Test-Path -LiteralPath $acf)) { continue }
        $m = [regex]::Match((Get-Content -LiteralPath $acf -Raw -Encoding UTF8), '"installdir"\s+"([^"]+)"')
        if (-not $m.Success) { continue }
        $dir = Join-Path $lib "steamapps\common\$($m.Groups[1].Value)"
        if (Test-Path -LiteralPath (Join-Path $dir $GameExe)) { return (Resolve-Path -LiteralPath $dir).Path }
    }
    Say 'Nie znalazłem gry w bibliotekach Steam.' Yellow
    Say 'W Steam: prawy klik na grze > Zarządzaj > Przeglądaj pliki lokalne, skopiuj ścieżkę z paska adresu i wklej ją tutaj.'
    $dir = (Read-Host 'Folder gry').Trim().Trim('"')
    if (-not $dir -or -not (Test-Path -LiteralPath (Join-Path $dir $GameExe))) { throw "W tym folderze nie ma pliku $GameExe." }
    (Resolve-Path -LiteralPath $dir).Path
}

function Read-State {
    if (-not (Test-Path -LiteralPath $StateFile)) { return $null }
    $state = @{}
    foreach ($line in Get-Content -LiteralPath $StateFile -Encoding UTF8) {
        if ($line -match '^([a-z0-9_.]+)=(.*)$') { $state[$Matches[1]] = $Matches[2] }
    }
    $state
}

function Get-InstalledGame {
    $state = Read-State
    if (-not $state) { throw 'Lektor nie jest zainstalowany. Najpierw uruchom Zainstaluj.' }
    $state
}

function Get-Snapshot([string] $game) {
    $root = $game.TrimEnd('\')
    Get-ChildItem -LiteralPath $root -Recurse -Force -File | ForEach-Object {
        [pscustomobject]@{
            Path  = $_.FullName.Substring($root.Length + 1)
            Size  = [string]$_.Length
            Mtime = [string]$_.LastWriteTimeUtc.Ticks
        }
    } | Sort-Object Path
}

function Save-Snapshot([string] $game, [string] $path) {
    Get-Snapshot $game | Export-Csv -LiteralPath $path -NoTypeInformation -Encoding UTF8
}

function Show-Diff([string] $beforeCsv, [string] $afterCsv, [string] $title) {
    $before = @{}; foreach ($x in Import-Csv -LiteralPath $beforeCsv) { $before[$x.Path] = $x }
    $after = @{}; foreach ($x in Import-Csv -LiteralPath $afterCsv) { $after[$x.Path] = $x }
    $added = @($after.Keys | Where-Object { -not $before.ContainsKey($_) } | Sort-Object)
    $removed = @($before.Keys | Where-Object { -not $after.ContainsKey($_) } | Sort-Object)
    $changed = @($after.Keys | Where-Object {
            $before.ContainsKey($_) -and ($before[$_].Size -ne $after[$_].Size -or $before[$_].Mtime -ne $after[$_].Mtime)
        } | Sort-Object)
    Say ''
    Say $title Cyan
    Say ("dodane: {0}, usunięte: {1}, zmienione: {2}" -f $added.Count, $removed.Count, $changed.Count)
    foreach ($p in $added) { Say "  + $p$(Note $p)" }
    foreach ($p in $removed) { Say "  - $p$(Note $p)" }
    foreach ($p in $changed) { Say "  * $p$(Note $p)" }
}

function Note([string] $path) {
    if ($path -like 'Legends of the Dark_Data\SavedGames\*') { return '   (zapis gry, oczekiwane)' }
    ''
}

function Write-DoorstopConfig([string] $game, [bool] $enabled) {
    $flag = if ($enabled) { 'true' } else { 'false' }
    $text = @(
        '# Lektor PL (Doorstop 4.6). Plik zapisuje Zainstaluj, a Wyłącz/Włącz lektora zmienia "enabled".'
        '[General]'
        "enabled=$flag"
        "target_assembly=$LoaderDll"
        'redirect_output_log=false'
        'boot_config_override='
        'ignore_disable_switch=false'
        ''
        '[UnityMono]'
        'dll_search_path_override='
        'debug_enabled=false'
        'debug_address=127.0.0.1:10000'
        'debug_suspend=false'
        ''
    ) -join "`r`n"
    # UTF-16 z BOM: Doorstop czyta plik przez GetPrivateProfileStringW, więc ścieżka może mieć polskie znaki.
    [System.IO.File]::WriteAllText((Join-Path $game $ConfigName), $text, [System.Text.Encoding]::Unicode)
}

function Test-OurConfig([string] $game) {
    $cfg = Join-Path $game $ConfigName
    (Test-Path -LiteralPath $cfg) -and ((Get-Content -LiteralPath $cfg -Raw) -match 'LektorPL\.Loader\.dll')
}

function Install-Lektor {
    Assert-GameClosed
    foreach ($f in @($LoaderDll) + @($DoorstopFiles | ForEach-Object { Join-Path $DoorstopDir $_ })) {
        if (-not (Test-Path -LiteralPath $f)) { throw "Paczka jest niepełna, brakuje: $f" }
    }
    $state = Read-State
    if ($state) {
        $game = $state['game']
        if ((Test-Path -LiteralPath (Join-Path $game 'winhttp.dll')) -and (Test-OurConfig $game)) {
            Write-DoorstopConfig $game $true
            Say "Lektor był już zainstalowany w: $game" Green
            Say 'Odświeżyłem ścieżkę do folderu paczki i włączyłem lektora. Uruchom grę ze Steama.' Green
            return
        }
        throw "Stan instalacji wskazuje $game, ale nie ma tam plików lektora. Usuń folder $StateDir i uruchom Zainstaluj ponownie."
    }
    $game = if ($GameDir) { (Resolve-Path -LiteralPath $GameDir).Path } else { Find-Game }
    Say "Gra: $game"
    $foreign = @('winhttp.dll', $ConfigName, '.doorstop_version', 'version.dll', 'BepInEx', 'MelonLoader' |
            Where-Object { Test-Path -LiteralPath (Join-Path $game $_) })
    if ($foreign) {
        throw ("W folderze gry jest już inny loader modów: {0}. Lektor PL nie nadpisuje cudzych plików. " +
            "Odinstaluj tamten mod (albo usuń te pliki) i uruchom Zainstaluj ponownie.") -f ($foreign -join ', ')
    }

    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    Save-Snapshot $game $Baseline
    foreach ($f in $DoorstopFiles) { Copy-Item -LiteralPath (Join-Path $DoorstopDir $f) -Destination (Join-Path $game $f) }
    Write-DoorstopConfig $game $true
    $winhttp = (Get-FileHash -LiteralPath (Join-Path $game 'winhttp.dll') -Algorithm SHA256).Hash
    @(
        "# Lektor PL: instalacja z $(Get-Date -Format s). Nie usuwaj, dopóki lektor jest zainstalowany."
        "game=$game"
        "winhttp.sha256=$winhttp"
        "files=$(($DoorstopFiles + $ConfigName) -join ';')"
    ) | Set-Content -LiteralPath $StateFile -Encoding UTF8

    $after = Join-Path $StateDir 'po-instalacji.csv'
    Save-Snapshot $game $after
    Show-Diff $Baseline $after 'Zmiany w folderze gry (oczekiwane: 3 dodane pliki)'
    Say ''
    Say 'Zainstalowano. Uruchom grę normalnie ze Steama: lektor wystartuje razem z nią.' Green
    Say 'Nie przenoś ani nie usuwaj tego folderu bez odinstalowania (po przeniesieniu uruchom Zainstaluj ponownie).'
}

function Uninstall-Lektor {
    Assert-GameClosed
    $state = Get-InstalledGame
    $game = $state['game']
    foreach ($f in $state['files'] -split ';') {
        $full = Join-Path $game $f
        if (-not (Test-Path -LiteralPath $full)) { continue }
        if ($f -eq 'winhttp.dll' -and (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash -ne $state['winhttp.sha256']) {
            Say "winhttp.dll ma inną sumę niż zainstalowana (podmienił go inny mod?), zostawiam: $full" Yellow
            continue
        }
        if ($f -eq $ConfigName -and -not (Test-OurConfig $game)) {
            Say "$ConfigName nie jest plikiem lektora, zostawiam: $full" Yellow
            continue
        }
        Remove-Item -LiteralPath $full -Force
        Say "usunięto: $f"
    }
    if (Test-Path -LiteralPath $Baseline) {
        $after = Join-Path $StateDir 'po-odinstalowaniu.csv'
        Save-Snapshot $game $after
        Show-Diff $Baseline $after 'Folder gry względem stanu sprzed instalacji (oczekiwane: brak różnic poza zapisami gry)'
    }
    Remove-Item -LiteralPath $StateDir -Recurse -Force
    Say ''
    Say 'Odinstalowano. Ten folder można teraz usunąć.' Green
}

function Set-Enabled([bool] $enabled) {
    Assert-GameClosed
    $game = (Get-InstalledGame)['game']
    if (-not (Test-OurConfig $game)) { throw "Nie ma pliku lektora $ConfigName w $game. Uruchom Zainstaluj." }
    Write-DoorstopConfig $game $enabled
    if ($enabled) { Say 'Lektor włączony. Uruchom grę ze Steama.' Green }
    else { Say 'Lektor wyłączony: gra startuje bez niego. Włączysz go plikiem Włącz lektora.' Green }
}

function Get-Python {
    $override = Select-String -LiteralPath $Settings -Pattern '^\s*python\s*=\s*[''"]([^''"]+)[''"]' -Encoding UTF8 | Select-Object -First 1
    if ($override) { return $override.Matches[0].Groups[1].Value }
    Join-Path $Bundle 'python\python.exe'
}

function Start-SoundTest {
    $py = Get-Python
    if (-not (Test-Path -LiteralPath $py)) { throw "Brak Pythona paczki: $py" }
    Say 'Odtwarzam jedną kwestię narratora...'
    & $py -I -m lektor.companion --test --config $Settings --logs $Logs
    if ($LASTEXITCODE -ne 0) { throw "Test dźwięku nie powiódł się (kod $LASTEXITCODE). Sprawdź ustawienia.toml." }
    Say 'Jeśli nic nie było słychać: sprawdź głośność (volume) i urządzenie (device) w Ustawieniach.' Green
}

function Show-Status {
    $state = Read-State
    if (-not $state) { Say 'Lektor nie jest zainstalowany.'; return }
    $game = $state['game']
    Say "Gra: $game"
    if (-not (Test-OurConfig $game)) { Say "Brak pliku lektora $ConfigName w folderze gry. Uruchom Zainstaluj." Yellow; return }
    $on = (Get-Content -LiteralPath (Join-Path $game $ConfigName) -Raw) -match '(?m)^enabled=true'
    Say ("Lektor: {0}" -f $(if ($on) { 'włączony' } else { 'wyłączony' }))
    Say "Loader: $((Get-Item -LiteralPath $LoaderDll).VersionInfo.FileVersion)"
    foreach ($pattern in 'loader-*.log', 'hook-*.jsonl', 'companion-*.jsonl') {
        $last = Get-ChildItem -LiteralPath $Logs -Filter $pattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
        if ($last) { Say "  $($last.Name)  $($last.LastWriteTime)" }
    }
}

try {
    if ($Install) { Install-Lektor }
    elseif ($Uninstall) { Uninstall-Lektor }
    elseif ($Disable) { Set-Enabled $false }
    elseif ($Enable) { Set-Enabled $true }
    elseif ($Test) { Start-SoundTest }
    else { Show-Status }
}
catch {
    Say ''
    Say "Błąd: $($_.Exception.Message)" Red
    exit 1
}
