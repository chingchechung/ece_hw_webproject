# Run on a Windows GitHub-hosted runner using Windows PowerShell 5.1.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $repoRoot 'test-results/3d-p1-windows'
New-Item -ItemType Directory -Force -Path $output | Out-Null
$launcher = Join-Path (Split-Path $PSScriptRoot -Parent) 'launch.ps1'
$process = Start-Process powershell.exe -ArgumentList @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $launcher, '-NoBrowser') -PassThru -RedirectStandardOutput (Join-Path $output 'server.log') -RedirectStandardError (Join-Path $output 'server-errors.log')
try {
    $response = $null
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        try { $response = Invoke-WebRequest 'http://127.0.0.1:8787/' -UseBasicParsing -TimeoutSec 2; break } catch { Start-Sleep -Milliseconds 250 }
    }
    if ($null -eq $response -or $response.StatusCode -ne 200) { throw 'Loopback launcher did not become ready' }
    if (!$response.Content.Contains('Engineering Maze Lab')) { throw 'Incorrect static entry point' }
    $scriptPath = [regex]::Match($response.Content, 'src="\./(app-[^"]+\.js)"').Groups[1].Value
    if (!$scriptPath) { throw 'Missing relative local bundle' }
    $head = Invoke-WebRequest "http://127.0.0.1:8787/$scriptPath" -Method Head -UseBasicParsing
    if (!$head.Headers['Content-Type'].StartsWith('text/javascript')) { throw 'Incorrect JavaScript MIME type' }
    if ([int]$head.Headers['Content-Length'] -lt 100000) { throw 'Missing bundled renderer' }
    foreach ($path in @('AGENTS.md', 'teacher_data/S01.draft.json', 'student/index.html')) {
        try { Invoke-WebRequest "http://127.0.0.1:8787/$path" -UseBasicParsing | Out-Null; throw "Unexpected public file: $path" }
        catch { if ($_.Exception.Response.StatusCode.value__ -ne 404) { throw } }
    }
    # Raw encoded traversal must be rejected before filesystem access.
    $client = [Net.Sockets.TcpClient]::new('127.0.0.1', 8787)
    $stream = $client.GetStream()
    $bytes = [Text.Encoding]::ASCII.GetBytes("GET /%2e%2e/AGENTS.md HTTP/1.1`r`nHost: 127.0.0.1`r`n`r`n")
    $stream.Write($bytes, 0, $bytes.Length)
    $reader = [IO.StreamReader]::new($stream)
    $status = $reader.ReadLine(); $client.Close()
    if ($status -ne 'HTTP/1.1 403 Forbidden') { throw "Traversal was not rejected: $status" }
    @{ passed=$true; powershell=$PSVersionTable.PSVersion.ToString(); platform='GitHub-hosted Windows; launcher HTTP checks only, no Intel GPU benchmark'; checks=7 } | ConvertTo-Json | Set-Content (Join-Path $output 'results.json')
} finally { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
