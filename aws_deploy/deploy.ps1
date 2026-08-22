[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Ec2Host = $(if ($env:NAUAI_EC2_HOST) { $env:NAUAI_EC2_HOST } else { "3.19.168.215" }),
    [string]$Ec2User = $(if ($env:NAUAI_EC2_USER) { $env:NAUAI_EC2_USER } else { "ubuntu" }),
    [string]$SshKeyPath = $(if ($env:NAUAI_SSH_KEY_PATH) { $env:NAUAI_SSH_KEY_PATH } else { "C:\Users\Usuario\.ssh\nau_ai.pem" }),
    [string]$RemoteProjectPath = $(if ($env:NAUAI_REMOTE_PROJECT_PATH) { $env:NAUAI_REMOTE_PROJECT_PATH } else { "/home/ubuntu/AI_Engineer_course" }),
    [string]$ServiceName = $(if ($env:NAUAI_SERVICE_NAME) { $env:NAUAI_SERVICE_NAME } else { "nauai" }),
    [string]$CommitMessage,
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter()] [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($Arguments -join ' ')"
    }
}

function Require-Value {
    param([string]$Value, [string]$Name)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "$Name is required. Pass it as a parameter or set the matching NAUAI_* environment variable."
    }
}

Require-Value $Ec2Host "Ec2Host / NAUAI_EC2_HOST"
Require-Value $SshKeyPath "SshKeyPath / NAUAI_SSH_KEY_PATH"

if (-not (Test-Path -LiteralPath $SshKeyPath -PathType Leaf)) {
    throw "SSH key not found: $SshKeyPath"
}

if ((git rev-parse --is-inside-work-tree 2>$null) -ne "true") {
    throw "Run this script from inside the NauAI Git repository."
}

$branch = (git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($branch)) {
    throw "Deployment requires a checked-out branch; Git is currently in detached HEAD state."
}

$initialStagedChanges = git diff --cached --name-only
if ($initialStagedChanges) {
    throw "There are already staged changes. Commit or unstage them before running the deployment script so it only commits the document database update."
}

# Keep the two runtime layouts in sync: EC2 runs app.py from ingestion/, while
# Docker Compose/Kubernetes retrieval uses retrieval/data/.
$databaseFiles = @(
    "ingestion/embedded_chunked_data.csv",
    "ingestion/website_images.csv",
    "retrieval/data/embedded_chunked_data.csv",
    "retrieval/data/website_images.csv"
)

$missingFiles = $databaseFiles | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) }
if ($missingFiles) {
    throw "Expected document database files are missing:`n$($missingFiles -join "`n")"
}

if ($PSCmdlet.ShouldProcess("document database CSV files", "Stage and commit")) {
    Invoke-NativeCommand git (@("add", "--") + $databaseFiles)

    & git diff --cached --quiet
    $hasDatabaseChanges = $LASTEXITCODE -ne 0

    if ($hasDatabaseChanges) {
        if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
            $CommitMessage = "Feature: Add updated retrieval data from $(Get-Date -Format 'yyyy-MM-dd')"
        }

        Invoke-NativeCommand git @("commit", "-m", $CommitMessage)
    }
    else {
        Write-Host "No document database changes to commit. Deploying the current $branch revision."
    }
}

if ($PSCmdlet.ShouldProcess("origin/$branch", "Push local branch")) {
    Invoke-NativeCommand git @("push", "origin", $branch)
}

$remoteCommands = @(
    "set -euo pipefail",
    "cd '$RemoteProjectPath'",
    "git fetch origin '$branch'",
    "git checkout '$branch'",
    "git pull --ff-only origin '$branch'"
)

if (-not $SkipDependencyInstall) {
    $remoteCommands += "./nau_ai/bin/pip install -r requirements.txt"
}

$remoteCommands += @(
    "sudo -n systemctl restart '$ServiceName'",
    "sudo -n systemctl is-active --quiet '$ServiceName'",
    "for attempt in {1..30}; do curl -fsS --max-time 5 http://127.0.0.1:1235/health && exit 0; sleep 2; done",
    "echo 'NauAI health check did not succeed within 60 seconds.' >&2",
    "exit 1"
)

$sshArguments = @("-i", $SshKeyPath, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new", "$Ec2User@$Ec2Host", ($remoteCommands -join "; "))

if ($PSCmdlet.ShouldProcess("$Ec2User@$Ec2Host", "Pull $branch and restart $ServiceName")) {
    Invoke-NativeCommand ssh $sshArguments
}

Write-Host "Deployment completed successfully."
