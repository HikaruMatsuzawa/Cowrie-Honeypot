param(
    [string]$Service = "cowrie",
    [string]$TargetHost = "1.1.1.1",
    [int]$TargetPort = 80,
    [int]$TimeoutSeconds = 3,
    [string]$PythonPath = "/cowrie/cowrie-env/bin/python3"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking outbound connectivity from service '$Service' to $TargetHost`:$TargetPort"

docker compose ps *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: cannot access Docker Compose or Docker API. Run this script from the project root with Docker access."
    exit 2
}

$script = @"
import socket
import sys

target_host = "$TargetHost"
target_port = $TargetPort
timeout = $TimeoutSeconds

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(timeout)
try:
    sock.connect((target_host, target_port))
except OSError:
    sys.exit(0)
else:
    sys.exit(1)
finally:
    sock.close()
"@

$script | docker compose exec -T $Service $PythonPath -

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: outbound connection was blocked."
    exit 0
}

Write-Error "NG: outbound connection succeeded. Review Docker network or firewall settings."
exit 1
