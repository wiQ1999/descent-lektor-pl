# Próba nakładki lektora: podmienia plugin i companion w rozpakowanej paczce Descent-Lektor-PL (bez budowania paczki).
#   powershell -ExecutionPolicy Bypass -File src/plugin/install/nakladka-test.ps1 -Paczka "D:\Gry\Descent-Lektor-PL"
#   powershell -ExecutionPolicy Bypass -File src/plugin/install/nakladka-test.ps1 -Paczka "D:\Gry\Descent-Lektor-PL" -Przywroc
# Oryginały trafiają do stan\nakladka-kopia w paczce; -Przywroc je oddaje. Grę zamknij przed uruchomieniem.
param(
    [Parameter(Mandatory = $true)][string]$Paczka,
    [switch]$Przywroc
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$paczka = (Resolve-Path $Paczka).Path
if (-not (Test-Path (Join-Path $paczka 'lektor\companion\app.py'))) { throw "To nie jest folder paczki Descent-Lektor-PL: $paczka" }
$kopia = Join-Path $paczka 'stan\nakladka-kopia'

$pliki = @(
    @{ Z = 'build\plugin\LektorPL.Core\bin\Release\LektorPL.Core.dll'; Do = 'plugin\LektorPL.Core.dll' },
    @{ Z = 'build\plugin\LektorPL.Loader\bin\Release\LektorPL.Loader.dll'; Do = 'plugin\LektorPL.Loader.dll' },
    @{ Z = 'src\lektor\companion\app.py'; Do = 'lektor\companion\app.py' },
    @{ Z = 'src\lektor\companion\config.py'; Do = 'lektor\companion\config.py' },
    @{ Z = 'src\lektor\companion\control.py'; Do = 'lektor\companion\control.py' },
    @{ Z = 'src\lektor\companion\director.py'; Do = 'lektor\companion\director.py' }
)

if ($Przywroc) {
    if (-not (Test-Path $kopia)) { throw "Brak kopii oryginałów: $kopia" }
    foreach ($p in $pliki) {
        $cel = Join-Path $paczka $p.Do
        $org = Join-Path $kopia $p.Do
        if (Test-Path $org) { Copy-Item -LiteralPath $org -Destination $cel -Force }
        elseif (Test-Path $cel) { Remove-Item -LiteralPath $cel -Force }     # plik doszedł z próbą (control.py)
    }
    Remove-Item -LiteralPath $kopia -Recurse -Force
    Write-Host 'Przywrócono pliki paczki sprzed próby nakładki.'
    return
}

foreach ($p in $pliki) {
    $src = Join-Path $repo $p.Z
    if (-not (Test-Path $src)) { throw "Brak pliku $src (zbuduj plugin: dotnet build src/plugin/Loader -c Release)" }
}
# Kopia każdego pliku osobno: plik dopisany do listy po wcześniejszej próbie też dostaje oryginał (inaczej -Przywroc by go usunął).
foreach ($p in $pliki) {
    $cel = Join-Path $paczka $p.Do
    $dst = Join-Path $kopia $p.Do
    if ((Test-Path $cel) -and -not (Test-Path $dst)) {
        New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
        Copy-Item -LiteralPath $cel -Destination $dst
    }
}
foreach ($p in $pliki) { Copy-Item -LiteralPath (Join-Path $repo $p.Z) -Destination (Join-Path $paczka $p.Do) -Force }
$core = [System.Diagnostics.FileVersionInfo]::GetVersionInfo((Join-Path $paczka 'plugin\LektorPL.Core.dll')).FileVersion
Write-Host "Nakładka wgrana do $paczka z $repo (rdzeń $core). Oryginały: $kopia (powrót: -Przywroc)."
