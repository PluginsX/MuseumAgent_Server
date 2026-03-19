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
                // ✅ v2.0 自适应参数
                calibrationDuration : 1500,
                speechRatio         : 3.5,
                silenceRatio        : 1.8,
                minSpeechThreshold  : 0.010,
                minSilenceThreshold : 0.004,
                silenceDuration     : 800,
                minSpeechDuration   : 200,
                confirmFrames       : 3,
                preSpeechPadding    : 300,
                postSpeechPadding   : 300,
                zcrMin              : 3,
                zcrMax              : 60,
                voiceBandRatioMin   : 0.20,
                noiseUpdateRate     : 0.015,
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
        
        // 使用SDK内置的更新标记机制，不再需要本地维护更新开关
        // this.updateSwitches 已被SDK的 pendingUpdates 替代
        
        // 如果是在 FloatingPanel 中使用，立即渲染
        if (!this.isStandalone && this.container) {
            this.render();
        }
        
        // 订阅客户端配置变化事件
        this.subscribeToClientEvents();
    }
    
    /**
     * 订阅客户端配置变化事件
     */
    subscribeToClientEvents() {
        console.log('[SettingsPanel] 订阅客户端配置变化事件');
        
        try {
            // 尝试订阅可能的配置更新事件
            const eventNames = ['configUpdated', 'contextUpdated', 'updateContext', 'settingsChanged'];
            
            eventNames.forEach(eventName => {
                try {
                    this.client.on(eventName, () => {
                        console.log(`[SettingsPanel] 收到客户端配置更新事件: ${eventName}`);
                        this.refreshConfig();
                    });
                    console.log(`[SettingsPanel] 已订阅事件: ${eventName}`);
                } catch (error) {
                    console.warn(`[SettingsPanel] 无法订阅事件 ${eventName}:`, error);
                }
            });
        } catch (error) {
            console.error('[SettingsPanel] 订阅客户端事件失败:', error);
        }
    }
    
    /**
     * 刷新配置，从客户端读取最新配置并更新界面
     */
    refreshConfig() {
        console.log('[SettingsPanel] 刷新配置');
        
        try {
            // 从客户端读取最新配置
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
                }
            ];
            
            // 更新本地配置
            this.config = {
                platform: this.client.config.platform || 'WEB',
                requireTTS: this.client.config.requireTTS !== false,
                enableSRS: this.client.config.enableSRS !== false,
                autoPlay: this.client.config.autoPlay !== false,
                vadEnabled: this.client.vadEnabled !== false,
                functionCalling: this.client.config.functionCalling.length > 0 ? this.client.config.functionCalling : defaultFunctionCalling,
                vadParams: this.client.config.vadParams || {
                    silenceThreshold: 0.005,
                    silenceDuration: 500,
                    speechThreshold: 0.015,
                    minSpeechDuration: 150,
                    preSpeechPadding: 100,
                    postSpeechPadding: 200
                },
                // 智能体角色配置
                roleDescription: this.client.config.roleDescription || '你叫韩立，辽宁省博物馆智能讲解员，男性。性格热情、阳光、开朗、健谈、耐心。你精通辽博的历史文物、展览背景、文化知识，擅长用通俗的语言讲解复杂的知识。只回答与辽宁省博物馆、文物、历史文化、参观导览相关的内容，保持专业又友好的讲解员形象。',
                responseRequirements: this.client.config.responseRequirements || '基于当前所处的场景以及场景的内容，综合相关材料，回答用户的提问。同时你要分析用户的需求！在合适的时机选择合适函数，传入合适的参数返回函数调用响应，调用函数也必须要有语言回答内容！',
                // 场景描述
                sceneDescription: this.client.config.sceneDescription || '当前所处的是"卷体夔纹蟠龙盖罍展示场景"，主要内容为该青铜器表面包含的各种纹样的图形和寓意展示，以及各部分组成结构的造型寓意。'
            };
            
            console.log('[SettingsPanel] 配置已更新:', this.config);
            
            // 重新渲染界面
            this.reRender();
            
            // 更新状态指示器
            this.updateStatusIndicators();
        } catch (error) {
            console.error('[SettingsPanel] 刷新配置失败:', error);
        }
    }
    
    /**
     * 重新渲染界面
     */
    reRender() {
        console.log('[SettingsPanel] 重新渲染界面');
        
        try {
            // 找到所有内容区域
            const container = this.element || this.container;
            if (container) {
                // 清空现有内容
                const sections = container.querySelectorAll('.settings-section');
                sections.forEach(section => {
                    const contentWrapper = section.querySelector('.section-content');
                    if (contentWrapper) {
                        contentWrapper.innerHTML = '';
                    }
                });
                
                // 重新渲染每个展开的区域
                Object.keys(this.collapsedSections).forEach(sectionId => {
                    if (!this.collapsedSections[sectionId]) {
                        const section = container.querySelector(`[data-section-id="${sectionId}"]`);
                        if (section) {
                            const contentWrapper = section.querySelector('.section-content');
                            if (contentWrapper) {
                                let content;
                                switch (sectionId) {
                                    case 'basic':
                                        content = this.renderBasicSettings();
                                        break;
                                    case 'role':
                                        content = this.renderRoleSettings();
                                        break;
                                    case 'scene':
                                        content = this.renderSceneSettings();
                                        break;
                                    case 'functions':
                                        content = this.renderFunctionsSettings();
                                        break;
                                    case 'vad':
                                        content = this.renderVADSettings();
                                        break;
                                }
                                if (content) {
                                    contentWrapper.appendChild(content);
                                }
                            }
                        }
                    }
                });
                
                console.log('[SettingsPanel] 界面已重新渲染');
            }
        } catch (error) {
            console.error('[SettingsPanel] 重新渲染界面失败:', error);
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
        // 添加更新状态指示器的样式
        const style = document.createElement('style');
        style.textContent = `
            .update-status-indicator {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            
            .update-status-indicator.pending {
                background-color: #ffdddd;
                color: #d8000c;
                border: 1px solid #ffbaba;
            }
            
            .update-status-indicator.submitted {
                background-color: #ddffdd;
                color: #4f8a10;
                border: 1px solid #b6d7a8;
            }
        `;
        document.head.appendChild(style);

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

        // ✅ 右侧区域（更新状态指示器）- 仅对需要发送到服务器的配置显示
        const rightArea = createElement('div', {
            className: 'section-header-right'
        });

        // 只有 basic, role, scene, functions 需要更新状态指示（VAD 是客户端本地配置）
        const updatableSections = ['basic', 'role', 'scene', 'functions'];
        if (updatableSections.includes(id)) {
            // 创建状态指示器
            const statusIndicator = createElement('div', {
                className: 'update-status-indicator'
            });

            // 获取当前更新状态
            const updateMarks = this.client.getUpdateMarks();
            const isPending = updateMarks[id] || false;

            // 设置状态文本
            statusIndicator.textContent = isPending ? '未提交' : '已提交';
            statusIndicator.className = `update-status-indicator ${isPending ? 'pending' : 'submitted'}`;

            rightArea.appendChild(statusIndicator);
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
     * 渲染VAD设置（v2.0 自适应参数）
     * 
     * 分为两个层次：
     *   1. 开关层：EnableVAD + 自动环境噪声适应（autoNoise）
     *   2. 手动参数层：仅在关闭「自动适应」时可编辑
     */
    renderVADSettings() {
        const container = createElement('div', {
            className: 'settings-fields'
        });

        // ── 第一层：主开关 ──────────────────────────────
        // EnableVAD
        container.appendChild(this.createCheckboxGroup(
            'EnableVAD',
            'vadEnabled',
            this.config.vadEnabled,
            '是否启用语音活动检测（VAD）'
        ));

        // 自动环境噪声适应开关
        const autoNoiseEnabled = this.config.vadParams.autoNoiseAdaptation !== false; // 默认开启
        const autoNoiseGroup = this.createCheckboxGroup(
            '自动环境噪声适应',
            'vadParams.autoNoiseAdaptation',
            autoNoiseEnabled,
            '开启后系统自动校准环境噪声并动态调整检测阈值（推荐），关闭后可手动配置各项参数'
        );
        container.appendChild(autoNoiseGroup);

        // ── 第二层：手动参数区（由自动适应开关控制是否禁用）──
        const manualParamsContainer = createElement('div', {
            className: 'vad-manual-params'
        });
        // 初始状态：自动适应开启则禁用手动参数
        manualParamsContainer.style.opacity = autoNoiseEnabled ? '0.4' : '1';
        manualParamsContainer.style.pointerEvents = autoNoiseEnabled ? 'none' : 'auto';
        if (autoNoiseEnabled) {
            const hint = createElement('div', {
                className: 'vad-auto-hint',
                textContent: '自动适应已开启，以下参数由系统自动管理，无需手动调整'
            });
            hint.style.cssText = 'font-size:11px;color:#888;font-style:italic;margin-bottom:8px;padding:6px 8px;background:#f5f5f5;border-radius:4px;border-left:3px solid #ccc;';
            manualParamsContainer.appendChild(hint);
        }

        // 监听自动适应开关变化，动态切换手动参数区的可用状态
        const autoNoiseCheckbox = autoNoiseGroup.querySelector('input[type="checkbox"]');
        if (autoNoiseCheckbox) {
            autoNoiseCheckbox.addEventListener('change', (e) => {
                const isAuto = e.target.checked;
                manualParamsContainer.style.opacity = isAuto ? '0.4' : '1';
                manualParamsContainer.style.pointerEvents = isAuto ? 'none' : 'auto';
                // 更新提示文字
                const existingHint = manualParamsContainer.querySelector('.vad-auto-hint');
                if (isAuto && !existingHint) {
                    const hint = createElement('div', {
                        className: 'vad-auto-hint',
                        textContent: '自动适应已开启，以下参数由系统自动管理，无需手动调整'
                    });
                    hint.style.cssText = 'font-size:11px;color:#888;font-style:italic;margin-bottom:8px;padding:6px 8px;background:#f5f5f5;border-radius:4px;border-left:3px solid #ccc;';
                    manualParamsContainer.insertBefore(hint, manualParamsContainer.firstChild);
                } else if (!isAuto && existingHint) {
                    existingHint.remove();
                }
            });
        }

        // ── 校准 ──────────────────────────────────────
        manualParamsContainer.appendChild(this.createSectionLabel('── 自适应校准 ──'));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '校准时长 Calibration (ms)',
            'vadParams.calibrationDuration',
            this.config.vadParams.calibrationDuration ?? 1500,
            '开启录音后采集环境噪声的时长，建议 1000-2000ms',
            500, 3000, 100
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '噪声追踪速率 Noise Update Rate',
            'vadParams.noiseUpdateRate',
            this.config.vadParams.noiseUpdateRate ?? 0.015,
            '静音帧更新噪声基线的速率，越小越稳定（推荐 0.01-0.03）',
            0.005, 0.1, 0.005
        ));

        // ── 动态阈值比率 ──────────────────────────────
        manualParamsContainer.appendChild(this.createSectionLabel('── 动态阈值（相对噪声基线的倍率）──'));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '语音触发比率 Speech Ratio',
            'vadParams.speechRatio',
            this.config.vadParams.speechRatio ?? 3.5,
            '语音阈值 = 噪声基线 × 此值，越大越难触发（推荐 2.5-5.0）',
            1.5, 10.0, 0.5
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '静音判定比率 Silence Ratio',
            'vadParams.silenceRatio',
            this.config.vadParams.silenceRatio ?? 1.8,
            '静音阈值 = 噪声基线 × 此值，越小越容易判断为静音（推荐 1.2-2.5）',
            1.0, 5.0, 0.1
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '最小语音阈值 Min Speech Thr',
            'vadParams.minSpeechThreshold',
            this.config.vadParams.minSpeechThreshold ?? 0.010,
            '语音阈值的绝对下限（防止极安静环境过度敏感）',
            0.002, 0.1, 0.001
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '最小静音阈值 Min Silence Thr',
            'vadParams.minSilenceThreshold',
            this.config.vadParams.minSilenceThreshold ?? 0.004,
            '静音阈值的绝对下限',
            0.001, 0.05, 0.001
        ));

        // ── 时序参数 ──────────────────────────────────
        manualParamsContainer.appendChild(this.createSectionLabel('── 时序参数 ──'));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '防抖帧数 Confirm Frames',
            'vadParams.confirmFrames',
            this.config.vadParams.confirmFrames ?? 3,
            '连续多少帧超阈值才确认语音开始（防止瞬时噪声误触发）',
            1, 10, 1
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '静音结束时长 Silence Duration (ms)',
            'vadParams.silenceDuration',
            this.config.vadParams.silenceDuration ?? 800,
            '静音持续多久后结束本次语音（ms）',
            200, 3000, 100
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '最短语音时长 Min Speech Duration (ms)',
            'vadParams.minSpeechDuration',
            this.config.vadParams.minSpeechDuration ?? 200,
            '短于此时长的语音将被丢弃（过滤咳嗽/碰撞等短暂噪声）',
            50, 1000, 50
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '语音前填充 Pre-Speech Padding (ms)',
            'vadParams.preSpeechPadding',
            this.config.vadParams.preSpeechPadding ?? 300,
            '语音开始前保留的音频缓冲时长（避免丢失起始音节）',
            0, 1000, 50
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '语音后填充 Post-Speech Padding (ms)',
            'vadParams.postSpeechPadding',
            this.config.vadParams.postSpeechPadding ?? 300,
            '语音结束后保留的音频缓冲时长（避免丢失尾音）',
            0, 1000, 50
        ));

        // ── 人声特征过滤 ──────────────────────────────
        manualParamsContainer.appendChild(this.createSectionLabel('── 人声特征过滤（高级）──'));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '过零率下限 ZCR Min',
            'vadParams.zcrMin',
            this.config.vadParams.zcrMin ?? 3,
            '每帧过零次数下限，低于此值视为冲击噪声/碰撞音',
            0, 20, 1
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '过零率上限 ZCR Max',
            'vadParams.zcrMax',
            this.config.vadParams.zcrMax ?? 60,
            '每帧过零次数上限，高于此值视为高频噪声/风噪',
            20, 120, 5
        ));

        manualParamsContainer.appendChild(this.createNumberGroup(
            '人声频带能量比 Voice Band Ratio Min',
            'vadParams.voiceBandRatioMin',
            this.config.vadParams.voiceBandRatioMin ?? 0.20,
            '300-3400Hz 人声频带能量占总能量的最低比例（0-1）',
            0.05, 0.8, 0.05
        ));

        // 把手动参数区挂入主容器
        container.appendChild(manualParamsContainer);

        return container;
    }

    /**
     * 创建分组标签（纯展示，非输入）
     */
    createSectionLabel(text) {
        const el = createElement('div', {
            className: 'vad-section-label',
            textContent: text
        });
        el.style.cssText = 'margin: 12px 0 4px; font-size: 11px; color: #888; font-weight: 600; letter-spacing: 0.5px;';
        return el;
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
            
            // ✅ 使用 SDK 的配置管理（自动保存 + 自动标记更新）
            this.client.updateConfig(key, value);
        }

        console.log('[SettingsPanel] 配置已更新并自动保存');
        
        // 更新状态指示器
        this.updateStatusIndicators();
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
        // 使用SDK内置的方法获取待更新配置
        return this.client.getPendingUpdates();
    }

    /**
     * ✅ 清除所有更新开关（发送成功后调用）
     */
    clearUpdateSwitches() {
        // 使用SDK内置的方法清除更新标记
        this.client.clearUpdateMarks();
        
        // 更新状态指示器
        this.updateStatusIndicators();
        
        console.log('[SettingsPanel] 所有更新开关已清除');
    }
    
    /**
     * 更新所有状态指示器
     */
    updateStatusIndicators() {
        const container = this.element || this.container;
        if (!container) return;
        
        // 获取所有状态指示器
        const indicators = container.querySelectorAll('.update-status-indicator');
        const updateMarks = this.client.getUpdateMarks();
        
        indicators.forEach(indicator => {
            // 获取对应的部分ID
            const section = indicator.closest('.settings-section');
            if (section) {
                const sectionId = section.getAttribute('data-section-id');
                if (sectionId) {
                    // 获取当前更新状态
                    const isPending = updateMarks[sectionId] || false;
                    
                    // 更新状态文本和样式
                    indicator.textContent = isPending ? '未提交' : '已提交';
                    indicator.className = `update-status-indicator ${isPending ? 'pending' : 'submitted'}`;
                }
            }
        });
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
