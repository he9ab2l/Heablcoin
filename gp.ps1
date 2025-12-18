Param(
  [Parameter(Position = 0)]
  [string]$Message = ""
)

$ErrorActionPreference = "Stop"

function Get-NowStamp {
  return (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
}

function Assert-GitRepo {
  & git rev-parse --is-inside-work-tree *> $null
  if ($LASTEXITCODE -ne 0) {
    throw "Not a git repository."
  }
}

function Get-CurrentBranch {
  $branch = (& git rev-parse --abbrev-ref HEAD).Trim()
  if (-not $branch) {
    throw "Cannot determine current git branch."
  }
  return $branch
}

function Has-Changes {
  $status = (& git status --porcelain)
  return -not [string]::IsNullOrWhiteSpace($status)
}

function Run-SecretScan {
  if (-not (Test-Path "scripts/scan_secrets.py")) {
    Write-Host "WARN: scripts/scan_secrets.py not found, skip secret scan."
    return
  }
  & python "scripts/scan_secrets.py" --staged
  if ($LASTEXITCODE -ne 0) {
    throw "Secret scan failed. Fix before committing."
  }
}

Assert-GitRepo

if (-not (Has-Changes)) {
  Write-Host "No changes to commit."
  exit 0
}

if ([string]::IsNullOrWhiteSpace($Message)) {
  $Message = "chore: update ($(Get-NowStamp))"
}

$branch = Get-CurrentBranch

git add -A
Run-SecretScan
git commit -m $Message
git push origin $branch

