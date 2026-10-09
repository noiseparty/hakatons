# Save your work: commit it, publish it to GitHub and merge it into main, in one go.
#   Double-click easy\save.cmd, or (AI agents):
#   powershell -NoProfile -ExecutionPolicy Bypass -File easy\save.ps1 "what I did"
param([string]$Message)

$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
Set-Location (Split-Path $PSScriptRoot -Parent)

function Fail($text) { Write-Host ''; Write-Host $text -ForegroundColor Red; exit 1 }

function Slug($s) {
  $plain = ($s.Normalize([Text.NormalizationForm]::FormD).ToCharArray() |
    Where-Object { [Globalization.CharUnicodeInfo]::GetUnicodeCategory($_) -ne 'NonSpacingMark' }) -join ''
  $x = ($plain.ToLower() -replace '[^a-z0-9]+', '-').Trim('-')
  if ($x.Length -gt 40) { $x = $x.Substring(0, 40).Trim('-') }
  if (-not $x) { $x = 'work' }
  "$x-" + (Get-Date -Format 'MMdd-HHmm')
}

$login = gh api user --jq .login
if ($LASTEXITCODE -ne 0 -or -not $login) { Fail 'You are not logged in to GitHub. Run the setup again (see easy\README.md).' }

$dirty = [bool](git status --porcelain)
git fetch -q origin
$branch = git branch --show-current
$ahead = [int](git rev-list --count origin/main..HEAD)
if (-not $dirty -and $ahead -eq 0) { Write-Host 'Nothing to save - no changes since your last save.' -ForegroundColor Yellow; exit 0 }

if (-not $Message) { $Message = Read-Host 'What did you do? (one short sentence)' }
$Message = "$Message".Trim()
if (-not $Message) { Fail 'Please write a short description of what you did.' }

# main is protected, so work always goes through a branch + pull request
if ($branch -eq 'main') {
  $branch = "$login/" + (Slug $Message)
  git switch -q -c $branch
  if ($LASTEXITCODE -ne 0) { Fail 'Could not create a branch for your work.' }
  git branch -f main origin/main
}

if ($dirty) {
  git add -A
  git commit -q -m $Message
  if ($LASTEXITCODE -ne 0) { Fail 'Could not commit your changes.' }
}

Write-Host "Getting your teammates' latest changes..."
git rebase -q origin/main
if ($LASTEXITCODE -ne 0) {
  git rebase --abort
  Fail "Your changes and a teammate's changes touch the same lines, so they can't be combined automatically.`nNothing is lost: your work is saved on your computer on branch '$branch'.`nAsk your AI assistant or a teammate to resolve the conflict."
}

# Log the work in TODO.md (top of the Done section)
$todo = Join-Path (Get-Location) 'TODO.md'
if (Test-Path $todo) {
  $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm zzz'
  $line = "- [x] $Message " + [char]0x2014 + " done $stamp by $login"
  $text = [IO.File]::ReadAllText($todo)
  $re = [regex]'(?m)^## Done[ \t]*\r?\n'
  $new = $re.Replace($text, { param($m) $m.Value + $line + "`n" }, 1)
  if ($new -ne $text) {
    [IO.File]::WriteAllText($todo, $new, (New-Object Text.UTF8Encoding $false))
    git add TODO.md
    git commit -q -m "TODO: $Message"
  }
}

Write-Host 'Uploading to GitHub...'
git push -q --force-with-lease -u origin HEAD
if ($LASTEXITCODE -ne 0) { Fail 'Upload to GitHub failed. Check your internet connection and try again.' }

$url = gh pr view $branch --json url --jq .url 2>$null
if ($LASTEXITCODE -ne 0 -or -not $url) {
  $url = gh pr create --base main --head $branch --title $Message --body "Saved with easy/save by @$login."
  if ($LASTEXITCODE -ne 0) { Fail 'Your work is on GitHub, but the pull request could not be created. Try saving again.' }
}

Write-Host 'Merging into the shared version...'
gh pr merge $branch --squash --delete-branch
if ($LASTEXITCODE -ne 0) { Fail "Your work is on GitHub but could not be merged automatically:`n$url`nAsk your AI assistant or a teammate to merge it." }

git switch -q main
git pull -q --ff-only
Write-Host ''
Write-Host "Saved! Your work is in the shared version: $url" -ForegroundColor Green
