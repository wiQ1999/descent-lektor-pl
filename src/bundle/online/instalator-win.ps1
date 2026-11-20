<#
.SYNOPSIS
  Lektor PL dla Descent: Legends of the Dark (Windows): instalacja i aktualizacja jedną komendą.

.DESCRIPTION
  W PowerShell:  irm https://github.com/wiQ1999/descent-lektor-pl/releases/latest/download/instaluj-win.ps1 | iex

  Pobiera manifest lektor-win.json z tego samego miejsca co skrypt i części paczki, których brakuje
  w instalacji (stan\pakiet.json), sprawdza ich sumy SHA-256 i rozpakowuje je do stałego folderu
  %USERPROFILE%\Descent-Lektor-PL. Pierwsza instalacja instaluje lektora w grze (skrypty\lektor.ps1 -Install);
  aktualizacja podmienia tylko zmienione części, usuwa pliki, których nowa wersja już nie ma, zachowuje
  ustawienia (scalone z nowymi domyślnymi), zgłoszenia, dzienniki i stan włączenia lektora.

  Zmienne środowiskowe (albo parametry, gdy skrypt jest uruchomiony z pliku):
    LEKTOR_ZRODLO  adres albo folder z manifestem i częściami (domyślnie najnowsze wydanie na GitHub)
    LEKTOR_FOLDER  folder lektora (domyślnie %USERPROFILE%\Descent-Lektor-PL)
    LEKTOR_GRA     folder gry, gdy instalator nie znajdzie jej w Steam
#>
param(
    [string] $Zrodlo = $env:LEKTOR_ZRODLO,
    [string] $Folder = $env:LEKTOR_FOLDER,
    [string] $Gra = $env:LEKTOR_GRA
)

