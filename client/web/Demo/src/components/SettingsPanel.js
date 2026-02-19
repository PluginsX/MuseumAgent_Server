/**
 * 设置面板组件
 * 基于 MuseumAgentSDK 客户端库开发
 * 保持原有界面和功能不变
 */

import { createElement } from '../utils/dom.js';

export class SettingsPanel {
    constructor(client) {
        this.client = client;
        this.element = null;
        this.isOpen = false;
        
        // 桌面智能宠物预设函数定义
        const defaultFunctionCalling = [
            {
                name: "move_to_position",
                description: "移动宠物到屏幕指定位置",
                parameters: {
                    type: "object",
                    properties: {
                        x: {
                            type: "number",
                            description: "X坐标（像素）"
                        },
                        y: {
                            type: "number",
                            description: "Y坐标（像素）"
                        },
                        duration: {
                            type: "number",
                            description: "移动持续时间（毫秒）"
                        }
                    },
                    required: ["x", "y"]
                }
            },
            {
                name: "play_animation",
                description: "播放宠物动画",
                parameters: {
                    type: "object",
                    properties: {
                        animation: {
                            type: "string",
                            enum: ["idle", "walk", "run", "jump", "sit", "sleep", "happy", "sad", "angry"],
                            description: "动画类型"
                        },
                        loop: {
                            type: "boolean",
                            description: "是否循环播放"
                        }
                    },
                    required: ["animation"]
                }
            },
            {
                name: "show_emotion",
                description: "显示宠物情绪表情",
                parameters: {
                    type: "object",
                    properties: {
                        emotion: {
                            type: "string",
                            enum: ["happy", "sad", "angry", "surprised", "confused", "love"],
                            description: "情绪类型"
                        },
                        duration: {
                            type: "number",
                            description: "持续时间（毫秒）"
                        }
                    },
                    required: ["emotion"]
                }
            },
            {
                name: "speak_text",
                description: "让宠物说话（显示气泡文字）",
                parameters: {
                    type: "object",
                    properties: {
                        text: {
                            type: "string",
                            description: "要说的文字内容"
                        },
                        duration: {
                            type: "number",
                            description: "显示持续时间（毫秒）"
                        }
                    },
                    required: ["text"]
                }
            },
            {
                name: "change_size",
                description: "改变宠物大小",
                parameters: {
                    type: "object",
                    properties: {
                        scale: {
                            type: "number",
                            description: "缩放比例（0.5-2.0）"
                        }
                    },
                    required: ["scale"]
                }
            }
        ];

        // 本地配置状态（与客户端库同步）
        this.config = {
            platform: client.config.platform || 'WEB',
            requireTTS: client.config.requireTTS !== false,
            enableSRS: client.config.enableSRS !== false,
            autoPlay: client.config.autoPlay !== false,
            vadEnabled: client.vadEnabled !== false,
            functionCalling: client.config.functionCalling.length > 0 ? client.config.functionCalling : defaultFunctionCalling,
            vadParams: client.config.vadParams || {
                silenceThreshold: 0.005,
                silenceDuration: 500,
                speechThreshold: 0.015,
                minSpeechDuration: 150,
                preSpeechPadding: 100,
                postSpeechPadding: 200
            }
        };
    }

    /**
     * 渲染设置面板
     */
    render() {
        this.element = createElement('div', {
            className: 'settings-panel'
        });

        // 面板头部
        const header = createElement('div', {
            className: 'settings-header'
        });

        const title = createElement('h3', {
            textContent: '客户端配置'
        });

        const closeButton = createElement('button', {
            className: 'settings-close',
            textContent: '×'
        });

        closeButton.addEventListener('click', () => {
            this.close();
        });

        header.appendChild(title);
        header.appendChild(closeButton);

        // 面板内容
        const content = createElement('div', {
            className: 'settings-content'
        });

        // 1. 客户端基本信息
        const basicSection = this.renderBasicSettings();
        content.appendChild(basicSection);

        // 2. VAD配置
        const vadSection = this.renderVADSettings();
        content.appendChild(vadSection);

        this.element.appendChild(header);
        this.element.appendChild(content);

        return this.element;
    }

