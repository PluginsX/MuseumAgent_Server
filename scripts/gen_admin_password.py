# -*- coding: utf-8 -*-
"""
生成管理员密码的 bcrypt 哈希
用于 config/config.ini 中的 admin_password_hash
"""
import sys

try:
    import bcrypt
except ImportError:
    print("请安装: pip install bcrypt")
    sys.exit(1)

password = input("请输入新密码: ").strip()
if not password:
    print("密码不能为空")
    sys.exit(1)
h = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
print("将以下哈希填入 config/config.ini 的 admin_password_hash:")
print(h.decode())
