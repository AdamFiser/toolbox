# Hromadné vytvoření tagu a release v celé organizaci
# Autor: Adam (běží lokálně ve Windows/PhpStorm Terminalu)

$Org      = "OA-PVA4-Syllabus"
$Tag      = "v2024-2025"
$Title    = "v2024–2025"
$Target   = ""      # prázdné = HEAD na default branch; jinak zadej "main" nebo konkrétní SHA
$Limit    = 1000    # max počet repo ke zpracování
$SkipArchived = $true

Write-Host "Načítám repozitáře v organizaci $Org…"
$reposJson = gh repo list $Org -L $Limit --json name,isArchived,defaultBranchRef
$repos = $reposJson | ConvertFrom-Json

if ($SkipArchived) {
  $repos = $repos | Where-Object { -not $_.isArchived }
}

foreach ($r in $repos) {
  $full = "$Org/$($r.name)"
  $def  = $r.defaultBranchRef.name
  Write-Host "→ $full (default branch: $def)"

  # Už existuje release?
  gh release view $Tag -R $full > $null 2>&1
  if ($LASTEXITCODE -eq 0) {
    Write-Host "  • Release $Tag už existuje – přeskočeno."
    continue
  }

  # Sestav argumenty
  $args = @("release","create",$Tag,"-R",$full,"--title",$Title,"--generate-notes")
  if ($Target -ne "") {
    $args += @("--target",$Target)
  } else {
    # Bez --target se použije HEAD default větve – jen informativně vypíšeme.
    Write-Host "  • Cíl: HEAD na default branch ($def)"
  }

  gh @args | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "  × Nepodařilo se vytvořit release v $full"
  } else {
    Write-Host "  ✓ Vytvořen release $Tag"
  }
}

Write-Host "Hotovo."
