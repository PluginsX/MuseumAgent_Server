# 本地 MySQL 访问教程

## 连接信息
- 主机地址: localhost 或 127.0.0.1
- 端口: 3306
- 用户名: root
- 密码: jiaofeifan.945

---

## 方法一：通过命令行访问

### 1. 打开命令提示符或 PowerShell

### 2. 连接到 MySQL
```bash
mysql -u root -p
```
输入密码: `jiaofeifan.945`

### 3. 常用命令
```sql
-- 查看所有数据库
SHOW DATABASES;

-- 使用指定数据库
USE database_name;

-- 查看当前数据库的所有表
SHOW TABLES;

-- 查看表结构
DESCRIBE table_name;

-- 退出 MySQL
EXIT;
```

---

## 方法二：通过 MySQL Workbench 访问

### 1. 打开 MySQL Workbench

### 2. 创建新连接
- 点击左侧的 "+" 图标添加新连接
- 连接名称: Local MySQL
- 主机名: localhost
- 端口: 3306
- 用户名: root
- 密码: jiaofeifan.945

### 3. 点击 "Test Connection" 测试连接

### 4. 点击 "OK" 保存并连接

### 5. 在查询窗口执行 SQL 语句

---

## 方法三：通过 MySQL Shell 访问

### 1. 打开 MySQL Shell

### 2. 切换到 SQL 模式
```
\sql
```

### 3. 连接到数据库
```
\connect root@localhost:3306
```
输入密码: `jiaofeifan.945`

### 4. 执行 SQL 查询
```sql
SHOW DATABASES;
```

### 5. 退出
```
\quit
```

---

## 常用 SQL 操作示例

### 创建数据库
```sql
CREATE DATABASE my_database;
```

### 创建表
```sql
USE my_database;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 插入数据
```sql
INSERT INTO users (username, email) VALUES ('user1', 'user1@example.com');
```

### 查询数据
```sql
SELECT * FROM users;
SELECT username, email FROM users WHERE id = 1;
```

### 更新数据
```sql
UPDATE users SET email = 'newemail@example.com' WHERE id = 1;
```

### 删除数据
```sql
DELETE FROM users WHERE id = 1;
```

### 删除表
```sql
DROP TABLE users;
```

### 删除数据库
```sql
DROP DATABASE my_database;
```

---

## 常见问题

### 1. 连接被拒绝
- 检查 MySQL 服务是否正在运行
- 在 Windows 服务中查找 "MySQL80" 服务

### 2. 密码错误
- 确认密码为: jiaofeifan.945
- 注意大小写和特殊字符

### 3. 端口占用
- 确认端口 3306 未被其他程序占用
- 使用 `netstat -ano | findstr :3306` 检查端口状态

---

## 推荐工具
- **MySQL Workbench**: 图形化管理界面，适合初学者
- **MySQL Shell**: 高级命令行工具，支持多种语言模式
- **命令行 mysql**: 传统命令行工具，轻量级

---

## 安全提示
- 不要在生产环境中使用 root 账户
- 定期备份数据库
- 为不同应用创建独立的数据库用户
- 使用强密码并定期更换