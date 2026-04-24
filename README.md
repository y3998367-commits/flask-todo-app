# 我的待办清单（准入式 + 可共享可独立）

这是一个用 **Python + Flask** 实现的待办事项网站。

这个版本已经改成：

- **每个 6 位准入码对应一份独立清单**
- **默认私有隔离**：只有创建该空间的当前设备可以再次进入
- **开启共享后**：知道同一个准入码的人，都可以查看并编辑同一份待办
- **不同准入码之间完全隔离**
- **数据保存在服务器端的 `todos.json` 中**，并按不同 `code` 分组存储
- **无需注册、无需登录**，只需要输入准入码即可进入

---

## 功能

- 输入 6 位准入码进入清单
- 生成新的独立空间
- 开启 / 关闭共享模式
- 复制准入码
- 退出当前空间
- 添加待办事项
- 标记任务完成
- 删除单条任务
- 一键清空全部任务
- 自动统计全部 / 已完成 / 未完成数量

---

## 使用规则

### 1）独立模式

点击“**生成新独立空间**”后，系统会生成一个随机 6 位准入码。

- 这个空间默认是 **私有** 的
- 只有创建该空间的 **当前浏览器设备** 能再次进入
- 其他人即使知道这个码，也不能进入

### 2）共享模式

如果创建者点击“**开启共享**”：

- 其他人只要输入同一个 6 位准入码
- 就能进入同一份待办清单
- 并且可以一起查看、添加、完成、删除任务

关闭共享后：

- 非创建者将无法再次进入该空间
- 创建者当前设备仍然可以继续访问

### 3）拥有者识别方式

因为本项目 **没有登录/注册系统**，所以“谁是空间创建者”是靠浏览器本地保存的 `owner_token` 来识别的。

这意味着：

- **私有模式不是账号体系**
- 它只是“创建该空间的那台浏览器设备有访问权”
- 如果你清空浏览器本地数据，可能会失去这个私有空间的拥有者身份

---

## 数据结构说明

待办数据保存在 `todos.json` 中，结构类似：

```json
{
  "spaces": {
    "123456": {
      "code": "123456",
      "owner_token": "...",
      "shared": false,
      "next_id": 3,
      "todos": [
        {
          "id": 1,
          "content": "完成作业",
          "completed": false
        }
      ],
      "created_at": "2026-04-24T00:00:00+00:00",
      "updated_at": "2026-04-24T00:00:00+00:00"
    }
  }
}
```

---

## 项目结构

```text
to_do_list/
├─ main.py
├─ templates/
│  └─ index.html
├─ todos.json
├─ requirements.txt
├─ render.yaml
└─ README.md
```

---

## 本地运行

### 1. 创建虚拟环境（可选）

Windows PowerShell：

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

或：

```powershell
py main.py
```

### 4. 打开网页

```text
http://127.0.0.1:5000/
```

---

## 部署到 Render，让别人也能访问

这个项目已经带有 `render.yaml`，适合部署到 **Render Web Service**。

### 第一步：把项目上传到 GitHub

如果你还没有把 `to_do_list` 这个项目放到 GitHub，可以执行：

```powershell
git add .
git commit -m "Update todo app to access-code sharing mode"
git branch -M main
git remote add origin <你的 GitHub 仓库地址>
git push -u origin main
```

> 建议把 `to_do_list` 作为一个独立仓库上传，这样 Render 会更省事。

### 第二步：在 Render 创建网站

1. 登录 Render
2. 选择 **New +**
3. 选择 **Blueprint**（如果使用 `render.yaml`）
4. 连接你的 GitHub 仓库
5. Render 会读取仓库中的 `render.yaml`
6. 按提示完成创建

部署成功后，Render 会给你一个公网网址，例如：

```text
https://your-app-name.onrender.com
```

把这个网址发给别人，别人就可以直接访问。

---

## 如何更新网站

如果你已经部署到 Render，后续更新网站通常就是：

### 方式一：推荐，改代码后推送到 GitHub

```powershell
git add .
git commit -m "Add copy code button and leave space button"
git push
```

只要你的 Render 服务连接的是这个 GitHub 仓库，通常会自动重新部署。

### 方式二：在 Render 后台手动重新部署

如果你已经把代码推上 GitHub，但想手动触发一次：

1. 打开 Render 后台
2. 进入你的 Web Service
3. 点击 **Manual Deploy**
4. 选择最新提交重新部署

---

## 非常重要：当前 `todos.json` 的线上持久化问题

现在这个项目把数据保存在文件 `todos.json` 中。

这在 **本地运行** 没问题；但如果你把它部署到云平台，必须注意：

- 如果平台的磁盘是**临时文件系统**，那么服务重启、重新部署后，`todos.json` 里的数据可能会丢失
- 所以如果你要长期给别人一起用，最好配置**持久化磁盘**，或者改成数据库

### 当前项目已支持自定义数据文件路径

`main.py` 支持读取环境变量：

```text
TODO_DATA_FILE
```

如果你在部署平台上挂载了持久化磁盘，可以把它设置成例如：

```text
TODO_DATA_FILE=/var/data/todos.json
```

这样应用就会把数据写到持久化目录，而不是项目源码目录。

---

## 给你一个适合“分享给别人一起使用”的建议

如果你只是想快速上线给同学/朋友用：

1. 上传到 GitHub
2. 部署到 Render
3. 配置持久化磁盘或稳定的数据目录
4. 把网站链接分享给别人
5. 之后每次改代码，`git push` 即可更新

如果你以后还想继续升级，下一步最值得做的是：

- 把 `todos.json` 改成 SQLite / PostgreSQL
- 增加“只读共享”或“可编辑共享”两种模式
- 增加空间备注名
- 增加复制邀请链接功能

---

## 技术说明

- 后端：Flask
- 前端：HTML + CSS + JavaScript
- 数据存储：`todos.json`
- 部署：Render（推荐）

---

## 备注

如果你以后想要：

- 用户跨设备仍能找回自己的私有清单
- 更强的身份识别
- 更安全的访问控制

那么就需要继续增加：

- 登录 / 注册系统
- 用户账号体系
- 数据库
- 更正式的权限模型

当前这个版本更适合：

- 小型分享使用
- 班级 / 宿舍 / 小组协作
- 无需注册即可快速进入同一待办空间
