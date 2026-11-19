# Lektor PL (Windows): starter instalacji i aktualizacji.
#   irm https://github.com/wiQ1999/descent-lektor-pl/releases/latest/download/instaluj-win.ps1 | iex
#
# Tylko ASCII: irm dekoduje plik z wydania jako ISO-8859-1, wiec polskie litery i BOM by sie zepsuly.
# Starter pobiera wlasciwy instalator (instalator-win.ps1, UTF-8 z BOM) jako plik i uruchamia go przez -File.
# Bez exit: przy `| iex` zamknalby okno PowerShell. Zmienne LEKTOR_ZRODLO, LEKTOR_FOLDER i LEKTOR_GRA
# przechodza do instalatora (opis w instalator-win.ps1).
try {
    $ErrorActionPreference = 'Stop'
    $src = if ($env:LEKTOR_ZRODLO) { $env:LEKTOR_ZRODLO } else { 'https://github.com/wiQ1999/descent-lektor-pl/releases/latest/download' }
    $env:LEKTOR_ZRODLO = $src
    $dest = Join-Path $env:TEMP 'lektor-pl-instalator-win.ps1'
    if ($src -match '^https?://') {
        $url = $src.TrimEnd('/') + '/instalator-win.ps1'
        if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
            & curl.exe -fsSL --retry 3 -o $dest $url
            if ($LASTEXITCODE -ne 0) { throw "curl $LASTEXITCODE, $url" }
        }
        else {
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072
            (New-Object System.Net.WebClient).DownloadFile($url, $dest)
        }
    }
    else { Copy-Item -LiteralPath (Join-Path $src 'instalator-win.ps1') -Destination $dest -Force }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $dest
    Remove-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
}
catch {
    Write-Host ''
    Write-Host "Blad: $($_.Exception.Message)" -ForegroundColor Red
}
