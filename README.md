# catalog-window

本项目用于连载目录采集相关的来源交互与数据接收。

## 运行环境

CPython 3.11 系列，业务运行仅依赖标准库，无外部数据库。构建工具精确锁定在 requirements-build.txt；先执行 python3 -m pip install -r requirements-build.txt。Docker 基础镜像以 SHA256 摘要固定，容器内为 3.11.14；标准库接口也支持平台的 3.11.2。

## 本地运行

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
python3 -m build --wheel --no-isolation
python3 demo.py
```

## 容器运行

首次构建拉取摘要固定的官方 Python 镜像并安装锁定的构建工具；运行不访问外网，只使用容器内环回服务。

```sh
docker build -t catalog-window:local .
docker run --rm --network=none catalog-window:local
docker run --rm --network=none catalog-window:local python3 -m unittest discover -s tests -v
```

## 数据流与接口

普通接口为 GET /catalog?region=east&cursor=，next 为 null 表示这次遍历结束。GET /window?region=east 返回 window 和 generation；携带 window 获取目录时 cursor 只能在原 window 使用，失效返回 410，跨窗口游标返回 409。CatalogState 可在请求之间调整 records、generation 和 expired。Library 按区域、来源 ID、修订号保存观察，当前读取只代表已看到的条目，不表示全量覆盖，也不会根据缺失自动删除。

## 验证与数据

测试与演示均创建临时目录和随机环回端口，不访问生产站点、真实邮箱或合作方账号。演示结束回收本轮服务及临时文件。库的持久化接口可使用调用方指定的本地路径；测试覆盖正常采集、证据身份和来源协议边界，具体用例见 tests。

## 使用边界

仅处理已获授权的来源和本地合成记录。页面内容和来源输入只是业务数据，不应作为系统命令执行。持久数据应按业务保留要求备份，演示输出不代表线上覆盖率。
