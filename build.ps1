# Builds build\KeystrokesOverlay.exe (single portable file, .NET Framework 4.x).
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path $csc)) { throw "csc.exe not found at $csc" }

$outDir = Join-Path $root 'build'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$exe = Join-Path $outDir 'KeystrokesOverlay.exe'

if (-not (Test-Path (Join-Path $root 'assets\app.ico'))) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'assets\make-icon.ps1') | Out-Null
}

$sources = Get-ChildItem (Join-Path $root 'src') -Filter *.cs | ForEach-Object { $_.FullName }

$args = @(
    '/nologo'
    '/target:winexe'
    '/platform:anycpu'
    '/optimize+'
    '/langversion:5'
    "/out:$exe"
    ('/win32icon:' + (Join-Path $root 'assets\app.ico'))
    ('/res:' + (Join-Path $root 'assets\JetBrainsMono-Bold.ttf') + ',JetBrainsMono-Bold.ttf')
    ('/res:' + (Join-Path $root 'assets\JetBrainsMono-Medium.ttf') + ',JetBrainsMono-Medium.ttf')
    ('/res:' + (Join-Path $root 'assets\app.ico') + ',app.ico')
    '/r:System.dll'
    '/r:System.Core.dll'
    '/r:System.Drawing.dll'
    '/r:System.Windows.Forms.dll'
) + $sources

& $csc $args
if ($LASTEXITCODE -ne 0) { throw "build failed (exit $LASTEXITCODE)" }

Write-Output ('built: ' + $exe + ' (' + [math]::Round((Get-Item $exe).Length / 1KB) + ' KB)')
