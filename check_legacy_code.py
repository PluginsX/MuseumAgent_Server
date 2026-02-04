import os
import re

patterns_to_check = [
    'StandardCommandSet',
    'command_set_models', 
    'validate_command_set',
    'get_operations_for_session',
    'operation_set(?!\\s*=\\s*\\[)'
]

found_issues = []

for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in patterns_to_check:
                    matches = re.findall(pattern, content)
                    if matches:
                        found_issues.append({
                            'file': file_path,
                            'pattern': pattern,
                            'matches': matches[:3]
                        })
            except Exception as e:
                print(f'Error reading {file_path}: {e}')

if found_issues:
    print('发现潜在的旧指令集相关代码:')
    for issue in found_issues:
        print(f'文件: {issue["file"]}')
        print(f'模式: {issue["pattern"]}')  
        print(f'匹配: {issue["matches"]}')
        print('-' * 50)
else:
    print('✅ 未发现旧指令集相关代码残留')