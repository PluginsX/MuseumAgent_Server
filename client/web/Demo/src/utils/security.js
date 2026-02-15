/**
 * 安全工具
 * 提供加密、XSS 防护等功能
 */

/**
 * 使用 Web Crypto API 加密数据
 */
export async function encryptData(data) {
    try {
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(data);
        
        // 生成密钥（实际应用中应该使用用户特定的密钥）
        const key = await getEncryptionKey();
        
        // 生成随机 IV
        const iv = crypto.getRandomValues(new Uint8Array(12));
        
        // 加密
        const encryptedBuffer = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            key,
            dataBuffer
        );
        
        // 组合 IV 和加密数据
        const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength);
        combined.set(iv, 0);
        combined.set(new Uint8Array(encryptedBuffer), iv.length);
        
        // 转换为 Base64
        return btoa(String.fromCharCode(...combined));
        
    } catch (error) {
        console.error('[Security] 加密失败:', error);
        // 降级：使用 Base64（不安全，仅用于开发）
        return btoa(data);
    }
}

/**
 * 解密数据
 */
export async function decryptData(encryptedData) {
    try {
        // 从 Base64 解码
        const combined = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
        
        // 提取 IV 和加密数据
        const iv = combined.slice(0, 12);
        const encrypted = combined.slice(12);
        
        // 获取密钥
        const key = await getEncryptionKey();
        
        // 解密
        const decryptedBuffer = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv },
            key,
            encrypted
        );
        
        // 转换为字符串
        const decoder = new TextDecoder();
        return decoder.decode(decryptedBuffer);
        
    } catch (error) {
        console.error('[Security] 解密失败:', error);
        // 降级：使用 Base64
        try {
            return atob(encryptedData);
        } catch (e) {
            throw new Error('解密失败');
        }
    }
}

/**
 * 获取加密密钥（从浏览器指纹生成）
 */
async function getEncryptionKey() {
    // 使用浏览器指纹作为密钥材料
    const fingerprint = await getBrowserFingerprint();
    
    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        encoder.encode(fingerprint),
        { name: 'PBKDF2' },
        false,
        ['deriveBits', 'deriveKey']
    );
    
    return crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: encoder.encode('museumAgent'),
            iterations: 100000,
            hash: 'SHA-256'
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
    );
}

/**
 * 获取浏览器指纹
 */
async function getBrowserFingerprint() {
    const components = [
        navigator.userAgent,
        navigator.language,
        screen.width,
        screen.height,
        new Date().getTimezoneOffset()
    ];
    
    return components.join('|');
}

/**
 * XSS 防护：转义 HTML
 */
export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * XSS 防护：清理 HTML（保留安全标签）
 */
export function sanitizeHtml(html) {
    const allowedTags = ['b', 'i', 'em', 'strong', 'a', 'br', 'p'];
    const allowedAttributes = {
        'a': ['href', 'title']
    };
    
    const div = document.createElement('div');
    div.innerHTML = html;
    
    // 递归清理
    cleanNode(div);
    
    return div.innerHTML;
    
    function cleanNode(node) {
        const children = Array.from(node.childNodes);
        
        for (const child of children) {
            if (child.nodeType === Node.ELEMENT_NODE) {
                const tagName = child.tagName.toLowerCase();
                
                // 移除不允许的标签
                if (!allowedTags.includes(tagName)) {
                    child.replaceWith(...child.childNodes);
                    continue;
                }
                
                // 移除不允许的属性
                const allowedAttrs = allowedAttributes[tagName] || [];
                const attrs = Array.from(child.attributes);
                
                for (const attr of attrs) {
                    if (!allowedAttrs.includes(attr.name)) {
                        child.removeAttribute(attr.name);
                    }
                }
                
                // 递归处理子节点
                cleanNode(child);
            }
        }
    }
}

/**
 * 验证输入
 */
export function validateInput(value, rules = {}) {
    const errors = [];
    
    // 必填验证
    if (rules.required && !value) {
        errors.push('此字段为必填项');
    }
    
    // 最小长度
    if (rules.minLength && value.length < rules.minLength) {
        errors.push(`最小长度为 ${rules.minLength} 个字符`);
    }
    
    // 最大长度
    if (rules.maxLength && value.length > rules.maxLength) {
        errors.push(`最大长度为 ${rules.maxLength} 个字符`);
    }
    
    // 正则验证
    if (rules.pattern && !rules.pattern.test(value)) {
        errors.push(rules.patternMessage || '格式不正确');
    }
    
    // 自定义验证
    if (rules.validator) {
        const result = rules.validator(value);
        if (result !== true) {
            errors.push(result);
        }
    }
    
    return {
        valid: errors.length === 0,
        errors
    };
}

/**
 * 生成安全的随机 ID
 */
export function generateSecureId() {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

