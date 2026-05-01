param(
    [Parameter(Mandatory = $true)]
    [string]$CommandLine,

    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory
)

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "C:\Windows\System32\cmd.exe"
$psi.WorkingDirectory = $WorkingDirectory
$psi.UseShellExecute = $true
$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$psi.Arguments = "/c $CommandLine"

$process = [System.Diagnostics.Process]::Start($psi)
if ($null -eq $process) {
    throw "Failed to start process"
}

Write-Output ("Started PID: {0}" -f $process.Id)
