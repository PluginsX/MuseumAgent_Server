/**
 * 设置面板组件
 * 客户端配置管理
 */

import { stateManager } from '../core/StateManager.js';
import { createElement } from '../utils/dom.js';

export class SettingsPanel {
    constructor() {
        this.element = null;
        this.isOpen = false;
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

        const sessionConfig = stateManager.getState('session');

        // Platform
        const platformGroup = this.createSelectGroup(
            'Platform',
            'platform',
            sessionConfig.platform || 'WEB',
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
            sessionConfig.requireTTS !== false,
            '是否要求服务器用语音回复'
        );
        section.appendChild(requireTTSGroup);

        // AutoPlay
        const autoPlayGroup = this.createCheckboxGroup(
            'AutoPlay',
            'autoPlay',
            sessionConfig.autoPlay !== false,
            '收到语音消息是否自动播放'
        );
        section.appendChild(autoPlayGroup);

        // FunctionCalling
        const functionCallingGroup = this.createTextareaGroup(
            'FunctionCalling',
            'functionCalling',
            JSON.stringify(sessionConfig.functionCalling || [], null, 2),
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

        const recordingConfig = stateManager.getState('recording');

        // EnableVAD
        const enableVADGroup = this.createCheckboxGroup(
            'EnableVAD',
            'vadEnabled',
            recordingConfig.vadEnabled !== false,
            '是否启用语音活动检测'
        );
        section.appendChild(enableVADGroup);

        // VAD详细参数
        const vadParams = recordingConfig.vadParams || {
            silenceThreshold: 0.01,
            silenceDuration: 1500,
            speechThreshold: 0.05,
            minSpeechDuration: 300,
            preSpeechPadding: 300,
            postSpeechPadding: 500
        };

        const vadParamsGroup = createElement('div', {
            className: 'vad-params-group'
        });

        // Silence Threshold
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Silence Threshold',
            'vadParams.silenceThreshold',
            vadParams.silenceThreshold,
            '静音阈值（0-1）',
            0,
            1,
            0.01
        ));

        // Silence Duration
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Silence Duration (ms)',
            'vadParams.silenceDuration',
            vadParams.silenceDuration,
            '静音持续时长（毫秒）',
            100,
            5000,
            100
        ));

        // Speech Threshold
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Speech Threshold',
            'vadParams.speechThreshold',
            vadParams.speechThreshold,
            '语音阈值（0-1）',
            0,
            1,
            0.01
        ));

        // Min Speech Duration
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Min Speech Duration (ms)',
            'vadParams.minSpeechDuration',
            vadParams.minSpeechDuration,
            '最小语音持续时长（毫秒）',
            100,
            3000,
            100
        ));

        // Pre-Speech Padding
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Pre-Speech Padding (ms)',
            'vadParams.preSpeechPadding',
            vadParams.preSpeechPadding,
            '语音前填充（毫秒）',
            0,
            1000,
            50
        ));

        // Post-Speech Padding
        vadParamsGroup.appendChild(this.createNumberGroup(
            'Post-Speech Padding (ms)',
            'vadParams.postSpeechPadding',
            vadParams.postSpeechPadding,
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
     * 更新配置（即时应用）
     */
    updateConfig(key, value) {
        console.log('[SettingsPanel] 更新配置:', key, value);

        // 处理嵌套键（如 vadParams.silenceThreshold）
        if (key.includes('.')) {
            const [parent, child] = key.split('.');
            const currentParent = stateManager.getState(`recording.${parent}`) || {};
            stateManager.setState(`recording.${parent}`, {
                ...currentParent,
                [child]: value
            });
        } else if (key.startsWith('vad')) {
            // VAD相关配置存储在 recording 下
            stateManager.setState(`recording.${key}`, value);
        } else {
            // 其他配置存储在 session 下
            stateManager.setState(`session.${key}`, value);
            
            // 如果修改了 FunctionCalling，标记为已修改
            if (key === 'functionCalling') {
                stateManager.setState('session.functionCallingModified', true);
                console.log('[SettingsPanel] FunctionCalling已修改，将在下次请求时更新到服务器');
            }
        }

        console.log('[SettingsPanel] 配置已更新并应用');
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

