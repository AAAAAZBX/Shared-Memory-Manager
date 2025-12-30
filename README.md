# 🔗 Shared Memory Manager

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 一个基于 Python 的跨网络共享内存管理工具，支持 GUI 界面和 TCP 协议通信

## ✨ 特性

- 🖥️ **图形化界面** - 友好的 GUI 界面，支持 Host 和 Client 模式切换
- 🌐 **跨网络访问** - 支持本地和远程访问，自动模式切换
- 🔒 **原子性操作** - 基于锁机制的原子性读写，保证数据一致性
- 🔄 **实时同步** - 输入框实时显示共享内存内容，自动同步更新
- 📡 **TCP 协议** - 跨网络时通过 TCP 协议通信，Host 在本地操作共享内存
- 🧩 **模块化设计** - 代码结构清晰，易于维护和扩展
- ⚡ **零依赖** - 仅使用 Python 标准库，无需安装第三方包

## 📋 目录

- [快速开始](#-快速开始)
- [功能特性](#-功能特性)
- [项目结构](#-项目结构)
- [技术实现](#-技术实现)
- [使用指南](#-使用指南)
- [技术要点](#-技术要点)
- [注意事项](#-注意事项)
- [问题描述](#-问题描述)

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Windows 操作系统

### 安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/shared-memory-manager.git
cd shared-memory-manager

# 无需安装依赖，直接运行即可
python GUI.py
```

> 💡 **提示**: 本项目仅使用 Python 标准库，无需安装任何第三方包

## 🎯 功能特性

### 本地访问模式

- Host 和 Client 在同一台机器上
- Client 直接访问共享内存，性能最优
- 支持实时同步和自动刷新

### 远程访问模式

- Host 和 Client 在不同机器上
- 通过 TCP 协议进行通信
- 自动检测并切换模式
- 支持跨网络数据同步

### 核心功能

- ✅ 共享内存创建和管理
- ✅ 原子性读写操作
- ✅ 自动锁机制（写入时上锁，完成后立即释放）
- ✅ 实时内容同步
- ✅ 网络连接管理
- ✅ 错误处理和超时机制

## 📁 项目结构

```
Shared_Memory/
├── GUI.py                    # GUI 主程序（界面和交互逻辑）
├── shared_memory_utils.py    # 共享内存工具模块（底层操作）
├── requirements.txt          # 依赖说明（仅标准库）
├── README.md                 # 项目文档
├── .gitignore               # Git 忽略配置
└── GITHUB_SETUP.md          # GitHub 上传指南
```

### 模块说明

- **`GUI.py`**: 图形界面主程序
  - `SharedMemoryGUI` 类：主界面和事件处理
  - Host 和 Client 模式管理
  - 网络连接和自动刷新

- **`shared_memory_utils.py`**: 工具模块
  - `SharedMemoryLock` 类：锁机制实现
  - `shm_write()`: 原子性写入函数
  - `shm_read()`: 读取共享内存函数
  - `get_local_ip()`: 获取本机 IP 地址

## 🔧 技术实现

### 共享内存布局

本实现采用以下内存布局（总大小 4096 字节）：

```
偏移量    大小    内容
─────────────────────────────────────
0         1       lock_flag    (锁标志: 0=空闲, 1=占用)
1-4       4       str_len  (字符串长度，uint32，小端序)
5-4095    4091    data     (UTF-8 编码的字符串数据)
```

**关键常量**：
- `LOCK_SIZE = 1`: 锁标志占用 1 字节
- `LEN_SIZE = 4`: 长度字段占用 4 字节
- `DATA_OFFSET = 5`: 数据起始偏移
- `BUF_SIZE = 4096`: 共享内存总大小
- `MAX_DATA_SIZE = 4091`: 最大数据长度

### 锁机制

采用整块锁机制，保证读写操作的原子性：

- **锁位置**: 共享内存的第一个字节（偏移 0）
- **锁状态**: 
  - `LOCK_FREE = 0`: 锁空闲
  - `LOCK_HELD = 1`: 锁被占用
- **特性**:
  - 写入时自动上锁，完成后立即释放
  - 支持超时机制（默认 5 秒）
  - 原子性检查，防止竞争条件

```python
# 使用示例
from shared_memory_utils import SharedMemoryLock, shm_write, shm_read

lock = SharedMemoryLock(shm, lock_offset=0)
# 写入时自动上锁
shm_write(shm, text, lock)
# 读取时自动上锁
content = shm_read(shm, lock)
```

### 网络通信协议

#### 本地模式

- Client 直接访问共享内存
- 无需网络传输，性能最优

#### 远程模式（TCP 协议）

**READ 命令**（读取共享内存内容）
```
Client → Host: READ\n
Host → Client: OK <content>\n 或 ERROR <message>\n
```

**WRITE 命令**（写入共享内存内容）
```
Client → Host: WRITE <length>\n<content>\n
Host → Client: OK\n 或 ERROR <message>\n
```

## 📖 使用指南

### 基本使用流程

#### 1️⃣ 启动 Host

1. 运行程序：`python GUI.py`
2. 选择 **"Host（主机）"** 模式
3. 点击 **"启动 Host"** 按钮
4. 记录显示的连接信息：
   - 本机 IP
   - 端口号
   - 共享内存 ID

#### 2️⃣ 启动 Client

1. 运行程序：`python GUI.py`（可在同一台或另一台机器上）
2. 选择 **"Client（客户端）"** 模式
3. 输入连接信息：
   - Host IP（本地访问可使用 `127.0.0.1`）
   - 端口号
   - 共享内存 ID
4. 点击 **"连接 Host"** 按钮
5. 连接成功后，输入框会自动显示共享内存内容

#### 3️⃣ 读写操作

**读取**：
- 输入框会自动同步显示共享内存内容
- 每 500ms 自动刷新一次
- 无需手动操作

**写入**：
1. 在输入框中编辑内容（最大 4091 字节）
2. 点击 **"写入共享内存"** 按钮
3. 系统自动上锁 → 写入 → 释放锁
4. 内容自动同步到对方主机

### 使用场景

#### 场景 1: 本地访问（同一台机器）

```bash
# 终端 1: 启动 Host
python GUI.py
# 选择 Host 模式，点击启动

# 终端 2: 启动 Client
python GUI.py
# 选择 Client 模式，输入 127.0.0.1 和端口号
```

#### 场景 2: 跨网络访问（不同机器）

```bash
# 远程机器: 启动 Host
python GUI.py
# 记录显示的 IP、端口和 shm_id

# 本地机器: 启动 Client
python GUI.py
# 输入远程机器的 IP、端口和 shm_id
```

## 💡 技术要点

| 特性           | 说明                                         |
| -------------- | -------------------------------------------- |
| **内存布局**   | 锁标志(1字节) + 长度(4字节) + 数据(剩余空间) |
| **锁机制**     | 整块锁，写入时自动上锁，完成后立即释放       |
| **原子性**     | 所有写操作在锁保护下执行，保证原子性         |
| **网络容错**   | 支持超时机制，处理网络抖动                   |
| **跨进程通信** | 使用 `multiprocessing.shared_memory` 实现    |
| **协议设计**   | 基于 TCP 的简单文本协议，易于调试            |
| **跨网络支持** | 自动检测本地/远程模式，智能切换              |
| **模块化设计** | GUI 和工具模块分离，便于维护                 |
| **实时同步**   | 输入框实时显示，自动覆盖更新                 |

## ⚠️ 注意事项

### 系统要求

- ✅ Python 3.8+（`multiprocessing.shared_memory` 需要 Python 3.8+）
- ✅ Windows 操作系统（已在 Windows 上测试通过）
- ✅ 网络互通（跨网络访问时）

### 使用限制

- 📝 **数据长度**: 最大 4091 字节（4096 - 5）
- 🔒 **锁超时**: 默认 5 秒，超时后抛出异常
- 🌐 **网络**: 跨网络访问需要防火墙允许 TCP 连接
- 📂 **文件依赖**: `GUI.py` 和 `shared_memory_utils.py` 必须在同一目录

### 常见问题

<details>
<summary><b>Q: 连接超时怎么办？</b></summary>

- 检查 Host IP 和端口是否正确
- 确认 Host 程序已启动
- 检查防火墙设置
- 尝试使用 `127.0.0.1` 进行本地测试
</details>

<details>
<summary><b>Q: 共享内存 ID 不匹配？</b></summary>

- 确保输入的 shm_id 与 Host 显示的完全一致
- 检查是否有空格或特殊字符
- 重新启动 Host 获取新的 shm_id
</details>

<details>
<summary><b>Q: 写入时出现大量空格？</b></summary>

- 已修复：系统会自动移除文本末尾的空白字符
- 确保使用最新版本的代码
</details>

## 📚 问题描述

### 项目背景

本项目旨在实现一个跨网络的共享内存管理系统，解决以下技术难点：

#### 1. 内存不稳定问题

**问题**：
- 内存生命周期管理
- 重启/崩溃后内存编号映射恢复
- 内存换入/换出，位置不固定

**解决方案**：
- 使用 `multiprocessing.shared_memory` 管理内存生命周期
- 通过 shm_id 进行内存映射
- 内存位置由操作系统管理

#### 2. 并发读写一致性

**问题**：
- 多个客户端同时读写时的数据一致性
- 需要锁机制保证原子性
- 锁粒度选择（整块锁 vs 分段锁）

**解决方案**：
- 实现整块锁机制（简单高效）
- 写入时自动上锁，完成后立即释放
- 支持超时机制，避免死锁

#### 3. 网络抖动问题

**问题**：
- 网络断线、重连、超时
- 重复写操作的原子性保证

**解决方案**：
- TCP 协议保证可靠传输
- 超时机制处理网络延迟
- 锁机制保证写操作的原子性

### 技术细节

#### 内存映射

基本思路：协议内的内存地址定位只能依靠共享内存编号 `shm_id`，主机内部通过映射表 `shm_id -> (base, size)` 得到内存位置和大小。外部主机不能直接获取主机内部的 `(base, size)`，因为内存可能因为换入换出导致起始地址改变。

**内存信息**：
- `shm_id`: 外部看到的共享内存编号
- `base`: 区域在主机进程内的起始地址（仅主机内部用）
- `size`: 区域大小（字节数）
- `layout`: 布局（UTF8_STRING）
- `version`: 变更版本号（可选）
- `lock_state`: 锁状态（可选）

#### TCP 连接流程

```
Client 连接 HOST_IP:PORT
  ↓
Host → Client: 发送元数据（shm_id, size, offsets...）
  ↓
Client 验证 shm_id
  ↓
[本地模式] Client 直接访问共享内存
[远程模式] Client 通过 TCP 协议与 Host 通信
  ↓
Client → Host: READ/WRITE 命令
  ↓
Host 操作本地共享内存并返回结果
```

---

## 📄 License

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

Made with ❤️ by [Your Name]

</div>
