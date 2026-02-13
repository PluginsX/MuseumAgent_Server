# 创建会话注册脚本
$uri = "http://localhost:8002/api/session/register"
$body = @{
    username = "test_user"
    password = "test_password"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
}

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -Headers $headers
    Write-Host "会话注册成功:"
    $response | ConvertTo-Json
} catch {
    Write-Host "会话注册失败: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.ReadToEnd()
    }
}