    /**
     * 渲染基本设置
     */
    renderBasicSettings() {
        const section = createElement('div', {
            className: 'settings-section'
        });

        const sectionTitle = createElement('h4', {
            textContent: '客户端基本信息'
        });
        section.appendChild(sectionTitle);

        // Platform
        const platformGroup = this.createSelectGroup(
            'Platform',
            'platform',
            this.config.platform,
            [
                { value: 'WEB', label: 'Web浏览器' },
                { value: 'APP', label: '移动应用' },
                { value: 'MINI_PROGRAM', label: '小程序' },
                { value: 'TV', label: '电视端' }
            ]
        );
        section.appendChild(platformGroup);

        // RequireTTS
        const requireTTSGroup = this.createCheckboxGroup(
            'RequireTTS',
            'requireTTS',
            this.config.requireTTS,
            '是否要求服务器用语音回复'
        );
        section.appendChild(requireTTSGroup);

        // EnableSRS
        const enableSRSGroup = this.createCheckboxGroup(
            'EnableSRS',
            'enableSRS',
            this.config.enableSRS,
            '是否启用增强检索（SRS语义检索系统）'
        );
        section.appendChild(enableSRSGroup);

        // AutoPlay
        const autoPlayGroup = this.createCheckboxGroup(
            'AutoPlay',
            'autoPlay',
            this.config.autoPlay,
            '收到语音消息是否自动播放'
        );
        section.appendChild(autoPlayGroup);

        // FunctionCalling
        const functionCallingGroup = this.createTextareaGroup(
            'FunctionCalling',
            'functionCalling',
            JSON.stringify(this.config.functionCalling, null, 2),
            '函数定义（JSON格式）'
        );
        section.appendChild(functionCallingGroup);

        return section;
    }