try { & {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'
    $Release = 'https://github.com/wiQ1999/descent-lektor-pl/releases/latest/download'
    $ManifestName = 'lektor-win.json'
    $Defaults = 'skrypty\ustawienia.domyslne.toml'
    $GameProcess = 'Legends of the Dark'
    $GameExe = 'Legends of the Dark.exe'
    $AppId = '1611070'

    function Say([string] $msg, [string] $color = 'Gray') { Write-Host $msg -ForegroundColor $color }

    function Get-Source([string] $name, [string] $dest) {
        if ($Zrodlo -notmatch '^https?://') {
            Copy-Item -LiteralPath (Join-Path $Zrodlo $name) -Destination $dest -Force
            return
        }
        $url = $Zrodlo.TrimEnd('/') + '/' + [uri]::EscapeDataString($name)
        $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
        if ($curl) {
            # -C -: wznawia przerwane pobieranie części; pasek postępu tylko dla dużych plików
            $bar = if ($name -like '*.zip') { '--progress-bar' } else { '--silent' }
            & $curl.Source -fL --retry 3 --show-error $bar -C - -o $dest $url
            if ($LASTEXITCODE -ne 0) { throw "Nie udało się pobrać $url (curl, kod $LASTEXITCODE)." }
            return
        }
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072
        (New-Object System.Net.WebClient).DownloadFile($url, $dest)
    }

    function Read-Json([string] $path) {
        [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    }

    function Get-Sha256([string] $path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }

    function Format-Size([double] $bytes) {
        if ($bytes -ge 1GB) { return '{0:N1} GB' -f ($bytes / 1GB) }
        '{0:N0} MB' -f [math]::Max(1, $bytes / 1MB)
    }

    # Rozpakowuje z części tylko pliki z listy manifestu (bez plików przykrytych przez późniejsze warstwy).
    function Expand-Part([string] $zip, $files, [string] $root) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $want = New-Object 'System.Collections.Generic.HashSet[string]'
        foreach ($f in $files) { [void]$want.Add($f) }
        $archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
        try {
            foreach ($e in $archive.Entries) {
                if (-not $want.Contains($e.FullName)) { continue }
                $dest = Join-Path $root ($e.FullName -replace '/', '\')
                $dir = Split-Path -Parent $dest
                if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
                [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, $dest, $true)
            }
        }
        finally { $archive.Dispose() }
    }

    # Ustawienia: nowy plik domyślny z wartościami użytkownika dla kluczy, które ma w swoim pliku.
    function Merge-Settings([string] $user, [string] $defaults) {
        $mine = @{}
        $section = ''
        foreach ($line in [System.IO.File]::ReadAllLines($user, [System.Text.Encoding]::UTF8)) {
            if ($line -match '^\s*\[([^\]]+)\]') { $section = $Matches[1].Trim(); continue }
            if ($line -match '^\s*([A-Za-z0-9_\-]+)\s*=') {
                $key = "$section.$($Matches[1])"
                if ($key -notin '.db', '.audio') { $mine[$key] = $line }    # baza i audio zawsze z nowej wersji
            }
        }
        $section = ''
        $out = foreach ($line in [System.IO.File]::ReadAllLines($defaults, [System.Text.Encoding]::UTF8)) {
            if ($line -match '^\s*\[([^\]]+)\]') { $section = $Matches[1].Trim() }
            elseif ($line -match '^\s*([A-Za-z0-9_\-]+)\s*=' -and $mine.ContainsKey("$section.$($Matches[1])")) {
                $line = $mine["$section.$($Matches[1])"]
            }
            $line
        }
        [System.IO.File]::WriteAllText($user, (($out -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding $false))
    }

    function Invoke-Lektor([string] $root, [string[]] $arguments) {
        $script = Join-Path $root 'skrypty\lektor.ps1'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script @arguments
        if ($LASTEXITCODE -ne 0) { throw 'Instalacja w grze nie powiodła się (komunikat powyżej).' }
    }

    # Folder gry: ze stanu instalacji, z bibliotek Steam (jak lektor.ps1) albo od gracza.
    function Find-Game {
        if ($Gra) { return (Resolve-Path -LiteralPath $Gra).Path }
        $stateFile = Join-Path $state 'instalacja.txt'
        if (Test-Path -LiteralPath $stateFile) {
            $m = Select-String -LiteralPath $stateFile -Pattern '^game=(.+)$' -Encoding UTF8 | Select-Object -First 1
            if ($m -and (Test-Path -LiteralPath (Join-Path $m.Matches[0].Groups[1].Value $GameExe))) { return $m.Matches[0].Groups[1].Value }
        }
        $libs = New-Object System.Collections.Generic.List[string]
        foreach ($key in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam') {
            $p = Get-ItemProperty -Path $key -ErrorAction SilentlyContinue
            $steam = if ($p -and $p.SteamPath) { $p.SteamPath } elseif ($p -and $p.InstallPath) { $p.InstallPath } else { $null }
            if (-not $steam) { continue }
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

    # Przed pobraniem: czy w grze nie ma lektora z innego folderu albo innego loadera modów.
    # Lektor zostawia w folderze gry doorstop_config.ini z wierszem target_assembly=<folder lektora>\plugin\LektorPL.Loader.dll.
    function Assert-GameReady([string] $game) {
        $cfg = Join-Path $game 'doorstop_config.ini'
        $text = if (Test-Path -LiteralPath $cfg) { Get-Content -LiteralPath $cfg -Raw } else { '' }
        $m = [regex]::Match($text, '(?m)^target_assembly=(.+?)\\plugin\\LektorPL\.Loader\.dll\s*$')
        if ($m.Success) {
            $other = $m.Groups[1].Value
            if ([System.IO.Path]::GetFullPath($other).TrimEnd('\') -eq $Folder.TrimEnd('\')) { return }
            $uninstall = Join-Path $other 'skrypty\lektor.ps1'
            Say ''
            Say "W grze jest lektor zainstalowany z innego folderu: $other" Yellow
            if (-not (Test-Path -LiteralPath $uninstall)) {
                throw ("Tamtego folderu już nie ma, a w folderze gry zostały pliki lektora. Usuń z folderu gry pliki " +
                    "winhttp.dll, .doorstop_version i doorstop_config.ini i uruchom instalację ponownie.")
            }
            $answer = Read-Host 'Odinstalować go teraz? Ustawienia i zgłoszenia z tamtego folderu nie przejdą do nowego. [T/N]'
            if ($answer.Trim() -notmatch '^[TtYy]') { throw "Instalacja przerwana. Odinstaluj lektora plikiem Odinstaluj.cmd w folderze $other i uruchom instalację ponownie." }
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $uninstall -Uninstall
            if ($LASTEXITCODE -ne 0) { throw "Odinstalowanie z folderu $other nie powiodło się (komunikat powyżej)." }
            Say "Stary folder możesz teraz usunąć: $other" Green
            Say ''
            return
        }
        $foreign = @('winhttp.dll', 'doorstop_config.ini', '.doorstop_version', 'version.dll', 'BepInEx', 'MelonLoader' |
                Where-Object { Test-Path -LiteralPath (Join-Path $game $_) })
        if ($foreign -and -not (Test-Path -LiteralPath (Join-Path $state 'instalacja.txt'))) {
            throw ("W folderze gry jest inny loader modów: {0}. Lektor PL nie nadpisuje cudzych plików. " +
                "Odinstaluj tamten mod (albo usuń te pliki) i uruchom instalację ponownie.") -f ($foreign -join ', ')
        }
    }

    if (-not $Zrodlo) { $Zrodlo = $Release }
    if (-not $Folder) { $Folder = Join-Path $env:USERPROFILE 'Descent-Lektor-PL' }
    $Folder = [System.IO.Path]::GetFullPath($Folder)
    $state = Join-Path $Folder 'stan'
    $installedPath = Join-Path $state 'pakiet.json'
    $downloads = Join-Path $state 'pobrane'

    Say 'Lektor PL: instalacja i aktualizacja' Cyan
    if (Get-Process -Name $GameProcess -ErrorAction SilentlyContinue) {
        throw 'Gra jest uruchomiona. Zamknij ją i uruchom instalację ponownie.'
    }
    $game = Find-Game
    Say "Gra: $game"
    Assert-GameReady $game
    New-Item -ItemType Directory -Force -Path $downloads | Out-Null
    $manifestPath = Join-Path $downloads $ManifestName
    Remove-Item -LiteralPath $manifestPath -Force -ErrorAction SilentlyContinue
    Get-Source $ManifestName $manifestPath
    $manifest = Read-Json $manifestPath
    if ($manifest.format -ne 1 -or $manifest.platform -ne 'win') { throw 'Ten instalator nie obsługuje pobranego manifestu. Pobierz najnowszy instalator.' }

    $installed = if (Test-Path -LiteralPath $installedPath) { Read-Json $installedPath } else { $null }
    $upgrade = [bool]$installed
    if ($upgrade -and $installed.id -eq $manifest.id) {
        Say "Lektor jest aktualny: $($manifest.version)" Green
        Say "Folder: $Folder"
        Invoke-Lektor $Folder @('-Install', '-Upgrade', '-GameDir', $game)
        Remove-Item -LiteralPath $downloads -Recurse -Force
        return
    }
    $have = @{}
    if ($upgrade) { foreach ($p in $installed.parts) { $have[$p.sha256] = $true } }
    $todo = @($manifest.parts | Where-Object { -not $have.ContainsKey($_.sha256) })
    $bytes = ($todo | Measure-Object -Property size -Sum).Sum
    if ($upgrade) { Say "Aktualizacja: $($installed.version)  ->  $($manifest.version)" }
    else { Say "Nowa instalacja: $($manifest.version)" }
    Say "Folder: $Folder"
    Say ("Do pobrania: {0} z {1} części, {2}" -f $todo.Count, @($manifest.parts).Count, (Format-Size $bytes))

    $drive = Get-PSDrive -Name $Folder.Substring(0, 1) -ErrorAction SilentlyContinue
    $largest = ($todo | Measure-Object -Property size -Maximum).Maximum
    if ($drive -and $drive.Free -lt ($bytes + $largest + 200MB)) {
        throw ("Za mało miejsca na dysku {0}: potrzeba ok. {1}, wolne {2}." -f $drive.Name, (Format-Size ($bytes + $largest + 200MB)), (Format-Size $drive.Free))
    }

    $i = 0
    foreach ($part in $todo) {
        $i++
        Say ("[{0}/{1}] {2} ({3})" -f $i, $todo.Count, $part.name, (Format-Size $part.size))
        $zip = Join-Path $downloads $part.name
        if (-not ((Test-Path -LiteralPath $zip) -and (Get-Item -LiteralPath $zip).Length -eq $part.size)) {
            Get-Source $part.name $zip
        }
        if ((Get-Sha256 $zip) -ne $part.sha256) {
            Remove-Item -LiteralPath $zip -Force
            throw "Pobrany plik $($part.name) ma złą sumę SHA-256. Uruchom instalację ponownie."
        }
        Expand-Part $zip $part.files $Folder
        Remove-Item -LiteralPath $zip -Force
    }

    $removed = 0
    if ($upgrade) {
        $keep = New-Object 'System.Collections.Generic.HashSet[string]'
        foreach ($p in $manifest.parts) { foreach ($f in $p.files) { [void]$keep.Add($f) } }
        foreach ($p in $installed.parts) {
            foreach ($f in $p.files) {
                if ($keep.Contains($f)) { continue }
                $full = Join-Path $Folder ($f -replace '/', '\')
                if (Test-Path -LiteralPath $full) { Remove-Item -LiteralPath $full -Force; $removed++ }
            }
        }
    }

    $settings = Join-Path $Folder 'ustawienia.toml'
    $fresh = Join-Path $Folder $Defaults
    if (Test-Path -LiteralPath $settings) {
        Copy-Item -LiteralPath $settings -Destination (Join-Path $state 'ustawienia.przed-aktualizacja.toml') -Force
        Merge-Settings $settings $fresh
        Say 'Ustawienia zachowane (nowe opcje dostały wartości domyślne).'
    }
    else { Copy-Item -LiteralPath $fresh -Destination $settings }
    if ($removed) { Say "Usunięto pliki poprzedniej wersji: $removed" }

    $arguments = @('-Install', '-Quiet')
    if ($upgrade) { $arguments += '-Upgrade' }
    $arguments += @('-GameDir', $game)
    Invoke-Lektor $Folder $arguments

    Copy-Item -LiteralPath $manifestPath -Destination $installedPath -Force
    Remove-Item -LiteralPath $downloads -Recurse -Force
    Say ''
    if ($upgrade) { Say "Zaktualizowano do: $($manifest.version)" Green }
    else { Say "Zainstalowano: $($manifest.version)" Green }
    Say "Pliki lektora (Ustawienia, Test dźwięku, Odinstaluj): $Folder"
    Say 'Uruchom grę normalnie ze Steama: lektor wystartuje razem z nią.'
    Say 'Aktualizacja: ta sama komenda. Folderu lektora nie przenoś.'
} }
catch {
    # bez exit: przy `irm ... | iex` zamknąłby okno PowerShell
    Write-Host ''
    Write-Host "Błąd: $($_.Exception.Message)" -ForegroundColor Red
}
