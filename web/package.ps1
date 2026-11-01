param([string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $PSScriptRoot 'artifacts' }
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
# Explicit allowlist: no old saves, uploads, database, venv, model packages, or secrets.
$staging = Join-Path $OutputDirectory ('treecourt-web-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $staging -Force | Out-Null
$folders = @('web/backend','web/frontend','web/tests','data/curriculum','data/cinematics','assets/portraits','ue5','blender','mcp','docs')
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path (Join-Path $staging $folder) -Force | Out-Null
}
$groups = @(
    @{Folder='web/backend'; Pattern='*.py'},
    @{Folder='web/frontend'; Pattern='*'},
    @{Folder='web/tests'; Pattern='*.py'},
    @{Folder='web/tests'; Pattern='*.mjs'},
    @{Folder='data/curriculum'; Pattern='*.json'},
    @{Folder='data/cinematics'; Pattern='*.json'},
    @{Folder='assets/portraits'; Pattern='*.png'},
    @{Folder='ue5'; Pattern='*.md'},
    @{Folder='blender'; Pattern='*.md'},
    @{Folder='mcp'; Pattern='*.md'},
    @{Folder='docs'; Pattern='*.md'}
)
foreach ($group in $groups) {
    Get-ChildItem -LiteralPath (Join-Path $projectRoot $group.Folder) -Filter $group.Pattern -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $staging $group.Folder)
    }
}
foreach ($file in @('web/start.ps1','web/package.ps1','web/requirements.txt','web/requirements.lock.txt','web/README.md','data/teaching-policy.json','assets/bg_dawn.jpg','assets/bg_noon.jpg','assets/bg_dusk.jpg','assets/bg_night.jpg')) {
    Copy-Item -LiteralPath (Join-Path $projectRoot $file) -Destination (Join-Path $staging $file)
}
# Find the root launcher without relying on PowerShell 5's script encoding for its Chinese name.
Get-ChildItem -LiteralPath $projectRoot -Filter '*.bat' -File | Where-Object {
    (Get-Content -LiteralPath $_.FullName -Raw) -like '*web\start.ps1*'
} | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $staging }
Copy-Item -LiteralPath (Join-Path $projectRoot 'web/README.md') -Destination (Join-Path $staging 'README.md')
$archive = "$staging.zip"
# 成片单独列入白名单，不带入原视频、逐帧缓存、原始音轨或 Blender 工程。
$filmSpec = Get-Content -LiteralPath (Join-Path $projectRoot 'data/cinematics/phainon-wheat.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$filmFolder = Join-Path $projectRoot $filmSpec.output_dir
if ((Test-Path -LiteralPath (Join-Path $filmFolder 'verification.json')) -and (Test-Path -LiteralPath (Join-Path $filmFolder 'phainon-wheat-74s.mp4'))) {
    $filmTarget = Join-Path $staging $filmSpec.output_dir
    New-Item -ItemType Directory -Force -Path $filmTarget | Out-Null
    foreach ($filmAsset in @('phainon-wheat-74s.mp4','interactive.mp4','poster.jpg','verification.json','waymark-next_place.mp4','waymark-blank.mp4','name-call_you.mp4','name-stay.mp4')) {
        Copy-Item -LiteralPath (Join-Path $filmFolder $filmAsset) -Destination $filmTarget
    }
}
Compress-Archive -LiteralPath $staging -DestinationPath $archive
Write-Host "Package: $archive"
