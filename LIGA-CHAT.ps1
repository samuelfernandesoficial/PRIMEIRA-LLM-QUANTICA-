# Liga o AI BRASIL CHAT em background (ajuste os caminhos se precisar)
$py = 'python'   # ou caminho completo do seu python.exe
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process -WindowStyle Hidden -FilePath $py -ArgumentList ('"' + (Join-Path $dir 'AI-BRASIL-CHAT.py') + '"') -WorkingDirectory $dir
Start-Sleep -Seconds 4
try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8580/saude).Content } catch { "AINDA SUBINDO" }
