# Script para probar rate limiting en PowerShell
# Ejecutar: .\test_rate_limiting.ps1

Write-Host "Probando Rate Limiting - Haciendo 6 requests rápidos al endpoint /users" -ForegroundColor Yellow
Write-Host "Límite: 10 requests/minuto (pero probamos con /users porque es más simple)" -ForegroundColor Yellow
Write-Host ""

for ($i=1; $i -le 12; $i++) {
    Write-Host "Request $i" -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/users" `
            -Method GET `
            -UseBasicParsing `
            -ErrorAction Stop
        
        Write-Host "  ✅ Status: $($response.StatusCode)" -ForegroundColor Green
        
        # Verificar headers de rate limit
        $headers = $response.Headers
        if ($headers.'X-RateLimit-Limit') {
            Write-Host "    X-RateLimit-Limit: $($headers.'X-RateLimit-Limit')" -ForegroundColor Gray
        }
        if ($headers.'X-RateLimit-Remaining') {
            Write-Host "    X-RateLimit-Remaining: $($headers.'X-RateLimit-Remaining')" -ForegroundColor Gray
        }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 429) {
            Write-Host "  ❌ Rate Limit Excedido (429 Too Many Requests)" -ForegroundColor Red
            Write-Host "  ✅ Rate limiting funciona correctamente!" -ForegroundColor Green
        }
        else {
            Write-Host "  Error: Status $statusCode" -ForegroundColor Red
        }
    }
    
    Start-Sleep -Milliseconds 50
}

Write-Host ""
Write-Host "Prueba completada" -ForegroundColor Yellow
Write-Host ""
Write-Host "Si viste un 429, el rate limiting está funcionando ✅" -ForegroundColor Green

