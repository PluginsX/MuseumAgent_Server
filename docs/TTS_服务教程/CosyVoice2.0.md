CosyVoice2提供API接口，用于管理音频文件、创建语音合成等功能。本文为您介绍CosyVoice2支持的接口类型及调用方式。

## **准备工作**

1.  部署CosyVoice2 WebUI服务或Frontend/Backend分离式高性能服务，且需要挂载OSS或其他存储（用来保存上传的音频文件）。具体操作，请参见[快速部署WebUI服务](https://help.aliyun.com/zh/pai/use-cases/quick-deployment-of-cosyvoice2-0-webui-services)或[快速部署Frontend/Backend分离式高性能服务](https://help.aliyun.com/zh/pai/use-cases/rapid-deployment-of-decoupled-frontend-backend-high-performance-service)。
    
2.  获取服务访问地址和Token。
    
    **重要**
    
    -   对于Frontend/Backend分离式高性能服务，API调用的是**Frontend服务**。
        
    -   压测请使用vpc地址，相比公网可大幅提升处理速度。
        
    
    1.  单击CosyVoice2的WebUI服务或Frontend服务名称，在**概览**页面的**基本信息**区域，单击**查看调用信息**。
        
    2.  在**调用信息**配置面板的**共享网关**页签，获取服务访问地址（EAS\_SERVICE\_URL）和Token（EAS\_TOKEN），并将访问地址末尾的`/`删除。
        
        **说明**
        
        -   使用公网调用地址：调用客户端需支持访问公网。
            
        -   使用VPC调用地址：调用客户端必须与服务位于同一个专有网络内。
            
        
        ![image](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1572151571/p963429.png)
        
3.  准备音频文件。
    
    本方案中使用的参考音频如下：
    
    -   参考语音WAV文件：[zero\_shot\_prompt.wav](https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250603/usliib/zero_shot_prompt.wav)
        
    -   参考语音文本：`希望你以后能够做得比我还好哟`
        

## **接口列表**

### **上传参考音频文件**

-   调用方式
    
    | 调用地址 | `<EAS_SERVICE_URL>/api/v1/audio/reference_audio` |
    | --- | --- |
    | 请求方式 | POST |
    | 请求HEADERS | `Authorization: Bearer <EAS_TOKEN>` |
    | 请求参数 | - **file**：必填，表示需要上传的音频文件，支持MP3、WAV和PCM。类型：file，默认值：无。 - **text**：必填，表示音频文件对应的文字内容。类型：string。 |
    | 返回参数 | 返回一个reference audio object，详情请参见[返回参数列表](#002181fe28a5m)。 |
    
    **返回参数列表**
    
    | **参数** | **类型** | **说明** |
    | --- | --- | --- |
    | **id** | string | 音频文件对应的文件ID。 |
    | **filename** | string | 音频文件的文件名。 |
    | **bytes** | integer | 文件大小。 |
    | **created\\_at** | integer | 文件创建成功的时间戳。 |
    | **text** | string | 音频文件对应的文字内容。 |
    
-   请求示例
    
    #### **cURL**
    
    ```
    # <EAS_SERVICE_URL>和<EAS_TOKEN>需分别替换为服务访问地址和Token。 
    
    curl -XPOST <EAS_SERVICE_URL>/api/v1/audio/reference_audio \
        --header 'Authorization: Bearer <EAS_TOKEN>' \
        --form 'file=@"/home/xxxx/zero_shot_prompt.wav"' \
        --form 'text="希望你以后能够做得比我还好哟"'
    ```
    
    #### **Python**
    
    ```
    import requests
    
    response = requests.post(
        "<EAS_SERVICE_URL>/api/v1/audio/reference_audio",  # <EAS_SERVICE_URL>需替换为服务访问地址。
        headers={
            "Authorization": "Bearer <EAS_TOKEN>",  # <EAS_TOKEN>需替换为服务Token。
        },
        files={
            "file": open("./zero_shot_prompt.wav", "rb"),
        },
        data={
            "text": "希望你以后能够做得比我还好哟"
        }
    )
    
    print(response.text)
    ```
    
-   返回示例
    
    ```
    {
        "id": "50a5fdb9-c3ad-445a-adbb-3be32750****",
        "filename": "zero_shot_prompt.wav",
        "bytes": 111496,
        "created_at": 1748416005,
        "text": "希望你以后能够做得比我还好哟"
    }
    ```
    

### **查看参考音频文件列表**

-   调用方式
    
    | 调用地址 | <EAS\\_SERVICE\\_URL>/api/v1/audio/reference\\_audio |
    | --- | --- |
    | 请求方式 | GET |
    | 请求HEADERS | `Authorization: Bearer <EAS_TOKEN>` |
    | 请求参数 | - **limit**：选填，用于限制返回文件数。类型：integer，默认值：100。 - **order**：选填，类型：string。按对象的created\\_at时间戳排序，取值如下： - asc：升序 - desc（默认值）：降序 |
    | 返回参数 | 返回一个reference audio object的数组，详情请参见[上传音频的返回参数列表](#002181fe28a5m)。 |
    
-   请求示例
    
    #### **cURL**
    
    ```
    # <EAS_SERVICE_URL>和<EAS_TOKEN>需分别替换为服务访问地址和Token。
    
    curl -XGET <EAS_SERVICE_URL>/api/v1/audio/reference_audio?limit=10&order=desc \
          --header 'Authorization: Bearer <EAS_TOKEN>'
    ```
    
    #### **Python**
    
    ```
    import requests
    
    response = requests.get(
        "<EAS_SERVICE_URL>/api/v1/audio/reference_audio",  # <EAS_SERVICE_URL>需替换为服务访问地址。 
        headers={
            "Authorization": "Bearer <EAS_TOKEN>",  # <EAS_TOKEN>需替换为服务Token。
        }
    )
    
    print(response.text)
    ```
    
-   返回示例
    
    ```
    [
        {
            "id": "50a5fdb9-c3ad-445a-adbb-3be32750****",
            "filename": "zero_shot_prompt.wav",
            "bytes": 111496,
            "created_at": 1748416005,
            "text": "希望你以后能够做得比我还好哟"
        }
    ]
    ```
    

### **查看指定参考音频文件**

-   调用方式
    
    | 调用地址 | `<EAS_SERVICE_URL>/api/v1/audio/reference_audio/<reference_audio_id>` |
    | --- | --- |
    | 请求方式 | GET |
    | 请求HEADERS | `Authorization: Bearer <EAS_TOKEN>` |
    | 路径参数 | **reference\\_audio\\_id**：必填，表示参考音频ID，如何获取，请参见[查看参考音频文件列表](#871fa54a090iu)。类型：String，默认值：无。 |
    | 返回参数 | 返回一个reference audio object，详情请参见[返回参数列表](#002181fe28a5m)。 |
    
-   请求示例
    
    #### **cURL**
    
    ```
    # <EAS_SERVICE_URL>和<EAS_TOKEN>需分别替换为服务访问地址和Token。
    # <reference_audio_id>需替换为参考音频ID。
    curl -XGET <EAS_SERVICE_URL>/api/v1/audio/reference_audio/<reference_audio_id> \
          --header 'Authorization: Bearer <EAS_TOKEN>'
    ```
    
    #### **Python**
    
    ```
    import requests
    
    response = requests.get(
        "<EAS_SERVICE_URL>/api/v1/audio/reference_audio/<reference_audio_id>",  # <EAS_SERVICE_URL>需替换为服务访问地址。
        headers={
            "Authorization": "Bearer <EAS_TOKEN>",  # <EAS_TOKEN>需替换为服务Token。
        }
    )
    
    print(response.text)
    ```
    
-   返回示例
    
    ```
    {
        "id": "50a5fdb9-c3ad-445a-adbb-3be32750****",
        "filename": "zero_shot_prompt.wav",
        "bytes": 111496,
        "created_at": 1748416005,
        "text": "希望你以后能够做得比我还好哟"
    }
    ```
    

### **删除参考音频文件**

-   调用方式
    
    | 调用地址 | `<EAS_SERVICE_URL>/api/v1/audio/reference_audio/<reference_audio_id>` |
    | --- | --- |
    | 请求方式 | DELETE |
    | 请求HEADERS | `Authorization: Bearer <EAS_TOKEN>` |
    | 路径参数 | **reference\\_audio\\_id**：必填，表示参考音频ID，如何获取，请参见[查看参考音频文件列表](#871fa54a090iu)。类型：String，默认值：无。 |
    | 返回参数 | 返回一个reference audio object。 |
    
-   请求示例
    
    #### **cURL**
    
    ```
    # <EAS_SERVICE_URL>和<EAS_TOKEN>需分别替换为服务访问地址和Token。
    # <reference_audio_id>需替换为参考音频ID。 
    
    curl -XDELETE <EAS_SERVICE_URL>/api/v1/audio/reference_audio/<reference_audio_id> \
          --header 'Authorization: Bearer <EAS_TOKEN>'
    ```
    
    #### **Python**
    
    ```
    import requests
    
    response = requests.delete(
        "<EAS_SERVICE_URL>/api/v1/audio/reference_audio/<reference_audio_id>",  # <EAS_SERVICE_URL>需替换为服务访问地址。
        headers={
            "Authorization": "Bearer <EAS_TOKEN>",  # <EAS_TOKEN>需替换为服务Token。
        }
    )
    
    print(response.text)
    ```
    
-   返回示例
    
    ```
    {
        "code": "OK",
        "message": "reference audio: c0939ce0-308e-4073-918f-91ac88e3**** deleted.",
        "data": {}
    }
    ```
    

### **创建语音合成**

-   调用方式
    
    | 调用地址 | `<EAS_SERVICE_URL>/api/v1/audio/speech` |
    | --- | --- |
    | 请求方式 | POST |
    | 请求HEADERS | - `Authorization: Bearer <EAS_TOKEN>` - `Content-Type: application/json` |
    | 请求参数 | - **model**：必填，模型名称，目前仅支持CosyVoice2-0.5B。类型：string，默认值：无。 - **input**：必填，类型：object，默认值：无。表示输入内容，取值如下： - **mode**：必填，类型：string。音频合成模式，取值如下： - fast\\_replication：快速复刻 - cross\\_lingual\\_replication：跨语种复刻 - natural\\_language\\_replication：自然语言复刻 - **text**：必填，需要合成的文本。类型：string，默认值：无。 - **reference\\_audio\\_id**：必填，表示参考音频ID，如何获取，请参见[查看参考音频文件列表](#871fa54a090iu)。类型：string，默认值：无。 - **instruct**：选填，instruct文本，动态调整语音风格，例如语气、情感、语速等。仅模式选择natural\\_language\\_replication时生效。类型：string，默认值：无。 - **sample\\_rate**：选填，音频采样率。默认值：24000。 - **bit\\_rate:** 选填， 比特率。类型：string，默认值：192k。支持 16k、32k、48k、64k、128k、192k、256k、320k、384k。 - **volume**: 选填，音量。 类型：float，默认值：1.0。例如，3.0就是三倍音量，0.8就是0.8倍音量。 - **speed**：选填，输出语音的速度，取值范围：\\[0.5~2.0\\]。类型：float，默认值：1.0。 - **output\\_format**：选填，输出音频格式。目前支持的格式：wav、mp3、pcm。默认值：wav。 - **stream**：选填，是否输出流式。类型：boolean，默认值：true。 |
    | 返回参数 | 流式返回speech chunk object，详情请参见[返回参数列表](#7b5535df836ak)。 |
    
    **返回参数列表**
    
    | **参数** | **类型** | **说明** |
    | --- | --- | --- |
    | **request\\_id** | string | 请求ID。 |
    | **output** | string | 输出内容。 |
    | **audio** | object | 音频内容。 |
    | **audio.id** | string | 音频ID。 |
    | **audio.data** | string | WAV字节流转换为`Base64`编码的数据。 |
    | **finish\\_reason** | string | - **非流式输出**：成功返回取值为null，失败时返回原因。 - **流式输出**：正在生成时为null，因模型输出自然结束，或触发输入参数中的stop条件而结束时为"stop"。 |
    | **usage** | integer | 文件大小。 |
    
-   请求示例
    
    ## 非流式调用
    
    ## cURL
    
    -   <EAS\_SERVICE\_URL>和<EAS\_TOKEN>需分别替换为服务访问地址和Token。
        
    -   <reference\_audio\_id>需替换为参考音频ID。
        
    
    ```
    # <EAS_SERVICE_URL>和<EAS_TOKEN>需分别替换为服务访问地址和Token。
    # <reference_audio_id>需替换为参考音频ID。 
    
    curl -XPOST <EAS_SERVICE_URL>/api/v1/audio/speech \
    --header 'Authorization: Bearer <EAS_TOKEN>' \
    --header 'Content-Type: application/json' \
    --data '{
        "model": "CosyVoice2-0.5B",
        "input": {
            "mode": "natural_language_replication",
            "reference_audio_id": "<reference_audio_id>",
            "text": "收到好友从远方寄来的生日礼物，那份意外的惊喜与深深的祝福让我心中充满了甜蜜的快乐，笑容如花儿般绽放。",
            "speed": 1.0,
            "output_format": "mp3",
            "sample_rate": 32000,
            "bit_rate": "48k",
            "volume": 2.0,
            "instruct": "用四川话说"
        },
        "stream": false
    }'
    ```
    
    返回base64编码结果：
    
    ```
    {"output":{"finish_reason":null,"audio":{"data":"DNgB9djax9su3Ba...."}},"request_id": "f90a65be-f47b-46b5-9ddc-70bae550****"}
    ```
    
    ## Python
    
    需要安装如下依赖：
    
    ```
    pip install requests==2.32.3 packaging==24.2
    ```
    
    ```
    import json
    import base64
    import requests
    from packaging import version
    
    required_version = "2.32.3"
    
    if version.parse(requests.__version__) < version.parse(required_version):
        raise RuntimeError(f"requests version must >= {required_version}")
    
    with requests.post(
        "<EAS_SERVICE_URL>/api/v1/audio/speech",    # <EAS_SERVICE_URL>需替换为服务访问地址。
                                                    # 示例: "http://cosyvoice-frontend-test.1534081855183999.cn-hangzhou.pai-eas.aliyuncs.com/api/v1/audio/speech"
        headers={
            "Authorization": "Bearer <EAS_TOKEN>",  # <EAS_TOKEN>需替换为服务Token。
            "Content-Type": "application/json",
        },
        json={
            "model": "CosyVoice2-0.5B",
            "input": {
                "mode": "natural_language_replication",
                "reference_audio_id": "<reference_audio_id>",  # <reference_audio_id>需替换为参考音频ID。
                "text": "收到好友从远方寄来的生日礼物，那份意外的惊喜与深深的祝福让我心中充满了甜蜜的快乐，笑容如花儿般绽放。",
                "output_format": "mp3",
                "sample_rate": 24000,
                "speed": 1.0,
                "bit_rate": "48k",
                "volume": 2.0,
                "instruct": "用四川话说"
            },
            "stream": False
        },
        timeout=10
    ) as response:
        if response.status_code != 200:
            print(response.text)
            exit()
    
    
        data = json.loads(response.content)
        encode_buffer = data['output']['audio']['data']
        decode_buffer = base64.b64decode(encode_buffer)
    
        with open('./http_non_stream.mp3', 'wb') as f:
            f.write(decode_buffer)
    ```
    
    ## 流式调用
    
    ## cURL
    
    -   <EAS\_SERVICE\_URL>和<EAS\_TOKEN>需分别替换为服务访问地址和Token。
        
    -   <reference\_audio\_id>需替换为参考音频ID。
        
    
    ```
    # <EAS_SERVICE_URL>和<EAS_TOKEN>需分别替换为服务访问地址和Token。
    # <reference_audio_id>需替换为参考音频ID。 
    
    curl -XPOST <EAS_SERVICE_URL>/api/v1/audio/speech \
    --header 'Authorization: Bearer <EAS_TOKEN>' \
    --header 'Content-Type: application/json' \
    --data '{
        "model": "CosyVoice2-0.5B",
        "input": {
            "mode": "natural_language_replication",
            "reference_audio_id": "<reference_audio_id>",
            "text": "收到好友从远方寄来的生日礼物，那份意外的惊喜与深深的祝福让我心中充满了甜蜜的快乐，笑容如花儿般绽放。",
            "speed": 1.0,
            "output_format": "mp3",
            "sample_rate": 32000,
            "bit_rate": "48k",
            "volume": 2.0,
            "instruct": "用四川话说"
        },
        "stream": true
    }'
    ```
    
    返回base64位编码结果如下：
    
    ```
    data: {"output":{"finish_reason":null,"audio":{"data":"DNgB9djax9su3Ba...."}},"request_id": "f90a65be-f47b-46b5-9ddc-70bae550****"}
    data: {"output":{"finish_reason":null,"audio":{"data":"DNgB9djax9su3Ba...."}},"request_id": "f90a65be-f47b-46b5-9ddc-70bae550****"}
    data: {"output":{"finish_reason":null,"audio":{"data":"DNgB9djax9su3Ba...."}},"request_id": "f90a65be-f47b-46b5-9ddc-70bae550****"}
    data: {"output":{"finish_reason":null,"audio":{"data":"DNgB9djax9su3Ba...."}},"request_id": "f90a65be-f47b-46b5-9ddc-70bae550****"}
    ```
    
    ## Python
    
    需要安装Python SSE客户端：
    
    ```
    pip install requests==2.32.3 packaging==24.2 sseclient-py==1.8.0 -i http://mirrors.cloud.aliyuncs.com/pypi/simple --trusted-host mirrors.cloud.aliyuncs.com
    ```
    
    ```
    import io
    import json
    import base64
    import wave
    import requests
    from sseclient import SSEClient			# pip install sseclient-py
    from packaging import version
    
    required_version = "2.32.3"
    
    if version.parse(requests.__version__) < version.parse(required_version):
        raise RuntimeError(f"requests version must >= {required_version}")
    
    
    with requests.post(
        "<EAS_SERVICE_URL>/api/v1/audio/speech",    # <EAS_SERVICE_URL>需替换为服务访问地址。
                                                    # 示例: "http://cosyvoice-frontend-test.1534081855183999.cn-hangzhou.pai-eas.aliyuncs.com/api/v1/audio/speech"
        headers={
            "Authorization": "Bearer <EAS_TOKEN>",  # <EAS_TOKEN>需替换为服务Token。
            "Content-Type": "application/json",
        },
        json={
            "model": "CosyVoice2-0.5B",
            "input": {
                "mode": "natural_language_replication",
                "reference_audio_id": "<reference_audio_id>",  # <reference_audio_id>需替换为参考音频ID。 
                "text": "收到好友从远方寄来的生日礼物，那份意外的惊喜与深深的祝福让我心中充满了甜蜜的快乐，笑容如花儿般绽放。",
                "output_format": "mp3",
                "sample_rate": 24000,
                "speed": 1.0,
                "bit_rate": "48k",
                "volume": 2.0,
                "instruct": "用四川话说",
                "debug": True
            },
            "stream": True
        },
        stream=True,
        timeout=10
    ) as response:
        if response.status_code != 200:
            print(response.text)
            exit()
    
        messages = SSEClient(response)
        with open('./http_stream.mp3', 'wb') as f:
            for i, msg in enumerate(messages.events()):
                print(f"Event: {msg.event}, Data: {msg.data}")
                data = json.loads(msg.data)
                if data['error'] is not None:
                    print(data['error'])
                    break
                metrics = data['metrics']
                print(f"{metrics=}")
                encode_buffer = data['output']['audio']['data']
                decode_buffer = base64.b64decode(encode_buffer)
                f.write(decode_buffer)
    ```
    
    ## Websocket API
    
    需要安装如下依赖：
    
    ```
    pip install websocket-client==1.8.0 -i http://mirrors.cloud.aliyuncs.com/pypi/simple --trusted-host mirrors.cloud.aliyuncs.com
    ```
    
    ```
    #!/usr/bin/python
    # -*- coding: utf-8 -*-
    
    import base64
    import json
    import logging
    import sys
    import time
    import uuid
    import traceback
    import websocket
    
    
    class TTSClient:
        def __init__(self, api_key, uri, params, log_level='INFO'):
            """
        初始化 TTSClient 实例
    
        参数:
            api_key (str): 鉴权用的 API Key
            uri (str): WebSocket 服务地址
        """
            self._api_key = api_key  # 替换为你的 API Key
            self._uri = uri  # 替换为你的 WebSocket 地址
            self._task_id = str(uuid.uuid4())  # 生成唯一任务 ID
            self._ws = None  # WebSocketApp 实例
            self._task_started = False  # 是否收到 task-started
            self._task_finished = False  # 是否收到 task-finished / task-failed
            self._check_params(params)
            self._params = params
            self._chunk_metrics = []
            self._metrics = {}
            self._first_package_time = None
            self._last_time = None
            self._init_log(log_level)
            self.audio_data = b''
    
        def _init_log(self, log_level):
            self._log = logging.getLogger("ws_client")
            log_formatter = logging.Formatter('%(asctime)s - Process(%(process)s) - %(levelname)s - %(message)s')
            stream_handler = logging.StreamHandler(stream=sys.stdout)
            stream_handler.setFormatter(log_formatter)
            self._log.addHandler(stream_handler)
            self._log.setLevel(log_level)
    
        def get_metrics(self):
            """获取合成结果性能指标"""
            return self._metrics
    
        def _check_params(self, params):
            assert 'mode' in params and params['mode'] in ['fast_replication', 'cross_lingual_replication', 'natural_language_replication']
            assert 'reference_audio_id' in params
            assert 'output_format' in params and params['output_format'] in ['wav', 'mp3', 'pcm']
            if params['mode'] == 'natural_language_replication':
                assert 'instruct' in params and params['instruct']
            else:
                if 'instruct' in params:
                    del params['instruct']
    
        def on_open(self, ws):
            """
        WebSocket 连接建立时回调函数
        发送 run-task 指令开启语音合成任务
        """
            self._log.debug("WebSocket 已连接")
    
            # 构造 run-task 指令
            run_task_cmd = {
                "header": {
                    "action": "run-task",
                    "task_id": self._task_id,
                    "streaming": "duplex"
                },
                "payload": {
                    "task_group": "audio",
                    "task": "tts",
                    "function": "SpeechSynthesizer",
                    "model": "cosyvoice-v2",
                    "parameters": {
                        "mode": self._params['mode'],
                        "reference_audio_id": self._params['reference_audio_id'],
                        "output_format": self._params.get('output_format', 'wav'),
                        "sample_rate": self._params.get('sample_rate', 24000),
                        "bit_rate": self._params.get('bit_rate', '192k'),
                        "volume": self._params.get('volume', 1.0),
                        "instruct": self._params.get('instruct', ''),
                        "speed": self._params.get('speed', 1.0),
                        "debug": True,
                    },
                    "input": {}
                }
            }
    
            # 发送 run-task 指令
            ws.send(json.dumps(run_task_cmd))
            self._log.debug("已发送 run-task 指令")
    
        def on_message(self, ws, message):
            """
        接收到消息时的回调函数
        区分文本和二进制消息处理
        """
            try:
                msg_json = json.loads(message)
                # self._log.debug(f"收到 JSON 消息: {msg_json}")
                self._log.debug(f"收到 JSON 消息: {msg_json['header']['event']}")
    
                if "header" in msg_json:
                    header = msg_json["header"]
    
                    if "event" in header:
                        event = header["event"]
    
                        if event == "task-started":
                            self._log.debug("任务已启动")
                            self._task_started = True
    
                            # 发送 continue-task 指令
                            for text in self._params['texts']:
                                self.send_continue_task(text)
    
                            # 所有 continue-task 发送完成后发送 finish-task
                            self.send_finish_task()
                            self._last_time = time.time()
                        elif event == "result-generated":
                            metrics = msg_json['payload']['metrics']
                            cur_time = time.time()
                            metrics['client_cost_time'] = cur_time - self._last_time
                            self._last_time = cur_time
    
                            encode_data = msg_json["payload"]["output"]["audio"]["data"]
                            decode_data = base64.b64decode(encode_data)
                            self._log.debug(f"收到音频数据，大小: {len(decode_data)} 字节")
                            self.audio_data += decode_data
    
                            metrics['client_rtf'] = metrics['client_cost_time'] / metrics['speech_len']
                            self._chunk_metrics.append(metrics)
    
                        elif event == "task-finished":
                            self._metrics = {
                                'client_first_package_time': self._chunk_metrics[0]['client_cost_time'],
                                "client_rtf": sum([m["client_cost_time"] for m in self._chunk_metrics]) / sum([m["speech_len"] for m in self._chunk_metrics]),
                                'client_cost_time': sum([m["client_cost_time"] for m in self._chunk_metrics]),
                                'speech_len': sum([m["speech_len"] for m in self._chunk_metrics]),
                                'server_first_package_time': self._chunk_metrics[0]['server_cost_time'],
                                'server_rtf': sum([m["server_cost_time"] for m in self._chunk_metrics]) / sum([m["speech_len"] for m in self._chunk_metrics]),
                                'server_cost_time': sum([m["server_cost_time"] for m in self._chunk_metrics]),
                                "generate_time": sum([m["generate_time"] for m in self._chunk_metrics])
                            }
    
                            self._log.debug(f"任务已完成, 请求性能指标: client_first_package_time: {self._metrics['client_first_package_time']:.3f}, client_rtf: {self._metrics['client_rtf']:.3f}, client_cost_time: {self._metrics['client_cost_time']:.3f}, speech_len: {self._metrics['speech_len']:.3f}, server_cost_time: {self._metrics['server_cost_time']:.3f}, generate_time: {self._metrics['generate_time']:.3f}")
                            self._task_finished = True
                            self.close(ws)
    
                        elif event == "task-failed":
                            self._log.error(f"任务失败: {msg_json}")
                            self._task_finished = True
                            self.close(ws)
    
            except json.JSONDecodeError as e:
                self._log.error(f"JSON 解析失败: {str(e)}\t{traceback.format_exc()}")
    
        def on_error(self, ws, error):
            """发生错误时的回调"""
            self._log.error(f"WebSocket 出错: {error}\t{traceback.format_exc()}")
            self._metrics = {'error': error}
    
        def on_close(self, ws, close_status_code, close_msg):
            """连接关闭时的回调"""
            self._log.debug(f"WebSocket 已关闭: {close_msg} ({close_status_code})")
    
        def send_continue_task(self, text):
            """发送 continue-task 指令，附带要合成的文本内容"""
            cmd = {
                "header": {
                    "action": "continue-task",
                    "task_id": self._task_id,
                    "streaming": "duplex"
                },
                "payload": {
                    "input": {
                        "text": text
                    }
                }
            }
    
            self._ws.send(json.dumps(cmd))
            self._log.debug(f"已发送 continue-task 指令，文本内容: {text}")
    
        def send_finish_task(self):
            """发送 finish-task 指令，结束语音合成任务"""
            cmd = {
                "header": {
                    "action": "finish-task",
                    "task_id": self._task_id,
                    "streaming": "duplex"
                },
                "payload": {
                    "input": {}
                }
            }
    
            self._ws.send(json.dumps(cmd))
            self._log.debug("已发送 finish-task 指令")
    
        def close(self, ws):
            """主动关闭连接"""
            if ws and ws.sock and ws.sock.connected:
                ws.close()
                self._log.debug("已主动关闭连接")
    
        def run(self):
            """启动 WebSocket 客户端"""
            # 设置请求头部（鉴权）
            header = {
                "Authorization": f"Bearer {self._api_key}",
            }
    
            # 创建 WebSocketApp 实例
            self._ws = websocket.WebSocketApp(
                self._uri,
                header=header,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
    
            self._log.debug("正在监听 WebSocket 消息...")
            self._ws.run_forever()  # 启动长连接监听
    
    
    # 示例使用方式
    if __name__ == "__main__":
        API_KEY = "<EAS_TOKEN>"                                      # <EAS_TOKEN>需替换为服务Token
        SERVER_URI = "ws://<EAS_SERVICE_URL>/api-ws/v1/audio/speech" # <EAS_SERVICE_URL>需替换为服务访问地址。
                                                                     # 示例: "ws://cosyvoice-frontend-test.1534081855183999.cn-hangzhou.pai-eas.aliyuncs.com/api-ws/v1/audio/speech"
        texts = [
            "收到好友从远方寄来的生日礼物，那份意外的惊喜与深深的祝福让我心中充满了甜蜜的快乐，笑容如花儿般绽放。"
        ]
        params = {
            "mode": "natural_language_replication",
            "texts": texts,
            "reference_audio_id": "<reference_audio_id>",
            "speed": 1.0,
            "output_format": "mp3",
            "sample_rate": 24000,
            "bit_rate": "48k",
            "volume": 2.0,
            "instruct": "用冷静的语气说"
        }
    
        client = TTSClient(API_KEY, SERVER_URI, params, log_level='DEBUG')
        client.run()
        with open('./websocket_stream.mp3', 'wb') as wfile:
            wfile.write(client.audio_data)
        metrics = client.get_metrics()
        print(f"{metrics=}")
    ```