param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("pull", "commit", "deploy")]
    $Action,
    
    [Parameter(Mandatory=$false)]
    $Message = "update: sync work"
)

# 1. Pull Latest Changes
if ($Action -eq "pull") {
    Write-Host ">>> Fetching and Pulling from GitHub..." -ForegroundColor Cyan
    git fetch origin
    git pull origin uat
    Write-Host ">>> Local uat is now up to date." -ForegroundColor Green
}

# 2. Commit and Push to UAT
if ($Action -eq "commit") {
    Write-Host ">>> Committing changes to UAT..." -ForegroundColor Cyan
    git add .
    git commit -m "$Message"
    git push origin uat
    Write-Host ">>> Changes pushed to GitHub (uat branch)." -ForegroundColor Green
}

# 3. Deploy (Merge UAT to PRD)
if ($Action -eq "deploy") {
    Write-Host ">>> STARTING DEPLOYMENT: Merging uat into prd..." -ForegroundColor Yellow
    
    # Switch to prd
    git checkout prd
    
    # Pull latest prd (to avoid conflicts)
    git pull origin prd
    
    # Merge uat
    git merge uat -m "Deploy: $Message"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "!!! MERGE CONFLICT DETECTED. Please resolve manually." -ForegroundColor Red
        return
    }
    
    # Push prd to trigger Render
    git push origin prd
    
    # Switch back to uat for continued development
    git checkout uat
    
    Write-Host ">>> DEPLOYMENT COMPLETE! Render should begin building shortly." -ForegroundColor Green
}
