<#
Prepare local configuration without overwriting existing secrets.
Does not install dependencies or start services; see README for those steps.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $repoRoot '.env'
if (Test-Path -LiteralPath $envPath) {
    Write-Host '.env already exists; preserving its configuration.'
    exit 0
}

# Generate a unique local credential for each installation without printing it.
$randomBytes = New-Object byte[] 32
$generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $generator.GetBytes($randomBytes) } finally { $generator.Dispose() }
$password = [BitConverter]::ToString($randomBytes).Replace('-', '').ToLowerInvariant()
$template = [IO.File]::ReadAllText((Join-Path $repoRoot '.env.example'))
$content = $template.Replace('replace-with-generated-local-password', $password)
[IO.File]::WriteAllText($envPath, $content, (New-Object System.Text.UTF8Encoding $false))
Write-Host '.env created with a random local password. Do not share or commit it.'
