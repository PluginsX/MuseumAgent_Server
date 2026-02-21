import terser from '@rollup/plugin-terser';
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';

const banner = `/**
 * MuseumAgent Client SDK v2.0
 * (c) 2024 MuseumAgent Team
 * @license MIT
 */`;

export default [
    // UMD 构建（浏览器直接引入）
    {
        input: 'src/index.js',
        output: {
            file: 'dist/museum-agent-sdk.js',
            format: 'umd',
            name: 'MuseumAgentSDK',
            banner,
            sourcemap: true,
            exports: 'named'
        },
        plugins: [
            resolve(),
            commonjs()
        ]
    },
    
    // UMD 压缩版
    {
        input: 'src/index.js',
        output: {
            file: 'dist/museum-agent-sdk.min.js',
            format: 'umd',
            name: 'MuseumAgentSDK',
            banner,
            sourcemap: true,
            exports: 'named'
        },
        plugins: [
            resolve(),
            commonjs(),
            terser({
                compress: {
                    drop_console: false, // 保留 console（用户可能需要调试）
                    pure_funcs: ['debug'] // 移除 debug 日志
                },
                format: {
                    comments: /^!/
                }
            })
        ]
    },
    
    // ESM 构建（现代打包工具）
    {
        input: 'src/index.js',
        output: {
            file: 'dist/museum-agent-sdk.esm.js',
            format: 'esm',
            banner,
            sourcemap: true
        },
        plugins: [
            resolve(),
            commonjs()
        ]
    },
    
    // ESM 压缩版
    {
        input: 'src/index.js',
        output: {
            file: 'dist/museum-agent-sdk.esm.min.js',
            format: 'esm',
            banner,
            sourcemap: true
        },
        plugins: [
            resolve(),
            commonjs(),
            terser({
                compress: {
                    drop_console: false,
                    pure_funcs: ['debug']
                },
                format: {
                    comments: /^!/
                }
            })
        ]
    }
];

