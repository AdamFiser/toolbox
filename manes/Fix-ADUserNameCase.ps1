<#
.SYNOPSIS
    Vytáhne sAMAccountName všech aktivních AD účtů a vygeneruje SQL UPDATE příkazy
    pro opravu velikosti písmen v tabulce manes.dbo.manes_employee_user.
    Nevyžaduje RSAT – používá přímo .NET System.DirectoryServices.

.PARAMETER Server
    FQDN nebo IP adresa řadiče domény. Pokud není zadán, použije se výchozí DC domény.

.PARAMETER SearchBase
    OU, ve které se hledá (distinguishedName formát).
    Příklad: "OU=Users,DC=pkpcargointernational,DC=com"
    Pokud není zadán, prohledá se celá doména.

.PARAMETER OutputFile
    Cesta k výstupnímu .sql souboru. Výchozí: .\fix_username_case.sql

.EXAMPLE
    .\Fix-ADUserNameCase.ps1
    .\Fix-ADUserNameCase.ps1 -Server "dc01.pkpcargointernational.com"
    .\Fix-ADUserNameCase.ps1 -Server "dc01.pkpcargointernational.com" -SearchBase "OU=Users,DC=pkpcargointernational,DC=com"
#>

[CmdletBinding()]
param(
    [string]$Server      = $null,
    [string]$SearchBase  = $null,
    [string]$OutputFile  = ".\fix_username_case.sql",

    [Parameter(Mandatory = $false)]
    [System.Management.Automation.PSCredential]
    [System.Management.Automation.Credential()]
    $Credential = $null
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# 1. Přihlašovací údaje
# ---------------------------------------------------------------------------
if ($Credential -eq $null) {
    Write-Host "Zadej přihlašovací údaje pro čtení Active Directory:" -ForegroundColor Cyan
    $Credential = Get-Credential
}

$username = $Credential.UserName
$password = $Credential.GetNetworkCredential().Password

# ---------------------------------------------------------------------------
# 2. Sestavení LDAP cesty
# ---------------------------------------------------------------------------
if ($Server) {
    $ldapRoot = "LDAP://$Server"
} else {
    # Automatické zjištění domény z prostředí
    $domain = [System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain()
    $ldapRoot = "LDAP://$($domain.Name)"
}

if ($SearchBase) {
    $ldapPath = "$ldapRoot/$SearchBase"
} else {
    $ldapPath = $ldapRoot
}

Write-Host "Připojuji se na: $ldapPath" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 3. LDAP dotaz přes DirectorySearcher
# ---------------------------------------------------------------------------
try {
    $entry    = New-Object System.DirectoryServices.DirectoryEntry($ldapPath, $username, $password)
    $searcher = New-Object System.DirectoryServices.DirectorySearcher($entry)

    # Filtr: pouze povolené uživatelské účty
    # userAccountControl bit 2 = ACCOUNTDISABLE → vylučujeme ho
    $searcher.Filter = "(&(objectClass=user)(objectCategory=person)(!userAccountControl:1.2.840.113556.1.4.803:=2))"

    # Načíst pouze sAMAccountName
    [void]$searcher.PropertiesToLoad.Add("sAMAccountName")

    # Stránkování – důležité pro velké AD (výchozí limit je 1000)
    $searcher.PageSize = 500

    Write-Host "Spouštím LDAP dotaz..." -ForegroundColor Cyan
    $results = $searcher.FindAll()

} catch {
    Write-Error "Chyba při připojení k AD: $_"
    exit 1
}

# ---------------------------------------------------------------------------
# 4. Zpracování výsledků
# ---------------------------------------------------------------------------
$samList = [System.Collections.Generic.List[string]]::new()

foreach ($result in $results) {
    $sam = $result.Properties["sAMAccountName"][0]
    if ($sam) {
        $samList.Add($sam)
    }
}

$results.Dispose()

$count = $samList.Count
Write-Host "Nalezeno $count aktivních účtů." -ForegroundColor Green

if ($count -eq 0) {
    Write-Warning "Žádné účty nenalezeny. Zkontroluj SearchBase nebo připojení k AD."
    exit 0
}

# ---------------------------------------------------------------------------
# 5. Generování SQL příkazů
# ---------------------------------------------------------------------------
$lines = [System.Collections.Generic.List[string]]::new()

$lines.Add("-- ============================================================")
$lines.Add("-- Oprava velikosti písmen userNameAD dle Active Directory")
$lines.Add("-- Vygenerováno: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lines.Add("-- Počet účtů:   $count")
$lines.Add("-- ============================================================")
$lines.Add("")
$lines.Add("USE manes;")
$lines.Add("GO")
$lines.Add("")

foreach ($sam in ($samList | Sort-Object)) {

    # Ochrana proti SQL injection – apostrof zdvojit, podezřelé znaky přeskočit
    if ($sam -match '[;`"\\]') {
        Write-Warning "Přeskakuji účet s neočekávanými znaky: '$sam'"
        continue
    }

    $samEscaped = $sam -replace "'", "''"

    $lines.Add("UPDATE dbo.manes_employee_user")
    $lines.Add("    SET  userNameAD = N'$samEscaped'")
    $lines.Add("    WHERE userNameAD LIKE '$samEscaped';")
    $lines.Add("")
}

$lines.Add("-- Konec skriptu")

# ---------------------------------------------------------------------------
# 6. Zápis do souboru
# ---------------------------------------------------------------------------
$outputDir = Split-Path -Parent $OutputFile
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$lines | Set-Content -Path $OutputFile -Encoding UTF8

$updateCount = ($lines | Where-Object { $_ -match "^UPDATE" } | Measure-Object).Count

Write-Host ""
Write-Host "SQL skript uložen do: $OutputFile" -ForegroundColor Green
Write-Host "Celkem vygenerováno UPDATE příkazů: $updateCount" -ForegroundColor Green
Write-Host ""
Write-Host "Před spuštěním SQL doporučuji:" -ForegroundColor Yellow
Write-Host "  1. Prohlednout výstupní soubor" -ForegroundColor Yellow
Write-Host "  2. Spustit nejdříve SELECT pro ověření počtu dotčených řádků" -ForegroundColor Yellow
Write-Host "  3. Spustit v transakci s BEGIN TRAN / ROLLBACK pro testování" -ForegroundColor Yellow