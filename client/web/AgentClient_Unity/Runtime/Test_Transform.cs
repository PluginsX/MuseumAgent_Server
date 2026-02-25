using UnityEngine;
using Museum.Debug;
using System.Collections;

public class Test_Transform : MonoBehaviour
{
    // 累加旋转（自动处理角度边界确保始终在360度范围内）
    [AIFunction("累加旋转，自动处理角度边界确保始终在360度范围内")]
    public void Add_Rotation(
        [AIParameter("Y轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float yaw,
        [AIParameter("X轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float pitch,
        [AIParameter("Z轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float roll,
        [AIParameter("过渡时长,单位毫秒,0为无过渡", Minimum = 0, Maximum = 10000, Unit = "毫秒")]  float duration = 500
    )
    {
        Log.Print("Test_Transform", "debug", $"Add_Rotation: yaw={yaw}, pitch={pitch}, roll={roll}, duration={duration}ms");
        
        try
        {
            Vector3 currentRotation = transform.eulerAngles;
            Vector3 targetRotation = currentRotation + new Vector3(pitch, yaw, roll);
            
            // 处理角度边界，确保始终在0-360范围内
            targetRotation.x = ClampAngle(targetRotation.x);
            targetRotation.y = ClampAngle(targetRotation.y);
            targetRotation.z = ClampAngle(targetRotation.z);
            
            if (duration > 0)
            {
                StartCoroutine(RotateToCoroutine(currentRotation, targetRotation, duration));
            }
            else
            {
                transform.eulerAngles = targetRotation;
                Log.Print("Test_Transform", "debug", $"旋转已更新: {transform.eulerAngles}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("Test_Transform", "error", $"Add_Rotation 失败: {e.Message}");
        }
    }
    
    // 沿着某个轴向旋转angle度
    [AIFunction("沿着指定轴向旋转指定角度")]
    public void Add_Rotation_ByAxis(
        [AIParameter("旋转轴向量")] Vector3 axis,
        [AIParameter("旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float angle,
        [AIParameter("过渡时长,单位毫秒,0为无过渡", Minimum = 0, Maximum = 10000, Unit = "毫秒")] float duration = 500
    )
    {
        Log.Print("Test_Transform", "debug", $"Add_Rotation_ByAxis: axis={axis}, angle={angle}, duration={duration}ms");
        
        try
        {
            // 检查轴向量有效性
            if (axis.sqrMagnitude < 0.001f)
            {
                Log.Print("Test_Transform", "error", "轴向量不能为零向量");
                return;
            }
            
            // 归一化轴向量，确保它是单位向量
            axis = axis.normalized;
            
            Quaternion currentRotation = transform.rotation;
            Quaternion targetRotation = Quaternion.AngleAxis(angle, axis) * currentRotation;
            
            if (duration > 0)
            {
                StartCoroutine(RotateQuaternionCoroutine(currentRotation, targetRotation, duration));
            }
            else
            {
                transform.rotation = targetRotation;
                Log.Print("Test_Transform", "debug", $"旋转已更新: {transform.rotation.eulerAngles}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("Test_Transform", "error", $"Add_Rotation_ByAxis 失败: {e.Message}");
        }
    }
    
    // 累加位置
    [AIFunction("累加物体位置")]
    public void Add_Position(
        [AIParameter("位置增量向量")] Vector3 position,
        [AIParameter("过渡时长,单位毫秒,0为无过渡", Minimum = 0, Maximum = 10000, Unit = "毫秒")]  float duration = 500
    )
    {
        Log.Print("Test_Transform", "debug", $"Add_Position: {position}, duration={duration}ms");
        
        try
        {
            Vector3 currentPosition = transform.position;
            Vector3 targetPosition = currentPosition + position;
            
            if (duration > 0)
            {
                StartCoroutine(MoveToCoroutine(currentPosition, targetPosition, duration));
            }
            else
            {
                transform.position = targetPosition;
                Log.Print("Test_Transform", "debug", $"位置已更新: {transform.position}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("Test_Transform", "error", $"Add_Position 失败: {e.Message}");
        }
    }
    
    // 设置旋转
    [AIFunction("设置物体旋转")]
    public void Set_Rotation(
        [AIParameter("目标旋转角度（度）")] Vector3 rotation,
        [AIParameter("过渡时长,单位毫秒,0为无过渡", Minimum = 0, Maximum = 10000, Unit = "毫秒")]  float duration = 500
    )
    {
        Log.Print("Test_Transform", "debug", $"Set_Rotation: {rotation}, duration={duration}ms");
        
        try
        {
            Vector3 currentRotation = transform.eulerAngles;
            Vector3 targetRotation = rotation;
            
            if (duration > 0)
            {
                StartCoroutine(RotateToCoroutine(currentRotation, targetRotation, duration));
            }
            else
            {
                transform.eulerAngles = targetRotation;
                Log.Print("Test_Transform", "debug", $"旋转已设置: {transform.eulerAngles}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("Test_Transform", "error", $"Set_Rotation 失败: {e.Message}");
        }
    }
    
    // 设置位置
    [AIFunction("设置物体位置")]
    public void Set_Position(
        [AIParameter("目标位置坐标")] Vector3 position,
        [AIParameter("过渡时长,单位毫秒,0为无过渡", Minimum = 0, Maximum = 10000, Unit = "毫秒")]  float duration = 500
    )
    {
        Log.Print("Test_Transform", "debug", $"Set_Position: {position}, duration={duration}ms");
        
        try
        {
            Vector3 currentPosition = transform.position;
            Vector3 targetPosition = position;
            
            if (duration > 0)
            {
                StartCoroutine(MoveToCoroutine(currentPosition, targetPosition, duration));
            }
            else
            {
                transform.position = targetPosition;
                Log.Print("Test_Transform", "debug", $"位置已设置: {transform.position}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("Test_Transform", "error", $"Set_Position 失败: {e.Message}");
        }
    }
    
    // 设置缩放
    [AIFunction("设置物体缩放")]
    public void Set_Scale(
        [AIParameter("目标缩放值")] Vector3 scale,
        [AIParameter("过渡时长,单位毫秒,0为无过渡", Minimum = 0, Maximum = 10000, Unit = "毫秒")]  float duration = 500
    )
    {
        Log.Print("Test_Transform", "debug", $"Set_Scale: {scale}, duration={duration}ms");
        
        try
        {
            Vector3 currentScale = transform.localScale;
            Vector3 targetScale = scale;
            
            if (duration > 0)
            {
                StartCoroutine(ScaleToCoroutine(currentScale, targetScale, duration));
            }
            else
            {
                transform.localScale = targetScale;
                Log.Print("Test_Transform", "debug", $"缩放已设置: {transform.localScale}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("Test_Transform", "error", $"Set_Scale 失败: {e.Message}");
        }
    }
    
    // 旋转插值协程（使用欧拉角）
    private IEnumerator RotateToCoroutine(Vector3 startRotation, Vector3 targetRotation, float durationMs)
    {
        float durationSeconds = durationMs / 1000f;
        float elapsedTime = 0;
        
        while (elapsedTime < durationSeconds)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / durationSeconds);
            
            Vector3 currentRotation = Vector3.Lerp(startRotation, targetRotation, t);
            transform.eulerAngles = currentRotation;
            
            yield return null;
        }
        
        transform.eulerAngles = targetRotation;
        Log.Print("Test_Transform", "debug", $"旋转插值完成: {transform.eulerAngles}");
    }
    
    // 旋转插值协程（使用四元数）
    private IEnumerator RotateQuaternionCoroutine(Quaternion startRotation, Quaternion targetRotation, float durationMs)
    {
        float durationSeconds = durationMs / 1000f;
        float elapsedTime = 0;
        
        while (elapsedTime < durationSeconds)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / durationSeconds);
            
            Quaternion currentRotation = Quaternion.Slerp(startRotation, targetRotation, t);
            transform.rotation = currentRotation;
            
            yield return null;
        }
        
        transform.rotation = targetRotation;
        Log.Print("Test_Transform", "debug", $"旋转插值完成: {transform.rotation.eulerAngles}");
    }
    
    // 位置插值协程
    private IEnumerator MoveToCoroutine(Vector3 startPosition, Vector3 targetPosition, float durationMs)
    {
        float durationSeconds = durationMs / 1000f;
        float elapsedTime = 0;
        
        while (elapsedTime < durationSeconds)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / durationSeconds);
            
            Vector3 currentPosition = Vector3.Lerp(startPosition, targetPosition, t);
            transform.position = currentPosition;
            
            yield return null;
        }
        
        transform.position = targetPosition;
        Log.Print("Test_Transform", "debug", $"位置插值完成: {transform.position}");
    }
    
    // 缩放插值协程
    private IEnumerator ScaleToCoroutine(Vector3 startScale, Vector3 targetScale, float durationMs)
    {
        float durationSeconds = durationMs / 1000f;
        float elapsedTime = 0;
        
        while (elapsedTime < durationSeconds)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / durationSeconds);
            
            Vector3 currentScale = Vector3.Lerp(startScale, targetScale, t);
            transform.localScale = currentScale;
            
            yield return null;
        }
        
        transform.localScale = targetScale;
        Log.Print("Test_Transform", "debug", $"缩放插值完成: {transform.localScale}");
    }
    
    // 处理角度边界，确保角度在0-360范围内
    private float ClampAngle(float angle)
    {
        angle %= 360;
        if (angle < 0)
        {
            angle += 360;
        }
        return angle;
    }
}
