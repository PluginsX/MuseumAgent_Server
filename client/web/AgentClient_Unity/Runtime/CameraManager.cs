using UnityEngine;
using Museum.Debug;
using System.Collections;
using System.Collections.Generic;

public class CameraManager : MonoBehaviour
{
    [Header("摄像机设置")]
    [Tooltip("摄像机列表")]
    public List<Camera> cameras = new List<Camera>();

    [Header("过渡设置")]
    [Tooltip("切换过渡时长（毫秒）")]
    [Range(0, 5000)]
    public float transitionDuration = 1000f;

    [Tooltip("是否使用平滑过渡")]
    public bool useSmoothTransition = true;

    [Header("调试信息")]
    [Tooltip("当前激活的摄像机索引")]
    [SerializeField]
    private int currentCameraIndex = -1;

    [Tooltip("是否启用摄像机控制")]
    public bool enableCameraControl = true;

    private Coroutine transitionCoroutine;

    void Start()
    {
        InitializeCameras();
        SetActiveCamera(0, false);
    }

    void InitializeCameras()
    {
        if (cameras.Count == 0)
        {
            Log.Print("CameraManager", "warning", "摄像机列表为空，自动查找场景中的摄像机");
            Camera[] allCameras = FindObjectsOfType<Camera>();
            cameras.AddRange(allCameras);
            Log.Print("CameraManager", "debug", $"找到 {cameras.Count} 个摄像机");
        }
        else
        {
            Log.Print("CameraManager", "debug", $"使用指定的 {cameras.Count} 个摄像机");
        }

        DisableAllCameras();
    }

    void DisableAllCameras()
    {
        foreach (var cam in cameras)
        {
            if (cam != null)
            {
                cam.enabled = false;
            }
        }
    }

    [AIFunction("切换到指定摄像机")]
    public void Switch_Camera(
        [AIParameter("摄像机索引", Minimum = 0, Unit = "个")] int cameraIndex,
        [AIParameter("过渡时长（毫秒），0表示直接切换", Minimum = 0,  Maximum = 10000, Unit = "毫秒")] float duration = 500
    )
    {
        Log.Print("CameraManager", "debug", $"Switch_Camera: cameraIndex={cameraIndex}, duration={duration}ms");
        
        try
        {
            if (!enableCameraControl)
            {
                Log.Print("CameraManager", "warning", "摄像机控制未启用");
                return;
            }

            if (cameraIndex < 0 || cameraIndex >= cameras.Count)
            {
                Log.Print("CameraManager", "error", $"摄像机索引超出范围: {cameraIndex}，总共有 {cameras.Count} 个摄像机");
                return;
            }

            if (cameras[cameraIndex] == null)
            {
                Log.Print("CameraManager", "error", $"摄像机索引 {cameraIndex} 为 null");
                return;
            }

            bool useTransition = duration > 0 || useSmoothTransition;
            SetActiveCamera(cameraIndex, useTransition);
        }
        catch (System.Exception e)
        {
            Log.Print("CameraManager", "error", $"Switch_Camera 失败: {e.Message}");
        }
    }

    [AIFunction("切换到下一个摄像机")]
    public void Next_Camera(
        [AIParameter("过渡时长（毫秒），0表示直接切换", Minimum = 0, Maximum = 10000, Unit = "毫秒")] float duration = 500
    )
    {
        Log.Print("CameraManager", "debug", $"Next_Camera: duration={duration}ms");
        
        try
        {
            if (!enableCameraControl)
            {
                Log.Print("CameraManager", "warning", "摄像机控制未启用");
                return;
            }

            int nextIndex = (currentCameraIndex + 1) % cameras.Count;
            bool useTransition = duration > 0 || useSmoothTransition;
            SetActiveCamera(nextIndex, useTransition);
        }
        catch (System.Exception e)
        {
            Log.Print("CameraManager", "error", $"Next_Camera 失败: {e.Message}");
        }
    }

    [AIFunction("切换到上一个摄像机")]
    public void Previous_Camera(
        [AIParameter("过渡时长（毫秒），0表示直接切换", Minimum = 0,  Maximum = 10000, Unit = "毫秒")] float duration = 500
    )
    {
        Log.Print("CameraManager", "debug", $"Previous_Camera: duration={duration}ms");
        
        try
        {
            if (!enableCameraControl)
            {
                Log.Print("CameraManager", "warning", "摄像机控制未启用");
                return;
            }

            int prevIndex = (currentCameraIndex - 1 + cameras.Count) % cameras.Count;
            bool useTransition = duration > 0 || useSmoothTransition;
            SetActiveCamera(prevIndex, useTransition);
        }
        catch (System.Exception e)
        {
            Log.Print("CameraManager", "error", $"Previous_Camera 失败: {e.Message}");
        }
    }

