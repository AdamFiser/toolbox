# Manes

# Synchronizace s Active Directory

Script je nutné spustit pro:

- list_user.username
- manes_employee_user.userNameAD

V powershell
`powershell.exe -ExecutionPolicy Bypass -File .\Fix-ADUserNameCase.ps1 -Credential (Get-Credential "czech\svc_ldap") -SearchBase "DC=czech,DC=awt,DC=eu" -Server "czech.awt.eu" -OutputFile "C:\temp\fix.sql"`