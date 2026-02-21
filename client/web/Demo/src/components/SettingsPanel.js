/**
 * 设置面板组件
 * 基于 MuseumAgentSDK 客户端库开发
 * 保持原有界面和功能不变
 */

import { createElement } from '../utils/dom.js';

export class SettingsPanel {
    constructor(container, client) {
        // 支持两种调用方式：
        // 1. new SettingsPanel(container, client) - 在 FloatingPanel 中使用
        // 2. new SettingsPanel(client) - 独立使用（向后兼容）
        if (client === undefined) {
            // 独立使用模式
            this.client = container;
            this.container = null;
            this.isStandalone = true;
        } else {
            // FloatingPanel 模式
            this.container = container;
            this.client = client;
            this.isStandalone = false;
        }
        
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
            },
            // 智能体角色配置
            roleDescription: client.config.roleDescription || '你叫韩立，辽宁省博物馆智能讲解员，男性。性格热情、阳光、开朗、健谈、耐心。你精通辽博的历史文物、展览背景、文化知识，擅长用通俗的语言讲解复杂的知识。只回答与辽宁省博物馆、文物、历史文化、参观导览相关的内容，保持专业又友好的讲解员形象。',
            responseRequirements: client.config.responseRequirements || '基于当前所处的场景以及场景的内容，综合相关材料，回答用户的提问。同时你要分析用户的需求！在合适的时机选择合适函数，传入合适的参数返回函数调用响应，调用函数也必须要有语言回答内容！',
            // 场景描述
            sceneDescription: client.config.sceneDescription || '当前所处的是“卷体夔纹蟠龙盖罍展示场景”，主要内容为该青铜器表面包含的各种纹样的图形和寓意展示，以及各部分组成结构的造型寓意。'
        };
        
        // 折叠状态
        this.collapsedSections = {
            basic: true,
            role: true,
            scene: true,
            functions: true,
            vad: true
        };
        
        // ✅ 配置更新开关状态（手动标记哪些配置需要更新）
        this.updateSwitches = {
            basic: false,      // 基本配置（requireTTS, enableSRS）
            role: false,       // 角色配置（roleDescription, responseRequirements）
            scene: false,      // 场景配置（sceneDescription）
            functions: false   // 函数定义（functionCalling）
            // VAD 配置不需要发送到服务器，所以不需要开关
        };
        
        // 如果是在 FloatingPanel 中使用，立即渲染
        if (!this.isStandalone && this.container) {
            this.render();
        }
    }

    /**
     * 渲染设置面板
     */
    render() {
        // 如果是在 FloatingPanel 中使用，直接渲染到容器
        if (!this.isStandalone && this.container) {
            this.renderContent(this.container);
            return this.container;
        }
        
        // 独立模式：创建完整的面板
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

        this.renderContent(content);

        this.element.appendChild(header);
        this.element.appendChild(content);

        return this.element;
    }

    /**
     * 渲染内容部分（可复用）
     */
    renderContent(container) {

        // 1. 客户端基本信息
        const basicSection = this.renderCollapsibleSection(
            'basic',
            '客户端基本信息',
            () => this.renderBasicSettings()
        );
        container.appendChild(basicSection);

        // 2. 智能体角色配置
        const roleSection = this.renderCollapsibleSection(
            'role',
            '智能体角色配置',
            () => this.renderRoleSettings()
        );
        container.appendChild(roleSection);

        // 3. 上下文配置
        const sceneSection = this.renderCollapsibleSection(
            'scene',
            '上下文配置',
            () => this.renderSceneSettings()
        );
        container.appendChild(sceneSection);

        // 4. 函数定义
        const functionsSection = this.renderCollapsibleSection(
            'functions',
            '函数定义',
            () => this.renderFunctionsSettings()
        );
        container.appendChild(functionsSection);

        // 5. VAD配置
        const vadSection = this.renderCollapsibleSection(
            'vad',
            'VAD配置',
            () => this.renderVADSettings()
        );
        container.appendChild(vadSection);
    }

    /**
     * 渲染可折叠区域
     */
    renderCollapsibleSection(id, title, contentRenderer) {
        const section = createElement('div', {
            className: 'settings-section collapsible-section'
        });
        
        // ✅ 添加 data-section-id 属性，用于自动开启开关时定位
        section.setAttribute('data-section-id', id);

        // 标题栏（可点击）
        const header = createElement('div', {
            className: 'section-header'
        });

        const toggleIcon = createElement('span', {
            className: 'toggle-icon',
            textContent: this.collapsedSections[id] ? '▶' : '▼'
        });

        const titleElement = createElement('h4', {
            textContent: title
        });

        // ✅ 左侧区域（折叠图标 + 标题）- 可点击展开/折叠
        const leftArea = createElement('div', {
            className: 'section-header-left'
        });
        leftArea.appendChild(toggleIcon);
        leftArea.appendChild(titleElement);

        // ✅ 右侧区域（更新开关）- 仅对需要发送到服务器的配置显示
        const rightArea = createElement('div', {
            className: 'section-header-right'
        });

        // 只有 basic, role, scene, functions 需要更新开关（VAD 是客户端本地配置）
        if (this.updateSwitches.hasOwnProperty(id)) {
            const switchLabel = createElement('label', {
                className: 'update-switch-label'
            });

            const switchInput = createElement('input', {
                type: 'checkbox',
                className: 'update-switch'
            });
            switchInput.checked = this.updateSwitches[id];

            // 阻止事件冒泡，避免触发折叠/展开
            switchLabel.addEventListener('click', (e) => {
                e.stopPropagation();
            });

            switchInput.addEventListener('change', (e) => {
                this.updateSwitches[id] = e.target.checked;
                console.log(`[SettingsPanel] 配置更新开关 [${id}]:`, e.target.checked);
            });

            const switchSlider = createElement('span', {
                className: 'update-switch-slider'
            });

            const switchText = createElement('span', {
                className: 'update-switch-text',
                textContent: '更新'
            });

            switchLabel.appendChild(switchInput);
            switchLabel.appendChild(switchSlider);
            switchLabel.appendChild(switchText);

            rightArea.appendChild(switchLabel);
        }

        header.appendChild(leftArea);
        header.appendChild(rightArea);

        // 内容区域
        const contentWrapper = createElement('div', {
            className: 'section-content'
        });
        
        if (!this.collapsedSections[id]) {
            contentWrapper.style.display = 'block';
            const content = contentRenderer();
            contentWrapper.appendChild(content);
        } else {
            contentWrapper.style.display = 'none';
        }

        // 点击左侧区域切换折叠状态
        leftArea.addEventListener('click', () => {
            this.collapsedSections[id] = !this.collapsedSections[id];
            
            if (this.collapsedSections[id]) {
                // 折叠
                toggleIcon.textContent = '▶';
                contentWrapper.style.display = 'none';
            } else {
                // 展开
                toggleIcon.textContent = '▼';
                contentWrapper.style.display = 'block';
                // 如果内容为空，则渲染
                if (contentWrapper.children.length === 0) {
                    const content = contentRenderer();
                    contentWrapper.appendChild(content);
                }
            }
        });

        section.appendChild(header);
        section.appendChild(contentWrapper);

        return section;
    }

    /**
     * 渲染基本设置
     */
    renderBasicSettings() {
        const container = createElement('div', {
            className: 'settings-fields'
        });

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
        container.appendChild(platformGroup);

        // RequireTTS
        const requireTTSGroup = this.createCheckboxGroup(
            'RequireTTS',
            'requireTTS',
            this.config.requireTTS,
            '是否要求服务器用语音回复'
        );
        container.appendChild(requireTTSGroup);

        // EnableSRS
        const enableSRSGroup = this.createCheckboxGroup(
            'EnableSRS',
            'enableSRS',
            this.config.enableSRS,
            '是否启用增强检索（SRS语义检索系统）'
        );
        container.appendChild(enableSRSGroup);

        // AutoPlay
        const autoPlayGroup = this.createCheckboxGroup(
            'AutoPlay',
            'autoPlay',
            this.config.autoPlay,
            '收到语音消息是否自动播放'
        );
        container.appendChild(autoPlayGroup);

        return container;
    }

    /**
     * 渲染智能体角色配置
     */
    renderRoleSettings() {
        const container = createElement('div', {
            className: 'settings-fields'
        });

        // 角色描述
        const roleDescGroup = this.createTextareaGroup(
            '角色描述',
            'roleDescription',
            this.config.roleDescription,
            '告诉 LLM 它的角色定位和身份'
        );
        container.appendChild(roleDescGroup);

        // 响应要求
        const responseReqGroup = this.createTextareaGroup(
            '响应要求',
            'responseRequirements',
            this.config.responseRequirements,
            '告诉 LLM 如何回答问题，有何侧重'
        );
        container.appendChild(responseReqGroup);

        return container;
    }

    /**
     * 渲染场景配置
     */
    renderSceneSettings() {
        const container = createElement('div', {
            className: 'settings-fields'
        });

        // 场景描述
        const sceneDescGroup = this.createTextareaGroup(
            '场景描述',
            'sceneDescription',
            this.config.sceneDescription,
            '描述当前所处的场景（例如：纹样展示场景、铸造工艺展示场景）'
        );
        container.appendChild(sceneDescGroup);

        return container;
    }

    /**
     * 渲染函数定义配置
     */
    renderFunctionsSettings() {
        const container = createElement('div', {
            className: 'settings-fields'
        });

        // FunctionCalling
        const functionCallingGroup = this.createTextareaGroup(
            'FunctionCalling',
            'functionCalling',
            JSON.stringify(this.config.functionCalling, null, 2),
            '当前场景可执行的函数定义（JSON格式）'
        );
        container.appendChild(functionCallingGroup);

        return container;
    }

    /**
     * 渲染VAD设置
     */
    renderVADSettings() {
        const container = createElement('div', {
            className: 'settings-fields'
        });

        // EnableVAD
        const enableVADGroup = this.createCheckboxGroup(
            'EnableVAD',
            'vadEnabled',
            this.config.vadEnabled,
            '是否启用语音活动检测'
        );
        container.appendChild(enableVADGroup);

        // Silence Threshold
        container.appendChild(this.createNumberGroup(
            'Silence Threshold',
            'vadParams.silenceThreshold',
            this.config.vadParams.silenceThreshold,
            '静音阈值（0-1）',
            0,
            1,
            0.01
        ));

        // Silence Duration
        container.appendChild(this.createNumberGroup(
            'Silence Duration (ms)',
            'vadParams.silenceDuration',
            this.config.vadParams.silenceDuration,
            '静音持续时长（毫秒）',
            100,
            5000,
            100
        ));

        // Speech Threshold
        container.appendChild(this.createNumberGroup(
            'Speech Threshold',
            'vadParams.speechThreshold',
            this.config.vadParams.speechThreshold,
            '语音阈值（0-1）',
            0,
            1,
            0.01
        ));

        // Min Speech Duration
        container.appendChild(this.createNumberGroup(
            'Min Speech Duration (ms)',
            'vadParams.minSpeechDuration',
            this.config.vadParams.minSpeechDuration,
            '最小语音持续时长（毫秒）',
            100,
            3000,
            100
        ));

        // Pre-Speech Padding
        container.appendChild(this.createNumberGroup(
            'Pre-Speech Padding (ms)',
            'vadParams.preSpeechPadding',
            this.config.vadParams.preSpeechPadding,
            '语音前填充（毫秒）',
            0,
            1000,
            50
        ));

        // Post-Speech Padding
        container.appendChild(this.createNumberGroup(
            'Post-Speech Padding (ms)',
            'vadParams.postSpeechPadding',
            this.config.vadParams.postSpeechPadding,
            '语音后填充（毫秒）',
            0,
            2000,
            50
        ));

        return container;
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
     * 创建输入框组
     */
    createInputGroup(label, key, value, description) {
        const group = createElement('div', {
            className: 'form-group'
        });

        const labelElement = createElement('label', {
            textContent: label
        });

        const input = createElement('input', {
            type: 'text',
            className: 'form-control'
        });
        input.value = value;

        input.addEventListener('blur', (e) => {
            this.updateConfig(key, e.target.value);
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
            // ✅ 只对 functionCalling 字段进行 JSON 解析
            if (key === 'functionCalling') {
                try {
                    const parsed = JSON.parse(e.target.value);
                    this.updateConfig(key, parsed);
                    textarea.classList.remove('error');
                } catch (error) {
                    textarea.classList.add('error');
                    console.error('[SettingsPanel] JSON解析失败:', error);
                }
            } else {
                // 其他字段直接保存文本
                this.updateConfig(key, e.target.value);
                textarea.classList.remove('error');
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
            
            // 处理 vadParams 配置
            if (parent === 'vadParams') {
                this.config.vadParams[child] = value;
                // ✅ 使用 SDK 的配置管理（自动保存）
                this.client.updateConfig('vadParams', { ...this.client.config.vadParams, [child]: value });
            }
        } else {
            this.config[key] = value;
            
            // ✅ 使用 SDK 的配置管理（自动保存）
            this.client.updateConfig(key, value);
            
            // 更新开关状态
            if (key === 'requireTTS' || key === 'enableSRS') {
                this._autoEnableUpdateSwitch('basic');
            } else if (key === 'functionCalling') {
                this._autoEnableUpdateSwitch('functions');
            } else if (key === 'roleDescription' || key === 'responseRequirements') {
                this._autoEnableUpdateSwitch('role');
            } else if (key === 'sceneDescription') {
                this._autoEnableUpdateSwitch('scene');
            }
        }

        console.log('[SettingsPanel] 配置已更新并自动保存');
    }

    /**
     * ✅ 自动开启更新开关（仅开启一次，用户可手动关闭）
     * @private
     */
    _autoEnableUpdateSwitch(switchId) {
        // 如果开关已经是开启状态，不重复开启
        if (this.updateSwitches[switchId]) {
            return;
        }

        // 开启开关
        this.updateSwitches[switchId] = true;
        console.log(`[SettingsPanel] 自动开启更新开关: ${switchId}`);

        // ✅ 更新 UI 中的开关状态（支持独立模式和容器模式）
        const container = this.element || this.container;
        if (container) {
            const section = container.querySelector(`[data-section-id="${switchId}"]`);
            if (section) {
                const switchInput = section.querySelector('.update-switch');
                if (switchInput) {
                    switchInput.checked = true;
                    console.log(`[SettingsPanel] UI 开关已更新: ${switchId}`);
                } else {
                    console.warn(`[SettingsPanel] 找不到开关元素: ${switchId}`);
                }
            } else {
                console.warn(`[SettingsPanel] 找不到区域元素: ${switchId}`);
            }
        } else {
            console.warn(`[SettingsPanel] 容器未初始化`);
        }
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

    /**
     * ✅ 获取需要更新的配置（差异更新）
     * 只返回开关打开的配置项
     */
    getPendingUpdates() {
        const updates = {};

        // 基本配置
        if (this.updateSwitches.basic) {
            updates.require_tts = this.config.requireTTS;
            updates.enable_srs = this.config.enableSRS;
        }

        // 角色配置
        if (this.updateSwitches.role) {
            updates.system_prompt = {
                role_description: this.config.roleDescription || '',
                response_requirements: this.config.responseRequirements || ''
            };
        }

        // 场景配置
        if (this.updateSwitches.scene) {
            updates.scene_context = {
                scene_description: this.config.sceneDescription || ''
            };
        }

        // 函数定义
        if (this.updateSwitches.functions) {
            updates.function_calling = this.config.functionCalling;
        }

        return updates;
    }

    /**
     * ✅ 清除所有更新开关（发送成功后调用）
     */
    clearUpdateSwitches() {
        for (const key in this.updateSwitches) {
            this.updateSwitches[key] = false;
        }
        
        // ✅ 更新 UI 中的开关状态（支持独立模式和容器模式）
        const container = this.element || this.container;
        if (container) {
            const switches = container.querySelectorAll('.update-switch');
            switches.forEach(sw => {
                sw.checked = false;
            });
        }
        
        console.log('[SettingsPanel] 所有更新开关已清除');
    }

    /**
     * 销毁组件
     */
    destroy() {
        console.log('[SettingsPanel] 销毁组件');
        
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        
        this.element = null;
        this.isOpen = false;
        
        console.log('[SettingsPanel] 组件已销毁');
    }
}
