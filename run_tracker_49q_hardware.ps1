[CmdletBinding()]
param(
    [string]$RunLabel = "dryrun",
    [string]$InstanceId = "operator_loschmidt_echo_49x648",
    [string]$Backend = "ibm_fez",
    [int]$Shots = 4000,
    [int]$OptimizationLevel = 1,
    [int]$SeedTranspiler = 424242,
    [string]$Bitstring = "",
    [string]$InitialLayout = "",
    [switch]$SubmitOnly,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Convert-WindowsPathToWsl {
    param([Parameter(Mandatory = $true)][string]$Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if ($fullPath -notmatch "^[A-Za-z]:\\") {
        throw "Unsupported Windows path for WSL conversion: $fullPath"
    }

    $drive = $fullPath.Substring(0, 1).ToLowerInvariant()
    $rest = $fullPath.Substring(2).Replace("\", "/")
    return "/mnt/$drive$rest"
}

$ProjectRootWin = Split-Path -Parent $PSCommandPath
$ProjectRootWsl = Convert-WindowsPathToWsl -Path $ProjectRootWin
$OutputRel = "data/results/hardware/${InstanceId}_${RunLabel}.json"
$OutputWin = Join-Path $ProjectRootWin ($OutputRel.Replace("/", "\"))
$StdoutLogWin = Join-Path $ProjectRootWin ("data\results\hardware\stdout_{0}_{1}.log" -f $InstanceId, $RunLabel)
$TimingWin = Join-Path $ProjectRootWin ("data\results\hardware\time_{0}_{1}.txt" -f $InstanceId, $RunLabel)

$BitstringArg = ""
if ($Bitstring) {
    $BitstringArg = "--bitstring $Bitstring"
}

$InitialLayoutArg = ""
if ($InitialLayout) {
    $InitialLayoutArg = "--initial-layout $InitialLayout"
}

$SubmitOnlyArg = ""
if ($SubmitOnly) {
    $SubmitOnlyArg = "--submit-only"
}

$InnerCmd = @(
    "cd '$ProjectRootWsl' &&"
    "export PYTHONPATH=src &&"
    "scripts/run-in-qiskit-venv.sh python -m tracker_ole_repro.cli.run_tracker_hardware"
    "--instance-id $InstanceId"
    "--backend $Backend"
    "--shots $Shots"
    "--optimization-level $OptimizationLevel"
    "--seed-transpiler $SeedTranspiler"
    "$BitstringArg"
    "$InitialLayoutArg"
    "$SubmitOnlyArg"
    "--output-json $OutputRel"
) -join " "

Write-Host "Tracker 49Q hardware runner"
Write-Host "Instance: $InstanceId"
Write-Host "Backend: $Backend"
Write-Host "Project: $ProjectRootWin"

if ($DryRun) {
    [pscustomobject]@{
        instance_id = $InstanceId
        backend = $Backend
        command = $InnerCmd
        output_json = $OutputWin
        stdout_log = $StdoutLogWin
        timing_file = $TimingWin
    } | Format-List
    exit 0
}

New-Item -ItemType Directory -Force (Split-Path -Parent $OutputWin) | Out-Null
$startedUtc = (Get-Date).ToUniversalTime().ToString("o")
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
& wsl -e bash -lc "$InnerCmd" *> $StdoutLogWin
$exitCode = $LASTEXITCODE
$stopwatch.Stop()
$completedUtc = (Get-Date).ToUniversalTime().ToString("o")

@(
    "started_utc=$startedUtc"
    "completed_utc=$completedUtc"
    "elapsed_seconds=$([math]::Round($stopwatch.Elapsed.TotalSeconds, 2))"
    "backend=$Backend"
    "instance_id=$InstanceId"
    "output_json=$OutputRel"
) | Set-Content $TimingWin

if ($exitCode -ne 0) {
    throw "Tracker hardware run failed with exit code $exitCode. See $StdoutLogWin"
}

Write-Host ""
Write-Host "Tracker hardware run finished."
Write-Host "Output JSON: $OutputWin"
Write-Host "Stdout log: $StdoutLogWin"
Write-Host "Timing file: $TimingWin"
