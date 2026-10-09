# One-time setup: installs Git + GitHub CLI, logs in to GitHub and puts the project on your Desktop.
# Paste into PowerShell:
#   irm https://raw.githubusercontent.com/noiseparty/hakatons/main/easy/setup.ps1 | iex
& {
  function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') }
  Refresh-Path

  foreach ($app in @(@{ cmd = 'git'; id = 'Git.Git' }, @{ cmd = 'gh'; id = 'GitHub.cli' })) {
    if (-not (Get-Command $app.cmd -ErrorAction SilentlyContinue)) {
      Write-Host "Installing $($app.id)... (click Yes if Windows asks)" -ForegroundColor Cyan
      winget install --id $app.id -e --accept-source-agreements --accept-package-agreements
      Refresh-Path
    }
  }
  if (-not (Get-Command gh -ErrorAction SilentlyContinue) -or -not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host 'Installation did not finish. Close PowerShell, open it again and re-run the setup line.' -ForegroundColor Red
    return
  }

  gh auth status *> $null
  if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host 'Logging in to GitHub: copy the code shown below, then press Enter - a browser opens; paste the code and click Authorize.' -ForegroundColor Cyan
    gh auth login -h github.com -p https -w
    if ($LASTEXITCODE -ne 0) { Write-Host 'GitHub login failed. Re-run the setup line to try again.' -ForegroundColor Red; return }
  }
  gh auth setup-git

  $login = gh api user --jq .login
  $id = gh api user --jq .id

  $dir = Join-Path ([Environment]::GetFolderPath('Desktop')) 'hakatons'
  if (-not (Test-Path (Join-Path $dir '.git'))) {
    Write-Host "Downloading the project to $dir ..." -ForegroundColor Cyan
    gh repo clone noiseparty/hakatons $dir
    if ($LASTEXITCODE -ne 0) { Write-Host 'Download failed. Are you added as a collaborator on GitHub?' -ForegroundColor Red; return }
  }

  # So GitHub shows your commits under your username
  git -C $dir config user.name $login
  git -C $dir config user.email "$id+$login@users.noreply.github.com"

  Write-Host ''
  Write-Host "All set, $login! The project is in: $dir" -ForegroundColor Green
  Write-Host 'Next: read easy\README.md there. Day to day you only need easy\update.cmd and easy\save.cmd.'
  explorer $dir
}
