using UnityEngine;
using Museum.Debug;
using System.Collections;

public class LightController : MonoBehaviour
{
    [Header("灯光设置")]
    [Tooltip("引用的方向光组件")]
    public Light directLight;

    void Start()
    {
        if (directLight == null)
        {
            directLight = GetComponent<Light>();
            if (directLight == null)
            {
                Log.Print("LightController", "error", "未找到 Light 组件,请手动指定或确保该组件挂载在带有 Light 的物体上");
            }
            else
            {
                Log.Print("LightController", "debug", $"自动找到 Light 组件,初始强度: {directLight.intensity}, 初始颜色: {directLight.color}");
            }
        }
        else
        {
            Log.Print("LightController", "debug", $"使用指定的 Light 组件,初始强度: {directLight.intensity}, 初始颜色: {directLight.color}");
        }
    }

    [AIFunction("控制环境光的开关和明亮")]
    public void Set_Intensity(
        [AIParameter("目标强度值", Minimum = 0, Maximum = 10)] float intensity,
        [AIParameter("过渡时长(毫秒),0表示直接设置", Minimum = 0, Maximum = 10000, Unit = "毫秒")] float duration = 500
    )
    {
        Log.Print("LightController", "debug", $"Set_Intensity: intensity={intensity}, duration={duration}ms");
        
        try
        {
            if (directLight == null)
            {
                Log.Print("LightController", "error", "未找到 Light 组件");
                return;
            }

            float currentIntensity = directLight.intensity;
            
            if (duration > 0)
            {
                StartCoroutine(IntensityToCoroutine(currentIntensity, intensity, duration));
            }
            else
            {
                directLight.intensity = intensity;
                Log.Print("LightController", "debug", $"强度已设置: {directLight.intensity}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("LightController", "error", $"Set_Intensity 失败: {e.Message}");
        }
    }

    [AIFunction("设置灯光颜色")]
    public void Set_Color(
        [AIParameter("目标颜色(RGB值,0-1)")] Vector3 color,
        [AIParameter("过渡时长(毫秒),0表示直接设置", Minimum = 0, Maximum = 10000, Unit = "毫秒")] float duration = 500
    )
    {
        Log.Print("LightController", "debug", $"Set_Color: color={color}, duration={duration}ms");
        
        try
        {
            if (directLight == null)
            {
                Log.Print("LightController", "error", "未找到 Light 组件");
                return;
            }

            Color currentColor = directLight.color;
            Color targetColor = new Color(color.x, color.y, color.z);
            
            if (duration > 0)
            {
                StartCoroutine(ColorToCoroutine(currentColor, targetColor, duration));
            }
            else
            {
                directLight.color = targetColor;
                Log.Print("LightController", "debug", $"颜色已设置: {directLight.color}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("LightController", "error", $"Set_Color 失败: {e.Message}");
        }
    }

    private IEnumerator IntensityToCoroutine(float startIntensity, float targetIntensity, float durationMs)
    {
        float durationSeconds = durationMs / 1000f;
        float elapsedTime = 0;
        
        while (elapsedTime < durationSeconds)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / durationSeconds);
            
            float currentIntensity = Mathf.Lerp(startIntensity, targetIntensity, t);
            directLight.intensity = currentIntensity;
            
            yield return null;
        }
        
        directLight.intensity = targetIntensity;
        Log.Print("LightController", "debug", $"强度插值完成: {directLight.intensity}");
    }

    private IEnumerator ColorToCoroutine(Color startColor, Color targetColor, float durationMs)
    {
        float durationSeconds = durationMs / 1000f;
        float elapsedTime = 0;
        
        while (elapsedTime < durationSeconds)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / durationSeconds);
            
            Color currentColor = Color.Lerp(startColor, targetColor, t);
            directLight.color = currentColor;
            
            yield return null;
        }
        
        directLight.color = targetColor;
        Log.Print("LightController", "debug", $"颜色插值完成: {directLight.color}");
    }
}
