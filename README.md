# 我的待办清单

一个用 Python + Flask 实现的简单待办事项工具，带网页界面，支持本地数据持久化。

## 功能

- 添加待办任务
- 标记任务完成
- 删除单条任务
- 一键清空全部任务
- 自动统计全部、已完成、未完成任务数量
- 任务保存到本地 `todos.json`，重启后数据不会丢失
- 支持部署到 Render

## 项目结构

```text
to_do_list/
├─ main.py
├─ requirements.txt
├─ render.yaml
├─ .gitignore
└─ README.md
```

说明：

- `main.py`：Flask 主程序，页面 HTML 也写在这个文件里
- `requirements.txt`：项目依赖
- `render.yaml`：Render 部署配置
- `todos.json`：运行时自动生成的数据文件，不需要提交到 GitHub

## 本地运行

### 1. 创建虚拟环境（可选）

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

如果你的电脑使用 `py` 命令：

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3. 启动项目

```powershell
python main.py
```

如果你的电脑使用 `py` 命令：

```powershell
py main.py
```

### 4. 打开网页

浏览器访问：

```text
http://127.0.0.1:5000/
```

## 数据说明

- 默认情况下，任务数据保存在项目目录下的 `todos.json`
- 线上部署时，可以通过环境变量 `TODO_FILE_PATH` 指定保存路径

例如：

```text
TODO_FILE_PATH=/var/data/todos.json
```

## 部署到 Render

这个项目已经自带 `render.yaml`，可以直接用于部署。

### 部署步骤

1. 把 `to_do_list` 文件夹上传到 GitHub 仓库
2. 登录 Render
3. 选择 `New +` -> `Blueprint`
4. 连接你的 GitHub 仓库
5. Render 会自动读取项目中的 `render.yaml`
6. 按提示创建服务

### 部署说明

- 使用 `gunicorn` 启动 Flask 应用
- 配置了 `/health` 健康检查接口
- 配置了持久化磁盘，用来保存 `todos.json`


## 依赖版本

- Flask
- gunicorn

## 备注

这是一个偏基础写法的小项目，适合学习 Flask 的表单提交、路由处理、JSON 持久化和简单部署流程。
