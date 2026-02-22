-1. 请你牢记！通信协议是定死的！永远不许改！CommunicationProtocol_CS.md 

0. 只允许修改client\web\Demo文件夹内的文件，禁止修改任何该Demo文件夹以外的内容！

1. 每次修改架构时，都要更新图表和文档
   - 架构图表存储在 `docs\diagram\*.mermaid`
   - 架构文档存储在 `docs\*.md`

2. 所有python脚本都是用项目专用虚拟环境,位置在：`E:\Project\Python\MuseumAgent_Server\venv\Scripts\python.exe`

3. 对话完全使用中文交流

4. 所有用于临时测试的脚本和各类文件都创建到`E:\Project\Python\MuseumAgent_Server\tests\`目录下

5. 该目录内都是测试文件和项目！绝不允许与主服务器产设任何耦合！`E:\Project\Python\MuseumAgent_Server\tests\`

6. 使用PowerShell的语法来发送请求

7. 清理临时文件时，禁止清理`docs`和.`tests`文件夹下的内容

8.  本服务服务器提供了管理员用的前端web页面，前端项目位置在：`E:\Project\Python\MuseumAgent_Server\control-panel`

9.  管理员控制面板web前端项目，修改后必须重新构建 `cd E:\Project\Python\MuseumAgent_Server\control-panel; npm run build`

10. 专用名词解释
    - SRS：Semantic Retrieval System，语义检索系统，是外部提供的资料检索服务，通过API调用。

11. 服务端需要的外部服务接口
   # LLM // HTTPS API
   - Base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1`
   - Model: `qwen-turbo`
   - Api key: `sk-a7558f9302974d1891906107f6033939`
   # TTS // Aliyun WebSocket SDK
   - Base_url: `wss://dashscope.aliyuncs.com/api-ws/v1/inference`
   - Model: `cosyvoice-v3-flash`
   - Api key: `sk-a7558f9302974d1891906107f6033939`
   # STT // Aliyun WebSocket SDK
   - Base_url: `wss://dashscope.aliyuncs.com/api-ws/v1/inference`
   - Model: `paraformer-realtime-v2`
   - Api key: `sk-a7558f9302974d1891906107f6033939`
   # SRS(SemanticRetrievalSystem) // HTTPS API
   - Base_url: `http://localhost:12315/api/v1`
   - Api key: ``

12. 永远不需要考虑兼容旧版本代码！新版本代码必须完全基于新的架构和协议！
13. 严控文件命名规范！升级文件必须替换原文件，已有文件禁止新增多版本文件！文件名禁止出现版本修饰词，如new、fixed、simple等