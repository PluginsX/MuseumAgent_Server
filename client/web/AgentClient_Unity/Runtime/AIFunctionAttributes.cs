// 文件：AIFunctionAttributes.cs
using System;

[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public class AIFunctionAttribute : Attribute
{
    public string Name { get; set; }
    public string Description { get; set; }
    public string Category { get; set; }
    public string[] Tags { get; set; }
    public string Example { get; set; }

    public AIFunctionAttribute(string description)
    {
        Description = description;
    }
}

[AttributeUsage(AttributeTargets.Parameter, AllowMultiple = false)]
public class AIParameterAttribute : Attribute
{
    public string Description { get; set; }
    public float Minimum { get; set; } = float.MinValue;
    public float Maximum { get; set; } = float.MaxValue;
    public string[] EnumOptions { get; set; }
    public string Unit { get; set; }
    public string Example { get; set; }

    public AIParameterAttribute(string description)
    {
        Description = description;
    }
}