    /**
     * 渲染VAD设置
     */
    renderVADSettings() {
        const section = createElement('div', {
            className: 'settings-section'
        });

        const sectionTitle = createElement('h4', {
            textContent: '客户端语音采集VAD配置'
        });
        section.appendChild(sectionTitle);

        // EnableVAD
        const enableVADGroup = this.createCheckboxGroup(
            'EnableVAD',
            'vadEnabled',
            this.config.vadEnabled,
            '是否启用语音活动检测'
        );
        section.appendChild(enableVADGroup);

        // VAD详细参数
        const vadParamsGroup = createElement('div', {
            className: 'vad-params-group'
        });

        // Silence Threshold
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Silence Threshold',
            'vadParams.silenceThreshold',
            this.config.vadParams.silenceThreshold,
            '静音阈值（0-1）',
            0,
            1,
            0.01
        ));

        // Silence Duration
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Silence Duration (ms)',
            'vadParams.silenceDuration',
            this.config.vadParams.silenceDuration,
            '静音持续时长（毫秒）',
            100,
            5000,
            100
        ));

        // Speech Threshold
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Speech Threshold',
            'vadParams.speechThreshold',
            this.config.vadParams.speechThreshold,
            '语音阈值（0-1）',
            0,
            1,
            0.01
        ));

        // Min Speech Duration
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Min Speech Duration (ms)',
            'vadParams.minSpeechDuration',
            this.config.vadParams.minSpeechDuration,
            '最小语音持续时长（毫秒）',
            100,
            3000,
            100
        ));

        // Pre-Speech Padding
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Pre-Speech Padding (ms)',
            'vadParams.preSpeechPadding',
            this.config.vadParams.preSpeechPadding,
            '语音前填充（毫秒）',
            0,
            1000,
            50
        ));

        // Post-Speech Padding
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Post-Speech Padding (ms)',
            'vadParams.postSpeechPadding',
            this.config.vadParams.postSpeechPadding,
            '语音后填充（毫秒）',
            0,
            2000,
            50
        ));

        section.appendChild(vadParamsGroup);

        return section;
    }

    /**
     * 创建下拉选择组
     */
    createSelectGroup(label, key, value, options) {
        const group = createElement('div', {
            className: 'form-group'
        });

        const labelElement = createElement('label', {
            textContent: label
        });

        const select = createElement('select', {
            className: 'form-control'
        });

        options.forEach(opt => {
            const option = createElement('option', {
                value: opt.value,
                textContent: opt.label
            });
            if (opt.value === value) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        select.addEventListener('change', (e) => {
            this.updateConfig(key, e.target.value);
        });

        group.appendChild(labelElement);
        group.appendChild(select);

        return group;
    }

    /**
     * 创建复选框组
     */
    createCheckboxGroup(label, key, checked, description) {
        const group = createElement('div', {
            className: 'form-group checkbox-group'
        });

        const checkboxWrapper = createElement('label', {
            className: 'checkbox-label'
        });

        const checkbox = createElement('input', {
            type: 'checkbox'
        });
        checkbox.checked = checked;

        checkbox.addEventListener('change', (e) => {
            this.updateConfig(key, e.target.checked);
        });

        const labelText = createElement('span', {
            textContent: label
        });

        checkboxWrapper.appendChild(checkbox);
        checkboxWrapper.appendChild(labelText);

        if (description) {
            const desc = createElement('div', {
                className: 'form-description',
                textContent: description
            });
            group.appendChild(checkboxWrapper);
            group.appendChild(desc);
        } else {
            group.appendChild(checkboxWrapper);
        }

        return group;
    }

    /**
     * 创建文本域组
     */
    createTextareaGroup(label, key, value, description) {
        const group = createElement('div', {
            className: 'form-group'
        });

        const labelElement = createElement('label', {
            textContent: label
        });

        const textarea = createElement('textarea', {
            className: 'form-control',
            rows: '8'
        });
        textarea.value = value;

        textarea.addEventListener('blur', (e) => {
            try {
                const parsed = JSON.parse(e.target.value);
                this.updateConfig(key, parsed);
                textarea.classList.remove('error');
            } catch (error) {
                textarea.classList.add('error');
                console.error('[SettingsPanel] JSON解析失败:', error);
            }
        });

        if (description) {
            const desc = createElement('div', {
                className: 'form-description',
                textContent: description
            });
            group.appendChild(labelElement);
            group.appendChild(desc);
        } else {
            group.appendChild(labelElement);
        }

        group.appendChild(textarea);

        return group;
    }

    /**
     * 创建数字输入组
     */
    createNumberGroup(label, key, value, description, min, max, step) {
        const group = createElement('div', {
            className: 'form-group number-group'
        });

        const labelElement = createElement('label', {
            textContent: label
        });

        const input = createElement('input', {
            type: 'number',
            className: 'form-control',
            min: min.toString(),
            max: max.toString(),
            step: step.toString()
        });
        input.value = value;

        input.addEventListener('change', (e) => {
            const numValue = parseFloat(e.target.value);
            this.updateConfig(key, numValue);
        });

        if (description) {
            const desc = createElement('div', {
                className: 'form-description',
                textContent: description
            });
            group.appendChild(labelElement);
            group.appendChild(desc);
        } else {
            group.appendChild(labelElement);
        }

        group.appendChild(input);

        return group;
    }

    /**
     * 更新配置（即时应用到客户端库）
     */
    updateConfig(key, value) {
        console.log('[SettingsPanel] 更新配置:', key, value);

        // 处理嵌套键（如 vadParams.silenceThreshold）
        if (key.includes('.')) {
            const [parent, child] = key.split('.');
            this.config[parent][child] = value;
            
            // 更新客户端库配置
            if (parent === 'vadParams') {
                this.client.config.vadParams[child] = value;
            }
        } else {
            this.config[key] = value;
            
            // 更新客户端库配置
            if (key === 'requireTTS') {
                this.client.config.requireTTS = value;
            } else if (key === 'enableSRS') {
                this.client.config.enableSRS = value;
            } else if (key === 'autoPlay') {
                this.client.config.autoPlay = value;
            } else if (key === 'vadEnabled') {
                this.client.vadEnabled = value;
            } else if (key === 'functionCalling') {
                this.client.config.functionCalling = value;
            } else if (key === 'platform') {
                this.client.config.platform = value;
            }
        }

        console.log('[SettingsPanel] 配置已更新并应用到客户端库');
    }

    /**
     * 打开面板
     */
    open() {
        if (!this.element) {
            this.render();
        }

        this.isOpen = true;
        this.element.classList.add('open');
        document.body.appendChild(this.element);
    }

    /**
     * 关闭面板
     */
    close() {
        if (this.element && this.element.parentNode) {
            this.element.classList.remove('open');
            setTimeout(() => {
                if (this.element && this.element.parentNode) {
                    this.element.parentNode.removeChild(this.element);
                }
            }, 300);
        }
        this.isOpen = false;
    }

    /**
     * 切换面板
     */
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
}
