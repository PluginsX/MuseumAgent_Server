#!/usr/bin/env python3
"""
Unity WebGL 构建检查工具
检查 Unity 构建文件的压缩状态和大小
"""
import os
import sys

def check_unity_build():
    """检查 Unity 构建文件"""
    build_dir = "unity/Build"
    
    if not os.path.exists(build_dir):
        print(f"❌ 构建目录不存在: {build_dir}")
        return False
    
    print("=" * 60)
    print("Unity WebGL 构建检查")
    print("=" * 60)
    
    # 检查关键文件
    files_to_check = [
        "build.loader.js",
        "build.framework.js.unityweb",
        "build.wasm.unityweb",
        "build.data.unityweb"
    ]
    
    total_size = 0
    all_exist = True
    
    for filename in files_to_check:
        filepath = os.path.join(build_dir, filename)
        
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            size_mb = size / (1024 * 1024)
            total_size += size
            
            # 判断是否压缩
            is_compressed = filename.endswith('.unityweb')
            status = "✅ 已压缩" if is_compressed else "⚠️  未压缩"
            
            print(f"\n{status} {filename}")
            print(f"   大小: {size_mb:.2f} MB ({size:,} bytes)")
            
            # 警告：如果 .unityweb 文件过大，可能未正确压缩
            if is_compressed and size_mb > 10:
                print(f"   ⚠️  警告: 文件过大，可能未正确压缩！")
                print(f"   建议: 检查 Unity 构建设置中的压缩选项")
        else:
            print(f"\n❌ 缺失 {filename}")
            all_exist = False
    
    print("\n" + "=" * 60)
    print(f"总大小: {total_size / (1024 * 1024):.2f} MB")
    print("=" * 60)
    
    # 给出建议
    print("\n📋 优化建议:")
    
    if total_size > 20 * 1024 * 1024:  # 超过 20MB
        print("⚠️  构建文件过大，建议优化：")
        print("   1. 在 Unity 中启用 Brotli 压缩（Publishing Settings）")
        print("   2. 减少纹理质量和资源大小")
        print("   3. 使用 Addressables 延迟加载资源")
    else:
        print("✅ 构建文件大小合理")
    
    if not all_exist:
        print("\n❌ 部分文件缺失，请重新构建 Unity 项目")
        return False
    
    print("\n✅ 所有必需文件都存在")
    
    # 检查压缩格式
    print("\n🔍 压缩格式检测:")
    wasm_file = os.path.join(build_dir, "build.wasm.unityweb")
    
    if os.path.exists(wasm_file):
        with open(wasm_file, 'rb') as f:
            header = f.read(4)
            
            # Brotli 魔数
            if header[:2] == b'\xce\xb2':
                print("   压缩格式: Brotli (推荐)")
                print("   Nginx 配置: add_header Content-Encoding br;")
            # Gzip 魔数
            elif header[:2] == b'\x1f\x8b':
                print("   压缩格式: Gzip")
                print("   Nginx 配置: add_header Content-Encoding gzip;")
            else:
                print("   ⚠️  未检测到压缩格式")
                print("   建议: 在 Unity 构建设置中启用压缩")
    
    return True

if __name__ == "__main__":
    success = check_unity_build()
    sys.exit(0 if success else 1)

