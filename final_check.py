import os
import re

# 检查功能性代码中的旧指令集相关代码
critical_patterns = [
    'StandardCommandSet',
    'command_set_models',
    'validate_command_set',
    'get_operations_for_session\s*\(',
    '\.operation_set(?!\s*=)',
]

found_critical = []

for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in critical_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        found_critical.append({
                            'file': file_path,
                            'pattern': pattern,
                            'matches': matches
                        })
            except Exception as e:
                print(f'Error reading {file_path}: {e}')

if found_critical:
    print('发现关键的旧指令集相关代码:')
    for issue in found_critical:
        print(f'文件: {issue["file"]}')
        print(f'模式: {issue["pattern"]}')
        print(f'匹配: {issue["matches"]}')
        print('-' * 50)
else:
    print('✅ 未发现关键的旧指令集相关代码')