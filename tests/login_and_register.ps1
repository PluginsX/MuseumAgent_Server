# 登录并获取访问令牌
$uri = "http://localhost:8002/api/auth/login"
$body = @{
    username = "123"
    password = "123"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
}

try {
    $loginResponse = Invoke-RestMethod -Uri $uri -Method Post -Body $body -Headers $headers
    Write-Host "登录成功"
    Write-Host "Access Token: $($loginResponse.access_token)"
    
    # 使用登录获取的令牌注册会话
    $sessionUri = "http://localhost:8002/api/session/register"
    $sessionHeaders = @{
        "Authorization" = "Bearer $($loginResponse.access_token)"
        "Content-Type" = "application/json"
    }
    
    $sessionBody = @{
        username = "test_user"
        password = "test_password"
    } | ConvertTo-Json
    
    $sessionResponse = Invoke-RestMethod -Uri $sessionUri -Method Post -Body $sessionBody -Headers $sessionHeaders
    Write-Host "会话注册成功:"
    $sessionResponse | ConvertTo-Json
} catch {
    Write-Host "操作失败: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.ReadToEnd()
    }
}