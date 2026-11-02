<#
.SYNOPSIS
  Tworzy kopię MonoMod.Utils.dll z BepInEx 5.4.23.5 bez zapisu flagi corlib_internal (crash przy wyjściu, D40, D54).

.DESCRIPTION
  MonoMod.Utils 22.1.29.1, Extensions.SetMonoCorlibInternal: przesunięcie pola corlib_internal w strukturze MonoAssembly
  jest liczone bez pola ignores_checks_assembly_names, które ma Mono z Unity 2022.3. Na x86 bajt 1 trafia w najstarszy
  bajt tego wskaźnika (+0x4F zamiast +0x53), a mono_domain_free przy wyjściu z gry zwalnia uszkodzoną listę
  (MonoMod #329, poprawione w MonoMod 25 przez PR #330).

  Kopia różni się jedną instrukcją: końcowe stind.i1 zamieniam na dwa pop. Reszta metody (pamięć podręczna
  ReflectionHelper.AssemblyCache) działa bez zmian. Flaga i tak nie trafiała w swoje pole, więc Harmony działa jak dotąd.
  Źródłem jest paczka BepInEx ze sprawdzoną sumą SHA-256. Wynik trafia do analysis\work\bin (poza repozytorium),
  folder gry zostaje nietknięty; poprawkę w grze nakłada lektor-hook.ps1 -MonoModFix.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File src\plugin\install\monomod-fix.ps1
#>
param([switch] $Force)
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Bin = Join-Path $RepoRoot 'analysis\work\bin\BepInEx-5.4.23.5'
$Zip = Join-Path $Bin 'BepInEx_win_x86_5.4.23.5.zip'
$ZipSha256 = '37651C79E40D6F909572A4F461AC25350BB3EF8FE7FBD29F1AA8791A33B84C82'
$OrigSha256 = '9D1495F147AC93C4F81F84538C1A326E8F8A6AEFC78D6289D798F3CE1162C5E9'
$OutDir = Join-Path $Bin 'monomod-fix'
$Out = Join-Path $OutDir 'MonoMod.Utils.dll'

if ((Test-Path -LiteralPath $Out) -and -not $Force) { Write-Host "Kopia już jest: $Out (-Force tworzy ją od nowa)"; return }
$hash = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash
if ($hash -ne $ZipSha256) { throw "Zła suma SHA-256 paczki BepInEx: $hash" }

$staging = Join-Path $OutDir 'staging'
if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
Expand-Archive -LiteralPath $Zip -DestinationPath $staging
$core = Join-Path $staging 'BepInEx\core'
$src = Join-Path $core 'MonoMod.Utils.dll'
$hash = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
if ($hash -ne $OrigSha256) { throw "Nieoczekiwana wersja MonoMod.Utils.dll: $hash" }

# Wczytanie z bajtów nie blokuje pliku, więc katalog roboczy da się potem usunąć.
[void][System.Reflection.Assembly]::Load([System.IO.File]::ReadAllBytes((Join-Path $core 'Mono.Cecil.dll')))
$resolver = New-Object Mono.Cecil.DefaultAssemblyResolver
$resolver.AddSearchDirectory($core)
$rp = New-Object Mono.Cecil.ReaderParameters
$rp.AssemblyResolver = $resolver
$rp.InMemory = $true
$asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($src, $rp)

$type = $asm.MainModule.GetType('MonoMod.Utils.Extensions')
$method = @($type.Methods | Where-Object { $_.Name -eq 'SetMonoCorlibInternal' })
if ($method.Count -ne 1) { throw "Oczekiwałem jednej metody SetMonoCorlibInternal, jest $($method.Count)" }
$body = $method[0].Body
$stores = @($body.Instructions | Where-Object { $_.OpCode.Code -eq [Mono.Cecil.Cil.Code]::Stind_I1 })
if ($stores.Count -ne 1) { throw "Oczekiwałem jednego stind.i1, jest $($stores.Count)" }
$store = $stores[0]
if ($store.Next.OpCode.Code -ne [Mono.Cecil.Cil.Code]::Ret) { throw 'Po stind.i1 nie ma ret: inna wersja metody' }

# Zamiana w miejscu zachowuje skoki do tej instrukcji (br.s z gałęzi value == false).
$store.OpCode = [Mono.Cecil.Cil.OpCodes]::Pop
$store.Operand = $null
$body.GetILProcessor().InsertAfter($store, [Mono.Cecil.Cil.Instruction]::Create([Mono.Cecil.Cil.OpCodes]::Pop))

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$asm.Write($Out)
$asm.Dispose()
$resolver.Dispose()
Remove-Item -LiteralPath $staging -Recurse -Force
$patched = (Get-FileHash -LiteralPath $Out -Algorithm SHA256).Hash
Write-Host "Zapisano $Out"
Write-Host "SHA-256: $patched" -ForegroundColor Green
