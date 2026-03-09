#!/bin/bash
# Unity WebGL 优化部署检查脚本
# 用于验证 Nginx 配置和 Unity 文件是否正确

echo "=========================================="
echo "Unity WebGL 优化部署检查"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
PASS=0
FAIL=0
WARN=0

# 1. 检查 Nginx 配置语法
echo "1. 检查 Nginx 配置语法..."
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓ Nginx 配置语法正确${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ Nginx 配置语法错误${NC}"
    nginx -t
    ((FAIL++))
fi
echo ""

# 2. 检查 Unity Build 文件是否存在
echo "2. 检查 Unity Build 文件..."
BUILD_DIR="/www/wwwroot/MuseumAgent_Client/unity/Build"

if [ ! -d "$BUILD_DIR" ]; then
    echo -e "${RED}✗ Unity Build 目录不存在: $BUILD_DIR${NC}"
    ((FAIL++))
else
    echo -e "${GREEN}✓ Unity Build 目录存在${NC}"
    ((PASS++))
    
    # 检查关键文件
    FILES=("build.loader.js" "build.framework.js.unityweb" "build.wasm.unityweb" "build.data.unityweb")
    
    for file in "${FILES[@]}"; do
        if [ -f "$BUILD_DIR/$file" ]; then
            SIZE=$(du -h "$BUILD_DIR/$file" | cut -f1)
            echo -e "  ${GREEN}✓${NC} $file (大小: $SIZE)"
            ((PASS++))
        else
            echo -e "  ${RED}✗${NC} $file 不存在"
            ((FAIL++))
        fi
    done
fi
echo ""

# 3. 检查文件权限
echo "3. 检查文件权限..."
if [ -d "$BUILD_DIR" ]; then
    OWNER=$(stat -c '%U:%G' "$BUILD_DIR")
    if [ "$OWNER" = "www:www" ]; then
        echo -e "${GREEN}✓ 文件所有者正确: $OWNER${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠ 文件所有者不是 www:www，当前为: $OWNER${NC}"
        echo "  建议执行: chown -R www:www $BUILD_DIR"
        ((WARN++))
    fi
fi
echo ""

# 4. 检查 Unity 文件压缩格式
echo "4. 检查 Unity 文件压缩格式..."
WASM_FILE="$BUILD_DIR/build.wasm.unityweb"

if [ -f "$WASM_FILE" ]; then
    # 读取文件头部字节
    HEADER=$(xxd -l 2 -p "$WASM_FILE")
    
    if [ "$HEADER" = "1f8b" ]; then
        echo -e "${GREEN}✓ 检测到 Gzip 压缩格式${NC}"
        echo "  Nginx 配置应使用: add_header Content-Encoding gzip;"
        ((PASS++))
    elif [ "$HEADER" = "ceb2" ]; then
        echo -e "${YELLOW}⚠ 检测到 Brotli 压缩格式${NC}"
        echo "  Nginx 配置应使用: add_header Content-Encoding br;"
        echo "  但你的配置使用的是 Gzip，请检查 Unity 构建设置！"
        ((WARN++))
    else
        echo -e "${RED}✗ 未检测到压缩格式（文件头: $HEADER）${NC}"
        echo "  请检查 Unity 构建设置中的压缩选项"
        ((FAIL++))
    fi
fi
echo ""

# 5. 测试 Unity 文件 HTTP 响应
echo "5. 测试 Unity 文件 HTTP 响应..."
DOMAIN="https://www.soulflaw.com"

# 测试 build.wasm.unityweb
echo "  测试 build.wasm.unityweb..."
RESPONSE=$(curl -s -I "$DOMAIN/unity/Build/build.wasm.unityweb")

if echo "$RESPONSE" | grep -q "200 OK"; then
    echo -e "    ${GREEN}✓${NC} HTTP 状态码: 200 OK"
    ((PASS++))
else
    echo -e "    ${RED}✗${NC} HTTP 状态码异常"
    echo "$RESPONSE" | head -1
    ((FAIL++))
fi

if echo "$RESPONSE" | grep -qi "Content-Encoding: gzip"; then
    echo -e "    ${GREEN}✓${NC} Content-Encoding: gzip"
    ((PASS++))
else
    echo -e "    ${RED}✗${NC} 缺少 Content-Encoding: gzip 头"
    ((FAIL++))
fi

if echo "$RESPONSE" | grep -qi "Cache-Control:.*immutable"; then
    echo -e "    ${GREEN}✓${NC} Cache-Control 包含 immutable"
    ((PASS++))
else
    echo -e "    ${YELLOW}⚠${NC} Cache-Control 未包含 immutable"
    ((WARN++))
fi

if echo "$RESPONSE" | grep -qi "Access-Control-Allow-Origin"; then
    echo -e "    ${GREEN}✓${NC} CORS 头存在"
    ((PASS++))
else
    echo -e "    ${RED}✗${NC} 缺少 CORS 头"
    ((FAIL++))
fi
echo ""

# 6. 检查 WebSocket 配置
echo "6. 检查 WebSocket 配置..."
if grep -q "proxy_read_timeout 600s" /www/server/panel/vhost/nginx/html_www.soulflaw.com.conf; then
    echo -e "${GREEN}✓ WebSocket 读取超时已设置为 600s（10分钟）${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠ WebSocket 读取超时未设置为 600s${NC}"
    ((WARN++))
fi
echo ""

# 7. 检查服务器配置
echo "7. 检查服务器配置..."
CONFIG_FILE="/opt/MuseumAgent_Server/config/config.json"

if [ -f "$CONFIG_FILE" ]; then
    HEARTBEAT_TIMEOUT=$(grep -o '"heartbeat_timeout_minutes":[[:space:]]*[0-9]*' "$CONFIG_FILE" | grep -o '[0-9]*$')
    
    if [ "$HEARTBEAT_TIMEOUT" -ge 10 ]; then
        echo -e "${GREEN}✓ 服务器心跳超时: ${HEARTBEAT_TIMEOUT} 分钟${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠ 服务器心跳超时过短: ${HEARTBEAT_TIMEOUT} 分钟${NC}"
        echo "  建议设置为 10 分钟或更长"
        ((WARN++))
    fi
else
    echo -e "${YELLOW}⚠ 服务器配置文件不存在: $CONFIG_FILE${NC}"
    ((WARN++))
fi
echo ""

# 8. 检查客户端 SDK
echo "8. 检查客户端 SDK..."
SDK_FILE="/www/wwwroot/MuseumAgent_Client/lib/museum-agent-sdk.min.js"

if [ -f "$SDK_FILE" ]; then
    if grep -q "heartbeatTimeout.*600000" "$SDK_FILE"; then
        echo -e "${GREEN}✓ 客户端心跳超时已设置为 600000ms（10分钟）${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠ 客户端心跳超时未更新${NC}"
        echo "  请重新构建 SDK: cd client/sdk && npm run build"
        ((WARN++))
    fi
else
    echo -e "${YELLOW}⚠ SDK 文件不存在: $SDK_FILE${NC}"
    ((WARN++))
fi
echo ""

# 9. 检查 Unity 加载保活心跳
echo "9. 检查 Unity 加载保活心跳..."
UNITY_CONTAINER="/www/wwwroot/MuseumAgent_Client/src/components/UnityContainer.js"

if [ -f "$UNITY_CONTAINER" ]; then
    if grep -q "keepAliveInterval" "$UNITY_CONTAINER"; then
        echo -e "${GREEN}✓ Unity 加载保活心跳已添加${NC}"
        ((PASS++))
    else
        echo -e "${RED}✗ Unity 加载保活心跳未添加${NC}"
        echo "  请更新 UnityContainer.js"
        ((FAIL++))
    fi
else
    echo -e "${YELLOW}⚠ UnityContainer.js 不存在: $UNITY_CONTAINER${NC}"
    ((WARN++))
fi
echo ""

# 总结
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo -e "${GREEN}通过: $PASS${NC}"
echo -e "${YELLOW}警告: $WARN${NC}"
echo -e "${RED}失败: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ] && [ $WARN -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！可以部署。${NC}"
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo -e "${YELLOW}⚠ 存在警告，建议修复后再部署。${NC}"
    exit 0
else
    echo -e "${RED}✗ 存在错误，请修复后再部署。${NC}"
    exit 1
fi

