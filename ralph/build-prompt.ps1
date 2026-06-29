param(
  [string]$OutputFile
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

if (-not $OutputFile) {
  $OutputFile = Join-Path $ScriptDir "generated-prompt.md"
}

Push-Location $ProjectDir
try {
  $previousErrorActionPreference = $ErrorActionPreference
  $ErrorActionPreference = "SilentlyContinue"
  $commits = & git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>$null
  $gitExitCode = $LASTEXITCODE
  $ErrorActionPreference = $previousErrorActionPreference

  if ($gitExitCode -ne 0 -or -not $commits) {
    $commits = "No commits found"
  }

  $issueFiles = Get-ChildItem -Path (Join-Path $ProjectDir "issues") -Filter "*.md" -File -ErrorAction SilentlyContinue
  if ($issueFiles) {
    $issues = $issueFiles | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName }
    $issues = $issues -join "`n"
  } else {
    $issues = "No issues found"
  }

  $prompt = Get-Content -Raw -LiteralPath (Join-Path $ScriptDir "prompt.md")

  $content = @"
Previous commits:
$commits

Issues:
$issues

$prompt
"@

  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($OutputFile, $content, $utf8NoBom)

  Write-Host "Prompt written to $OutputFile"
} finally {
  Pop-Location
}
