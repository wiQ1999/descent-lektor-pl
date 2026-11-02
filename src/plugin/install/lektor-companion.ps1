<#
.SYNOPSIS
  Uruchamia companion lektora PL przed grą (D46). Plugin w grze łączy się z nim sam i ponawia połączenie.

.DESCRIPTION
  Companion nasłuchuje na 127.0.0.1 (port z %LOCALAPPDATA%\LektorPL\companion.toml, domyślnie 47810)
  i odtwarza audio M1 z analysis\work\audio\m1. Okno zostaw otwarte w czasie gry; Ctrl+C kończy.
  Przy pierwszym uruchomieniu tworzy companion.toml z wartościami domyślnymi (głośność, urządzenie, przełączniki).
  Dziennik (klucze i czasy, bez tekstów): %LOCALAPPDATA%\LektorPL\logs\companion-*.jsonl.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-companion.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-companion.ps1 -Config D:\moj.toml
#>
param(
    [string] $Config
)
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { throw "Brak środowiska projektu: $Python" }
# .venv uruchamia bazowego Pythona z pyvenv.cfg (home). Musi być poza %LOCALAPPDATA% aplikacji Claude (D52).
$BaseHome = (Get-Content -LiteralPath (Join-Path $RepoRoot '.venv\pyvenv.cfg') | Where-Object { $_ -like 'home = *' }) -replace '^home = ', ''
if (-not (Test-Path -LiteralPath (Join-Path $BaseHome 'python.exe'))) { throw "Brak bazowego Pythona środowiska projektu: $BaseHome (pyvenv.cfg)" }

$CompanionArgs = @('-I', '-m', 'lektor', 'companion')
if ($Config) { $CompanionArgs += @('--config', $Config) }
Push-Location $RepoRoot
try { & $Python @CompanionArgs }
finally { Pop-Location }
