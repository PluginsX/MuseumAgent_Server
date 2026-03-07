using Newtonsoft.Json;

namespace AgentClient.Runtime
{
    public static class CommonUtils
    {
        /// <summary>
        /// 序列化对象为JSON字符串（无格式化，用于运行时传输）
        /// </summary>
        /// <param name="obj">要序列化的对象</param>
        /// <returns>压缩的JSON字符串</returns>
        public static string SerializeToJson(object obj)
        {
            return JsonConvert.SerializeObject(obj, Formatting.None);
        }

        /// <summary>
        /// 序列化对象为格式化的JSON字符串（用于编辑器预览）
        /// </summary>
        /// <param name="obj">要序列化的对象</param>
        /// <returns>格式化的JSON字符串</returns>
        public static string SerializeToFormattedJson(object obj)
        {
            return JsonConvert.SerializeObject(obj, Formatting.Indented);
        }

        /// <summary>
        /// 深拷贝对象
        /// </summary>
        /// <typeparam name="T">对象类型</typeparam>
        /// <param name="source">源对象</param>
        /// <returns>深拷贝后的对象</returns>
        public static T DeepClone<T>(T source)
        {
            if (source == null) return default;
            string json = JsonConvert.SerializeObject(source);
            return JsonConvert.DeserializeObject<T>(json);
        }
    }
}