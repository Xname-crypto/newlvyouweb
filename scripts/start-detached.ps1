param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,

    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,

    [Parameter(Mandatory = $true)]
    [string]$StdOutPath,

    [Parameter(Mandatory = $true)]
    [string]$StdErrPath,

    [string[]]$ArgumentList = @()
)

$stdoutDir = Split-Path -Parent $StdOutPath
$stderrDir = Split-Path -Parent $StdErrPath

if ($stdoutDir) {
    New-Item -ItemType Directory -Force -Path $stdoutDir | Out-Null
}

if ($stderrDir) {
    New-Item -ItemType Directory -Force -Path $stderrDir | Out-Null
}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $FilePath
$psi.WorkingDirectory = $WorkingDirectory
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true

foreach ($argument in $ArgumentList) {
    [void]$psi.ArgumentList.Add($argument)
}

$envMap = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
Get-ChildItem Env: | ForEach-Object {
    $envMap[$_.Name] = [string]$_.Value
}

$psi.Environment.Clear()
foreach ($entry in $envMap.GetEnumerator()) {
    $psi.Environment[$entry.Key] = $entry.Value
}

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $psi
[void]$process.Start()

$stdoutWriter = [System.IO.StreamWriter]::new($StdOutPath, $false, [System.Text.Encoding]::UTF8)
$stderrWriter = [System.IO.StreamWriter]::new($StdErrPath, $false, [System.Text.Encoding]::UTF8)

$process.BeginOutputReadLine()
$process.BeginErrorReadLine()

$outputHandler = [System.Diagnostics.DataReceivedEventHandler]{
    param($sender, $e)
    if ($null -ne $e.Data) {
        $stdoutWriter.WriteLine($e.Data)
        $stdoutWriter.Flush()
    }
}

$errorHandler = [System.Diagnostics.DataReceivedEventHandler]{
    param($sender, $e)
    if ($null -ne $e.Data) {
        $stderrWriter.WriteLine($e.Data)
        $stderrWriter.Flush()
    }
}

$process.add_OutputDataReceived($outputHandler)
$process.add_ErrorDataReceived($errorHandler)

Start-Sleep -Milliseconds 800

Write-Output ("Started PID: {0}" -f $process.Id)
