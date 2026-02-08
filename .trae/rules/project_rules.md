2. 所有python脚本都是用项目专用虚拟环境,位置在：E:\Project\Python\MuseumAgent_Server\venv\Scripts\python.exe

3. 对话完全使用中文交流

4. 所有用于临时测试的脚本和各类文件都创建到E:\Project\Python\MuseumAgent_Server\Test\目录下

5. 该目录内都是测试文件和项目！绝不允许与主服务器产设任何耦合！E:\Project\Python\MuseumAgent_Server\Test\

6. 使用PowerShell的语法来发送请求

7. 清理临时文件时，禁止清理./Documents和./Test文件夹下的内容

8. 本服务服务器提供了管理员用的前端web页面，前端项目位置在：E:\Project\Python\MuseumAgent_Server\control-panel
9. 前端修改后必须重新构建 cd E:\Project\Python\MuseumAgent_Server\control-panel; npm run build

10. 专用名词解释
    - SRS：Semantic Retrieval System，语义检索系统，是外部提供的资料检索服务，通过APIdiao调用。