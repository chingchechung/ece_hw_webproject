# Windows PowerShell 5.1 / .NET only; no Node, npm, Python, admin or Internet.
# Serves the shipped dist directory on IPv4 loopback, not the repository root.
param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$showcaseRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'dist'))
if (!(Test-Path (Join-Path $showcaseRoot 'index.html'))) { throw 'Missing dist/index.html. Extract the complete package first.' }
$listener = $null
foreach ($candidate in 8787..8797) {
    try {
        $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $candidate)
        $listener.Start()
        $showcasePort = $candidate
        break
    } catch { $listener = $null }
}
if ($null -eq $listener) { throw 'Loopback ports 8787-8797 are busy. Close another local demo and retry.' }
$url = "http://127.0.0.1:$showcasePort/"
Write-Host "Engineering Maze Lab / v1.0.0`n$url`nClose this window or press Ctrl+C to stop. Only dist/ is served."
if (!$NoBrowser) { Start-Process $url }
$mime = @{ '.html'='text/html; charset=utf-8'; '.js'='text/javascript; charset=utf-8'; '.css'='text/css; charset=utf-8'; '.json'='application/json'; '.txt'='text/plain; charset=utf-8'; '.png'='image/png' }
try {
    while ($true) {
        $client = $listener.AcceptTcpClient()
        try {
            $client.ReceiveTimeout = 3000; $client.SendTimeout = 5000
            $stream = $client.GetStream()
            # Read headers without buffering the request body. This is a GET/HEAD static server.
            $request = [Collections.Generic.List[byte]]::new()
            while ($request.Count -lt 8192) {
                $byte = $stream.ReadByte()
                if ($byte -lt 0) { break }
                $request.Add([byte]$byte)
                if ($request.Count -ge 4 -and [Text.Encoding]::ASCII.GetString($request.ToArray(), $request.Count-4, 4) -eq "`r`n`r`n") { break }
            }
            $line = ([Text.Encoding]::ASCII.GetString($request.ToArray()) -split "`r`n")[0]
            $parts = $line -split ' '
            $status = '400 Bad Request'; $body = [Text.Encoding]::UTF8.GetBytes('Bad request'); $contentType = 'text/plain'
            if ($parts.Count -eq 3 -and $parts[0] -in @('GET', 'HEAD') -and $parts[1].StartsWith('/')) {
                $relative = [Uri]::UnescapeDataString(($parts[1] -split '\?')[0]).Replace('/', [IO.Path]::DirectorySeparatorChar).TrimStart([char[]]@('\','/'))
                if (!$relative) { $relative = 'index.html' }
                $file = [IO.Path]::GetFullPath((Join-Path $showcaseRoot $relative))
                if (!$file.StartsWith($showcaseRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or $relative.Contains(':')) {
                    $status = '403 Forbidden'; $body = [Text.Encoding]::UTF8.GetBytes('Forbidden')
                } elseif (Test-Path -LiteralPath $file -PathType Leaf) {
                    $status = '200 OK'; $body = [IO.File]::ReadAllBytes($file)
                    $extension = [IO.Path]::GetExtension($file)
                    $contentType = if ($mime.ContainsKey($extension)) { $mime[$extension] } else { 'application/octet-stream' }
                } else { $status = '404 Not Found'; $body = [Text.Encoding]::UTF8.GetBytes('Not found') }
            }
            $header = [Text.Encoding]::ASCII.GetBytes("HTTP/1.1 $status`r`nContent-Type: $contentType`r`nContent-Length: $($body.Length)`r`nConnection: close`r`nCache-Control: no-cache`r`nX-Content-Type-Options: nosniff`r`n`r`n")
            $stream.Write($header, 0, $header.Length)
            if ($parts[0] -ne 'HEAD') { $stream.Write($body, 0, $body.Length) }
            $stream.Flush()
        } catch { Write-Verbose $_ } finally { $client.Close() }
    }
} finally { $listener.Stop() }
