# Move repos with 'opakovani' in the name from OA-PVA4-Syllabus to oa-pva4-opakovani
# Requires: gh (GitHub CLI) authenticated with a token having repo/admin perms.

$SourceOrg = "OA-PVA4-Syllabus"
$TargetOrg = "oa-pva4-opakovani"
$NamePattern = "opakovani"   # case-insensitive
$Limit = 1000
$DryRun = $false             # set $true to only print what would happen

Write-Host "Fetching repositories from $SourceOrg ..."
$repos = gh repo list $SourceOrg -L $Limit --json name,isArchived,visibility | ConvertFrom-Json

# filter: name contains 'opakovani' and not archived
$targets = $repos | Where-Object { -not $_.isArchived -and $_.name -match $NamePattern }

if (-not $targets) {
  Write-Warning "No matching repositories found."
  return
}

Write-Host "Will process $($targets.Count) repositories:"
$targets | ForEach-Object { Write-Host " - $($_.name) [$($_.visibility)]" }

if ($DryRun) {
  Write-Host "`nDry-run is ON. No changes will be made."
  return
}

foreach ($r in $targets) {
  $full = "$SourceOrg/$($r.name)"
  Write-Host "`nTransferring $full -> $TargetOrg ..."

  # GitHub REST: POST /repos/{owner}/{repo}/transfer  body: { new_owner, team_ids? }
  $res = gh api `
    --method POST `
    -H "Accept: application/vnd.github+json" `
    -H "X-GitHub-Api-Version: 2022-11-28" `
    "repos/$full/transfer" `
    -f new_owner="$TargetOrg" 2>&1

  if ($LASTEXITCODE -eq 0) {
    Write-Host "  + Transfer requested/accepted."
  } else {
    Write-Warning "  x Failed: $res"
  }
}

Write-Host "`nDone."