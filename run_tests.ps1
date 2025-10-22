# MedCare HMS Test Runner for Windows PowerShell
# Run all test suites with formatted output

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "║              MedCare HMS - Automated Test Suite              ║" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Change to medcare_hms directory
Set-Location -Path "medcare_hms"

# Test suites to run
$testSuites = @(
    @{
        Command = "python manage.py test chat.tests.ChatModelTest --verbosity=2"
        Description = "Chat Module - Model Tests"
    },
    @{
        Command = "python manage.py test chat.tests.ChatViewsTest --verbosity=2"
        Description = "Chat Module - View Tests"
    },
    @{
        Command = "python manage.py test notifications.tests --verbosity=2"
        Description = "Notifications Module - All Tests"
    },
    @{
        Command = "python manage.py test billing.tests --verbosity=2"
        Description = "Billing Module - All Tests"
    },
    @{
        Command = "python manage.py test accounts.tests --verbosity=2"
        Description = "Accounts Module - All Tests"
    },
    @{
        Command = "python manage.py test patients.tests --verbosity=2"
        Description = "Patients Module - All Tests"
    }
)

$results = @()

# Run each test suite
foreach ($suite in $testSuites) {
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Yellow
    Write-Host "  $($suite.Description)" -ForegroundColor Yellow
    Write-Host "=" * 70 -ForegroundColor Yellow
    Write-Host ""
    
    # Run the test
    $output = & cmd /c $suite.Command 2>&1
    $exitCode = $LASTEXITCODE
    
    # Store result
    $passed = ($exitCode -eq 0)
    $results += @{
        Name = $suite.Description
        Passed = $passed
    }
    
    # Print result
    if ($passed) {
        Write-Host ""
        Write-Host "✅ $($suite.Description) - PASSED" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ $($suite.Description) - FAILED" -ForegroundColor Red
    }
}

# Summary
Write-Host ""
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "                        TEST SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

$passedCount = ($results | Where-Object { $_.Passed }).Count
$totalCount = $results.Count

foreach ($result in $results) {
    if ($result.Passed) {
        Write-Host "  ✅ PASSED      - $($result.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAILED      - $($result.Name)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  Total: $passedCount/$totalCount test suites passed" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

if ($passedCount -eq $totalCount) {
    Write-Host "  🎉 All tests passed! Great job!" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Some tests failed. Please review the output above." -ForegroundColor Yellow
}

Write-Host ""

# Return to original directory
Set-Location -Path ".."
