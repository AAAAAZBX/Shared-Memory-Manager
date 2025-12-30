# GitHub 仓库上传指南

## 一、项目名称建议

当前项目名称：`Shared_Memory`

### 推荐名称（按优先级）：

1. **`shared-memory-manager`** - 共享内存管理器（推荐）
   - 清晰描述项目功能
   - 使用连字符，符合 GitHub 命名规范

2. **`shared-memory-tool`** - 共享内存工具
   - 简洁明了

3. **`cross-network-shared-memory`** - 跨网络共享内存
   - 强调跨网络功能

4. **`shm-manager`** - 共享内存管理器（缩写）
   - 简短易记

5. **`network-shared-memory`** - 网络共享内存
   - 强调网络特性

## 二、GitHub 上传步骤

### 方法 1: 使用 Git 命令行（推荐）

#### 步骤 1: 初始化 Git 仓库

```bash
# 在项目目录下执行
cd D:\Q\demo\Shared_Memory
git init
```

#### 步骤 2: 添加文件

```bash
# 添加所有文件
git add .

# 或者选择性添加
git add GUI.py
git add shared_memory_utils.py
git add README.md
git add requirements.txt
git add .gitignore
```

#### 步骤 3: 提交代码

```bash
git commit -m "Initial commit: 共享内存管理工具"
```

#### 步骤 4: 在 GitHub 上创建仓库

1. 登录 GitHub (https://github.com)
2. 点击右上角的 "+" 号，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `shared-memory-manager`（或你选择的其他名称）
   - **Description**: `跨网络共享内存管理工具，支持 GUI 界面和 TCP 协议通信`
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - **不要**勾选 "Initialize this repository with a README"（因为本地已有）
4. 点击 "Create repository"

#### 步骤 5: 连接远程仓库并推送

```bash
# 添加远程仓库（将 YOUR_USERNAME 替换为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/shared-memory-manager.git

# 或者使用 SSH（如果已配置 SSH key）
# git remote add origin git@github.com:YOUR_USERNAME/shared-memory-manager.git

# 推送代码到 GitHub
git branch -M main
git push -u origin main
```

### 方法 2: 使用 GitHub Desktop（图形界面）

1. 下载安装 GitHub Desktop: https://desktop.github.com/
2. 登录 GitHub 账号
3. 点击 "File" -> "Add Local Repository"
4. 选择项目目录：`D:\Q\demo\Shared_Memory`
5. 点击 "Publish repository"
6. 填写仓库名称和描述
7. 点击 "Publish Repository"

### 方法 3: 使用 GitHub Web 界面

1. 在 GitHub 上创建新仓库
2. 使用 GitHub 提供的上传文件功能
3. 拖拽项目文件到网页上

## 三、后续更新代码

### 提交更改

```bash
# 查看更改状态
git status

# 添加更改的文件
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到 GitHub
git push
```

## 四、仓库设置建议

### 1. 添加仓库描述

在 GitHub 仓库页面，点击 "Settings" -> 在 "Repository name" 下方添加描述：
```
跨网络共享内存管理工具，支持 GUI 界面和 TCP 协议通信
```

### 2. 添加 Topics（标签）

在仓库页面点击 ⚙️ 图标，添加以下标签：
- `python`
- `shared-memory`
- `gui`
- `tcp`
- `network-communication`
- `multiprocessing`

### 3. 添加 README 徽章（可选）

可以在 README.md 顶部添加徽章，例如：

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
```

## 五、常见问题

### Q: 如何更改远程仓库地址？

```bash
# 查看当前远程地址
git remote -v

# 更改远程地址
git remote set-url origin https://github.com/YOUR_USERNAME/NEW_REPO_NAME.git
```

### Q: 如何忽略已提交的文件？

如果 `__pycache__` 等文件已经被提交，需要：

```bash
# 从 Git 中移除但保留本地文件
git rm -r --cached __pycache__

# 提交更改
git commit -m "Remove __pycache__ from repository"

# 推送到 GitHub
git push
```

### Q: 如何创建 Release？

1. 在 GitHub 仓库页面，点击 "Releases"
2. 点击 "Create a new release"
3. 填写版本号（如 v1.0.0）和发布说明
4. 点击 "Publish release"

