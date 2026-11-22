# Daily SPY snapshot fetch + commit (VolSurf extension).
# Idempotent: skips if today's snapshot already exists.

$ErrorActionPreference = "Stop"
Set-Location "D:\Kuliah\Hackathon\Options pricing and volatility surface"

$date = Get-Date -Format "yyyy-MM-dd"
$csv = "data\snapshots\spy_$date.csv"

if (Test-Path $csv) {
    Write-Output "snapshot for $date already exists, skipping"
    exit 0
}

# market hours check (US/Eastern approximated by local clock here; see README)
$py = ".venv\Scripts\python.exe"
& $py -m volsurf.fetch
if ($LASTEXITCODE -ne 0) { Write-Error "fetch failed"; exit 1 }

# commit + push if a new snapshot appeared
if (Test-Path $csv) {
    git add "data/snapshots/spy_$date.csv" "data/snapshots/spy_$date.metadata.json" "data/snapshots/spy_$date.sha256" config/market.yaml
    if (git diff --cached --quiet) {
        Write-Output "nothing new to commit"
    } else {
        git commit -m "data: daily SPY snapshot $date"
        git push origin main
    }
}
