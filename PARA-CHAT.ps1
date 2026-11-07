# Para TODO processo python que roda AI-BRASIL-CHAT e confirma porta livre
$procs = Get-CimInstance Win32_Process -Filter "Name like 'python%'"
foreach ($p in $procs) {
  if ($p.CommandLine -match 'AI-BRASIL-CHAT') {
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Output ("MATOU " + $p.ProcessId)
  }
}
Start-Sleep -Seconds 2
if (Get-NetTCPConnection -LocalPort 8580 -State Listen -ErrorAction SilentlyContinue) {
  Write-Output "PORTA: OCUPADA"
} else {
  Write-Output "PORTA: LIVRE"
}
