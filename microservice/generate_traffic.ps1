# Traffic Generator for Checkout Microservice

$HOST_URL = "http://localhost:5000"

# Counters
$Total = 0
$Success = 0
$Failed = 0
$Timeout = 0

Write-Host "Traffic Generator Started - Press CTRL+C to stop" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    try {
        $Scenario = Get-Random -Minimum 1 -Maximum 11

        if ($Scenario -le 6) {
            $Response = Invoke-WebRequest -Uri "$HOST_URL/checkout" -Method GET -TimeoutSec 10 -ErrorAction Stop
            $Content = $Response.Content | ConvertFrom-Json
            $Status = $Content.status

            if ($Status -eq "success") {
                Write-Host "[SUCCESS] Checkout: $($Content.product) for $($Content.user) - $($Content.price)" -ForegroundColor Green
                $Success++
            } elseif ($Status -eq "timeout") {
                Write-Host "[TIMEOUT] Checkout timed out for $($Content.user)" -ForegroundColor Yellow
                $Timeout++
            } elseif ($Status -eq "payment_failed") {
                Write-Host "[PAYMENT FAILED] Payment failed for $($Content.user)" -ForegroundColor Red
                $Failed++
            } elseif ($Status -eq "out_of_stock") {
                Write-Host "[OUT OF STOCK] Product unavailable: $($Content.product)" -ForegroundColor Yellow
                $Failed++
            }

        } elseif ($Scenario -le 8) {
            $Response = Invoke-WebRequest -Uri "$HOST_URL/products" -Method GET -TimeoutSec 5 -ErrorAction Stop
            Write-Host "[PRODUCTS] Product catalog fetched" -ForegroundColor Cyan
            $Success++

        } else {
            $Response = Invoke-WebRequest -Uri "$HOST_URL/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
            Write-Host "[HEALTH] Service is healthy" -ForegroundColor Green
            $Success++
        }

        $Total++

    } catch {
        Write-Host "[ERROR] Request failed: $_" -ForegroundColor Red
        $Failed++
        $Total++
    }

    if ($Total % 20 -eq 0 -and $Total -gt 0) {
        Write-Host ""
        Write-Host "==== Summary ====" -ForegroundColor Cyan
        Write-Host "Total    : $Total"
        Write-Host "Success  : $Success" -ForegroundColor Green
        Write-Host "Failed   : $Failed" -ForegroundColor Red
        Write-Host "Timeouts : $Timeout" -ForegroundColor Yellow
        Write-Host "=================" -ForegroundColor Cyan
        Write-Host ""
    }

    $Delay = Get-Random -Minimum 300 -Maximum 1500
    Start-Sleep -Milliseconds $Delay
}