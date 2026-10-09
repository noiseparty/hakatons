# Get your teammates' latest work.
#   Double-click easy\update.cmd, or (AI agents):
#   powershell -NoProfile -ExecutionPolicy Bypass -File easy\update.ps1

$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
Set-Location (Split-Path $PSScriptRoot -Parent)

function Fail($text) { Write-Host ''; Write-Host $text -ForegroundColor Red; exit 1 }

$branch = git branch --show-current
if ($branch -ne 'main') {
  git fetch -q origin
  $ahead = [int](git rev-list --count origin/main..HEAD)
  if ((git status --porcelain) -or $ahead -gt 0) { Fail "You have unsaved work on '$branch'. Run save first, then update." }
  git switch -q main
}

Write-Host "Getting your teammates' latest changes..."
git pull -q --rebase --autostash
if ($LASTEXITCODE -ne 0) {
  Fail "Your unsaved changes touch the same lines as a teammate's changes.`nNothing is lost, but ask your AI assistant or a teammate to sort it out."
}
Write-Host ''
Write-Host 'Up to date!' -ForegroundColor Green