    [AIFunction("设置摄像机位置")]
    public void Set_Camera_Position(
        [AIParameter("目标位置坐标")] Vector3 position,
        [AIParameter("过渡时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 500
    )
    {
        Log.Print("CameraManager", "debug", $"Set_Camera_Position: position={position}, duration={duration}ms");
        
        try
        {
            if (!enableCameraControl)
            {
                Log.Print("CameraManager", "warning", "摄像机控制未启用");
                return;
            }

            if (currentCameraIndex < 0 || currentCameraIndex >= cameras.Count)
            {
                Log.Print("CameraManager", "error", "没有激活的摄像机");
                return;
            }

            Camera currentCamera = cameras[currentCameraIndex];
            if (currentCamera == null)
            {
                Log.Print("CameraManager", "error", "当前摄像机为 null");
                return;
            }

            if (duration > 0)
            {
                StartCoroutine(CameraPositionCoroutine(currentCamera.transform.position, position, duration));
            }
            else
            {
                currentCamera.transform.position = position;
                Log.Print("CameraManager", "debug", $"摄像机位置已设置: {currentCamera.transform.position}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("CameraManager", "error", $"Set_Camera_Position 失败: {e.Message}");
        }
    }

    [AIFunction("设置摄像机旋转")]
    public void Set_Camera_Rotation(
        [AIParameter("目标旋转角度（度）")] Vector3 rotation,
        [AIParameter("过渡时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 500
    )
    {
        Log.Print("CameraManager", "debug", $"Set_Camera_Rotation: rotation={rotation}, duration={duration}ms");
        
        try
        {
            if (!enableCameraControl)
            {
                Log.Print("CameraManager", "warning", "摄像机控制未启用");
                return;
            }

            if (currentCameraIndex < 0 || currentCameraIndex >= cameras.Count)
            {
                Log.Print("CameraManager", "error", "没有激活的摄像机");
                return;
            }

            Camera currentCamera = cameras[currentCameraIndex];
            if (currentCamera == null)
            {
                Log.Print("CameraManager", "error", "当前摄像机为 null");
                return;
            }

            if (duration > 0)
            {
                StartCoroutine(CameraRotationCoroutine(currentCamera.transform.eulerAngles, rotation, duration));
            }
            else
            {
                currentCamera.transform.eulerAngles = rotation;
                Log.Print("CameraManager", "debug", $"摄像机旋转已设置: {currentCamera.transform.eulerAngles}");
            }
        }
        catch (System.Exception e)
        {
            Log.Print("CameraManager", "error", $"Set_Camera_Rotation 失败: {e.Message}");
        }
    }

    private void SetActiveCamera(int index, bool useTransition)
    {
        if (index < 0 || index >= cameras.Count)
        {
            Log.Print("CameraManager", "error", $"摄像机索引超出范围: {index}");
            return;
        }

        Camera targetCamera = cameras[index];
        if (targetCamera == null)
        {
            Log.Print("CameraManager", "error", $"目标摄像机为 null");
            return;
        }

        if (transitionCoroutine != null)
        {
            StopCoroutine(transitionCoroutine);
            transitionCoroutine = null;
        }

        if (useTransition && currentCameraIndex >= 0 && currentCameraIndex < cameras.Count)
        {
            Camera currentCamera = cameras[currentCameraIndex];
            if (currentCamera != null && currentCamera != targetCamera)
            {
                transitionCoroutine = StartCoroutine(CameraTransitionCoroutine(currentCamera, targetCamera, transitionDuration / 1000f));
            }
            else
            {
                ActivateCamera(targetCamera);
            }
        }
        else
        {
            ActivateCamera(targetCamera);
        }
    }

    private void ActivateCamera(Camera camera)
    {
        DisableAllCameras();
        camera.enabled = true;
        currentCameraIndex = cameras.IndexOf(camera);
        Log.Print("CameraManager", "debug", $"摄像机已切换到索引: {currentCameraIndex}");
    }

    private IEnumerator CameraTransitionCoroutine(Camera fromCamera, Camera toCamera, float duration)
    {
        Log.Print("CameraManager", "debug", $"开始摄像机过渡: {duration}秒");
        
        float elapsedTime = 0;
        Vector3 startPosition = fromCamera.transform.position;
        Quaternion startRotation = fromCamera.transform.rotation;
        float startFOV = fromCamera.fieldOfView;
        
        Vector3 endPosition = toCamera.transform.position;
        Quaternion endRotation = toCamera.transform.rotation;
        float endFOV = toCamera.fieldOfView;
        
        toCamera.enabled = true;
        
        while (elapsedTime < duration)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / duration);
            
            float smoothT = Mathf.SmoothStep(0, 1, t);
            
            fromCamera.transform.position = Vector3.Lerp(startPosition, endPosition, smoothT);
            fromCamera.transform.rotation = Quaternion.Slerp(startRotation, endRotation, smoothT);
            fromCamera.fieldOfView = Mathf.Lerp(startFOV, endFOV, smoothT);
            
            yield return null;
        }
        
        ActivateCamera(toCamera);
        Log.Print("CameraManager", "debug", $"摄像机过渡完成");
    }

    private IEnumerator CameraPositionCoroutine(Vector3 startPosition, Vector3 endPosition, float durationMs)
    {
        float durationSeconds = durationMs / 1000f;
        float elapsedTime = 0;
        
        while (elapsedTime < durationSeconds)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / durationSeconds);
            
            Vector3 currentPosition = Vector3.Lerp(startPosition, endPosition, t);
            cameras[currentCameraIndex].transform.position = currentPosition;
            
            yield return null;
        }
        
        cameras[currentCameraIndex].transform.position = endPosition;
        Log.Print("CameraManager", "debug", $"摄像机位置插值完成: {endPosition}");
    }

    private IEnumerator CameraRotationCoroutine(Vector3 startRotation, Vector3 endRotation, float durationMs)
    {
        float durationSeconds = durationMs / 1000f;
        float elapsedTime = 0;
        
        while (elapsedTime < durationSeconds)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / durationSeconds);
            
            Vector3 currentRotation = Vector3.Lerp(startRotation, endRotation, t);
            cameras[currentCameraIndex].transform.eulerAngles = currentRotation;
            
            yield return null;
        }
        
        cameras[currentCameraIndex].transform.eulerAngles = endRotation;
        Log.Print("CameraManager", "debug", $"摄像机旋转插值完成: {endRotation}");
    }

    void OnValidate()
    {
        transitionDuration = Mathf.Clamp(transitionDuration, 0, 5000);
    }
}
