param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ArtifactName = "HandoffGuard-Installer-v0.1.0"

Push-Location $ProjectRoot
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name $ArtifactName `
        --add-data "runtime/custom-instructions.txt;runtime" `
        installer.py
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
    $ArtifactPath = Join-Path $ProjectRoot "dist\$ArtifactName.exe"
    $ChecksumPath = Join-Path $ProjectRoot "dist\$ArtifactName.sha256"
    $ArtifactHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ArtifactPath).Hash.ToLowerInvariant()
    Set-Content -LiteralPath $ChecksumPath -Value "$ArtifactHash  $ArtifactName.exe" -Encoding ascii
} finally {
    Pop-Location
}
