Write-Host "Clearing all scan results from MongoDB..." -ForegroundColor Cyan
mongosh pentestlab --eval "db.scan_results.deleteMany({})" --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "All scan results cleared successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to clear scan results!" -ForegroundColor Red
}
