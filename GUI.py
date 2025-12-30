"""共享内存管理工具 - GUI 主程序"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import time
import threading
from multiprocessing import shared_memory

# 从工具模块导入共享内存相关功能
from shared_memory_utils import (
    BUF_SIZE, DATA_OFFSET, MAX_DATA_SIZE, SYNC_UPDATE_CMD,
    LOCK_FREE, LOCK_HELD,
    get_local_ip, SharedMemoryLock, shm_write, shm_read
)


class SharedMemoryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("共享内存管理工具")
        self.root.geometry("800x700")
        
        # 状态变量
        self.mode = tk.StringVar(value="host")
        self.shm = None
        self.lock = None
        self.server_socket = None
        self.client_socket = None
        self.is_locked = False
        self.auto_refresh_running = False
        self.last_content = ""  # 用于检测内容变化
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 模式选择
        mode_frame = ttk.LabelFrame(self.root, text="选择身份", padding=10)
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Host（主机）", variable=self.mode, 
                       value="host", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Client（客户端）", variable=self.mode, 
                       value="client", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        
        # Host 模式界面
        self.host_frame = ttk.LabelFrame(self.root, text="Host 模式", padding=10)
        self.create_host_widgets()
        
        # Client 模式界面
        self.client_frame = ttk.LabelFrame(self.root, text="Client 模式", padding=10)
        self.create_client_widgets()
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 初始显示
        self.on_mode_change()
        
        # 初始化时显示本机 IP
        local_ip = get_local_ip()
        self.host_ip_var.set(f"{local_ip} (启动后可通过此 IP 访问)")
        
    def create_host_widgets(self):
        # Host IP 显示（本机实际 IP）
        ttk.Label(self.host_frame, text="Host IP (本机):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.host_ip_var = tk.StringVar()
        self.host_ip_label = ttk.Label(self.host_frame, textvariable=self.host_ip_var, 
                                      font=("Arial", 10, "bold"))
        self.host_ip_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 本地回环地址显示
        ttk.Label(self.host_frame, text="Localhost:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(self.host_frame, text="127.0.0.1", 
                 font=("Arial", 10)).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Port 显示
        ttk.Label(self.host_frame, text="端口 (Port):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.host_port_var = tk.StringVar(value="未启动")
        ttk.Label(self.host_frame, textvariable=self.host_port_var, 
                 font=("Arial", 10, "bold")).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # SHM ID 显示
        ttk.Label(self.host_frame, text="共享内存 ID (shm_id):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.host_shm_id_var = tk.StringVar(value="未创建")
        ttk.Label(self.host_frame, textvariable=self.host_shm_id_var, 
                 font=("Arial", 10, "bold")).grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # 启动/停止按钮
        self.host_start_btn = ttk.Button(self.host_frame, text="启动 Host", 
                                        command=self.start_host)
        self.host_start_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.host_stop_btn = ttk.Button(self.host_frame, text="停止 Host", 
                                       command=self.stop_host, state=tk.DISABLED)
        self.host_stop_btn.grid(row=5, column=0, columnspan=2, pady=5)
        
        # 共享内存内容显示和编辑区域
        ttk.Label(self.host_frame, text=f"共享内存中的内容 (最大 {MAX_DATA_SIZE} bytes):").grid(
            row=6, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        self.host_text = scrolledtext.ScrolledText(self.host_frame, height=15, width=70)
        self.host_text.grid(row=7, column=0, columnspan=2, pady=5)
        self.host_text.bind('<KeyRelease>', self.on_host_text_change)
        self.host_text_editing = False  # 标记是否正在编辑
        
        # 字符计数
        self.host_count_var = tk.StringVar(value="0 / 4091 bytes")
        ttk.Label(self.host_frame, textvariable=self.host_count_var).grid(
            row=8, column=0, columnspan=2, sticky=tk.W)
        
        # 写入按钮
        self.host_write_btn = ttk.Button(self.host_frame, text="写入共享内存", 
                                        command=self.host_write, state=tk.DISABLED)
        self.host_write_btn.grid(row=9, column=0, columnspan=2, pady=10)
        
        # 锁状态显示
        self.host_lock_var = tk.StringVar(value="锁状态: 空闲")
        ttk.Label(self.host_frame, textvariable=self.host_lock_var, 
                 foreground="green").grid(row=10, column=0, columnspan=2, pady=5)
        
    def create_client_widgets(self):
        # Host IP 输入
        ttk.Label(self.client_frame, text="Host IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.client_ip_entry = ttk.Entry(self.client_frame, width=20)
        self.client_ip_entry.insert(0, "127.0.0.1")
        self.client_ip_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Port 输入
        ttk.Label(self.client_frame, text="端口 (Port):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.client_port_entry = ttk.Entry(self.client_frame, width=20)
        self.client_port_entry.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # SHM ID 输入
        ttk.Label(self.client_frame, text="共享内存 ID (shm_id):").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        self.client_shm_id_entry = ttk.Entry(self.client_frame, width=30)
        self.client_shm_id_entry.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # 连接按钮
        self.client_connect_btn = ttk.Button(self.client_frame, text="连接 Host", 
                                             command=self.client_connect)
        self.client_connect_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.client_disconnect_btn = ttk.Button(self.client_frame, text="断开连接", 
                                                command=self.client_disconnect, state=tk.DISABLED)
        self.client_disconnect_btn.grid(row=4, column=0, columnspan=2, pady=5)
        
        # 共享内存内容显示和编辑区域
        ttk.Label(self.client_frame, text=f"共享内存中的内容 (最大 {MAX_DATA_SIZE} bytes):").grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        self.client_text = scrolledtext.ScrolledText(self.client_frame, height=15, width=70)
        self.client_text.grid(row=6, column=0, columnspan=2, pady=5)
        self.client_text.bind('<KeyRelease>', self.on_client_text_change)
        self.client_text_editing = False  # 标记是否正在编辑
        
        # 字符计数
        self.client_count_var = tk.StringVar(value="0 / 4091 bytes")
        ttk.Label(self.client_frame, textvariable=self.client_count_var).grid(
            row=7, column=0, columnspan=2, sticky=tk.W)
        
        # 写入按钮
        self.client_write_btn = ttk.Button(self.client_frame, text="写入共享内存", 
                                          command=self.client_write, state=tk.DISABLED)
        self.client_write_btn.grid(row=8, column=0, columnspan=2, pady=10)
        
        # 锁状态显示
        self.client_lock_var = tk.StringVar(value="锁状态: 未连接")
        ttk.Label(self.client_frame, textvariable=self.client_lock_var).grid(
            row=9, column=0, columnspan=2, pady=5)
        
    def on_mode_change(self):
        """切换模式"""
        if self.mode.get() == "host":
            self.host_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.client_frame.pack_forget()
        else:
            self.client_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.host_frame.pack_forget()
        self.status_var.set("就绪")
        
    def on_host_text_change(self, event=None):
        """Host 文本输入变化"""
        self.host_text_editing = True
        text = self.host_text.get("1.0", tk.END).rstrip('\n')
        byte_count = len(text.encode("utf-8"))
        self.host_count_var.set(f"{byte_count} / {MAX_DATA_SIZE} bytes")
        
        # 如果超过限制，禁用写入按钮
        if byte_count > MAX_DATA_SIZE:
            self.host_write_btn.config(state=tk.DISABLED)
            self.host_count_var.set(f"{byte_count} / {MAX_DATA_SIZE} bytes (超出限制!)")
        elif self.shm is not None:
            self.host_write_btn.config(state=tk.NORMAL)
        
        # 延迟重置编辑标志，避免频繁更新
        self.root.after(100, lambda: setattr(self, 'host_text_editing', False))
            
    def on_client_text_change(self, event=None):
        """Client 文本输入变化"""
        self.client_text_editing = True
        text = self.client_text.get("1.0", tk.END).rstrip('\n')
        byte_count = len(text.encode("utf-8"))
        self.client_count_var.set(f"{byte_count} / {MAX_DATA_SIZE} bytes")
        
        # 如果超过限制，禁用写入按钮
        if byte_count > MAX_DATA_SIZE:
            self.client_write_btn.config(state=tk.DISABLED)
            self.client_count_var.set(f"{byte_count} / {MAX_DATA_SIZE} bytes (超出限制!)")
        elif self.shm is not None:
            self.client_write_btn.config(state=tk.NORMAL)
        
        # 延迟重置编辑标志，避免频繁更新
        self.root.after(100, lambda: setattr(self, 'client_text_editing', False))
            
    def start_host(self):
        """启动 Host"""
        try:
            # 创建共享内存
            self.shm = shared_memory.SharedMemory(create=True, size=BUF_SIZE)
            self.shm.buf[0] = LOCK_FREE
            
            self.lock = SharedMemoryLock(self.shm)
            
            # 创建服务器 socket，绑定到 0.0.0.0（监听所有接口）
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", 0))  # 绑定到所有接口
            self.server_socket.listen(1)
            host, port = self.server_socket.getsockname()
            
            # 获取本机实际 IP
            local_ip = get_local_ip()
            
            # 更新界面
            self.host_ip_var.set(f"{local_ip} (可通过此 IP 访问)")
            self.host_port_var.set(str(port))
            self.host_shm_id_var.set(self.shm.name)
            self.host_start_btn.config(state=tk.DISABLED)
            self.host_stop_btn.config(state=tk.NORMAL)
            self.host_write_btn.config(state=tk.NORMAL)
            
            # 启动监听线程
            threading.Thread(target=self.host_listen, daemon=True).start()
            
            # 初始化输入框内容
            try:
                initial_text = shm_read(self.shm, self.lock, DATA_OFFSET)
                self.host_text.delete("1.0", tk.END)
                self.host_text.insert("1.0", initial_text)
                self.last_content = initial_text
                byte_count = len(initial_text.encode("utf-8"))
                self.host_count_var.set(f"{byte_count} / {MAX_DATA_SIZE} bytes")
            except:
                pass
            
            # 启动自动刷新
            self.start_auto_refresh()
            
            self.status_var.set(f"Host 已启动 - IP: {local_ip}, 端口: {port}, SHM ID: {self.shm.name}")
            messagebox.showinfo("成功", 
                              f"Host 启动成功！\n\n"
                              f"本机 IP: {local_ip}\n"
                              f"本地访问: 127.0.0.1\n"
                              f"端口: {port}\n"
                              f"共享内存 ID: {self.shm.name}\n\n"
                              f"Client 可通过 {local_ip}:{port} 或 127.0.0.1:{port} 连接")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动 Host 失败: {e}")
            self.status_var.set(f"错误: {e}")
            
    def host_listen(self):
        """Host 监听客户端连接（后台线程）"""
        try:
            while self.server_socket:
                conn, addr = self.server_socket.accept()
                # 为每个连接创建新线程处理
                threading.Thread(target=self.handle_client_connection, 
                               args=(conn, addr), daemon=True).start()
        except Exception as e:
            if self.server_socket:
                self.root.after(0, lambda: self.status_var.set(f"监听错误: {e}"))
    
    def handle_client_connection(self, conn, addr):
        """处理客户端连接"""
        try:
            with conn:
                # 检查共享内存是否已创建
                if not self.shm:
                    error_msg = "错误：共享内存未创建，无法发送元数据"
                    self.root.after(0, lambda: self.status_var.set(error_msg))
                    return
                
                # 发送元数据
                meta = f"{self.shm.name} {BUF_SIZE} 0 {BUF_SIZE-1} 0 {DATA_OFFSET}\n"
                try:
                    conn.sendall(meta.encode("utf-8"))
                    self.root.after(0, lambda: self.status_var.set(f"客户端已连接: {addr}"))
                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set(f"发送元数据失败: {e}"))
                    return
                
                # 持续监听客户端消息（支持远程读写协议）
                while True:
                    try:
                        data = conn.recv(1024)
                        if not data:
                            break
                        msg = data.decode("utf-8", errors="replace")
                        
                        # 处理READ命令
                        if msg.strip() == "READ":
                            # 读取共享内存内容并返回
                            try:
                                content = shm_read(self.shm, self.lock, DATA_OFFSET)
                                response = f"OK {content}\n".encode("utf-8")
                                conn.sendall(response)
                            except Exception as e:
                                error_response = f"ERROR {str(e)}\n".encode("utf-8")
                                conn.sendall(error_response)
                        
                        # 处理WRITE命令: "WRITE <length>\n<content>\n"
                        elif msg.startswith("WRITE "):
                            try:
                                # 解析第一行获取长度
                                first_line_end = msg.find("\n")
                                if first_line_end == -1:
                                    # 还没收到完整的第一行，继续接收
                                    continue
                                
                                length_str = msg[6:first_line_end].strip()  # 跳过"WRITE "
                                length = int(length_str)
                                
                                # 计算还需要接收的字节数（内容 + 最后的\n）
                                content_start = first_line_end + 1
                                received_content_len = len(msg) - content_start
                                remaining = length + 1 - received_content_len  # +1 for final \n
                                
                                # 如果内容不完整，继续接收
                                if remaining > 0:
                                    content_data = b""
                                    while len(content_data) < remaining:
                                        chunk = conn.recv(remaining - len(content_data))
                                        if not chunk:
                                            raise RuntimeError("连接中断")
                                        content_data += chunk
                                    msg += content_data.decode("utf-8", errors="replace")
                                
                                # 提取内容（跳过第一行和最后的\n）
                                content = msg[content_start:content_start+length]
                                
                                # 写入共享内存
                                shm_write(self.shm, content, self.lock)
                                
                                # 发送确认
                                conn.sendall(b"OK\n")
                                
                                # 触发自动刷新
                                self.root.after(0, self.host_auto_refresh)
                                self.root.after(0, lambda: self.status_var.set(f"客户端已更新: {addr}"))
                            except Exception as e:
                                error_response = f"ERROR {str(e)}\n".encode("utf-8")
                                conn.sendall(error_response)
                        
                        # 兼容旧协议
                        elif msg.strip() == "DONE":
                            # 客户端写入完成，触发自动刷新
                            self.root.after(0, self.host_auto_refresh)
                            self.root.after(0, lambda: self.status_var.set(f"客户端已更新: {addr}"))
                        elif msg.strip() == SYNC_UPDATE_CMD:
                            # 客户端请求同步更新
                            self.root.after(0, self.host_auto_refresh)
                    except socket.timeout:
                        # 接收超时，继续等待
                        continue
                    except Exception as e:
                        # 接收错误，断开连接
                        break
        except Exception as e:
            if self.server_socket:
                self.root.after(0, lambda: self.status_var.set(f"连接错误: {e}"))
                
    def stop_host(self):
        """停止 Host"""
        try:
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
                
            if self.shm:
                try:
                    self.shm.close()
                finally:
                    self.shm.unlink()
                self.shm = None
                self.lock = None
                
            # 更新界面
            self.host_ip_var.set("未启动")
            self.host_port_var.set("未启动")
            self.host_shm_id_var.set("未创建")
            self.host_start_btn.config(state=tk.NORMAL)
            self.host_stop_btn.config(state=tk.DISABLED)
            self.host_write_btn.config(state=tk.DISABLED)
            self.host_lock_var.set("锁状态: 空闲")
            
            # 停止自动刷新
            self.stop_auto_refresh()
            
            self.status_var.set("Host 已停止")
            messagebox.showinfo("成功", "Host 已停止")
            
        except Exception as e:
            messagebox.showerror("错误", f"停止 Host 失败: {e}")
            
    def host_write(self):
        """Host 写入共享内存（写入时上锁，完成后立即释放）"""
        if not self.shm:
            messagebox.showwarning("警告", "共享内存未创建")
            return
            
        text = self.host_text.get("1.0", tk.END).rstrip('\n')
        byte_count = len(text.encode("utf-8"))
        
        if byte_count > MAX_DATA_SIZE:
            messagebox.showerror("错误", f"文本太长: {byte_count} > {MAX_DATA_SIZE} bytes")
            return
            
        try:
            # 写入时自动上锁（对用户透明），写入完成后立即释放
            self.host_lock_var.set("锁状态: 写入中...")
            self.host_write_btn.config(state=tk.DISABLED)
            
            # 写入数据（内部会获取和释放锁）
            shm_write(self.shm, text, self.lock)
            
            # 写入完成，立即更新状态
            self.host_lock_var.set("锁状态: 空闲")
            self.host_write_btn.config(state=tk.NORMAL)
            self.is_locked = False
            
            # 更新last_content，避免立即被覆盖
            self.last_content = text
            
            # 通知已连接的客户端更新
            self.notify_clients_update()
            
            self.status_var.set("写入成功，已同步")
            messagebox.showinfo("成功", "写入成功！内容已同步")
            
        except TimeoutError as e:
            self.host_lock_var.set("锁状态: 空闲")
            self.host_write_btn.config(state=tk.NORMAL)
            self.is_locked = False
            messagebox.showerror("错误", f"获取锁失败: {e}")
        except Exception as e:
            self.host_lock_var.set("锁状态: 空闲")
            self.host_write_btn.config(state=tk.NORMAL)
            self.is_locked = False
            messagebox.showerror("错误", f"写入失败: {e}")
    
    def host_auto_refresh(self):
        """Host 自动刷新共享内存内容到输入框（即使正在编辑也会被覆盖）"""
        if not self.shm or not self.lock:
            return
        try:
            text = shm_read(self.shm, self.lock, DATA_OFFSET)
            if text != self.last_content:
                # 直接覆盖输入框内容，即使正在编辑
                current_pos = self.host_text.index(tk.INSERT)
                self.host_text.delete("1.0", tk.END)
                self.host_text.insert("1.0", text)
                # 尝试恢复光标位置（如果可能）
                try:
                    self.host_text.mark_set(tk.INSERT, current_pos)
                except:
                    pass
                self.last_content = text
                # 更新字符计数
                byte_count = len(text.encode("utf-8"))
                self.host_count_var.set(f"{byte_count} / {MAX_DATA_SIZE} bytes")
        except Exception as e:
            pass  # 静默失败，避免频繁弹窗
    
    def notify_clients_update(self):
        """通知已连接的客户端进行更新（通过共享内存变化，客户端会检测到）"""
        # 由于共享内存是共享的，客户端可以通过轮询检测到变化
        # 这里可以发送TCP通知（如果需要实时性）
        pass
            
            
    def client_connect(self):
        """Client 连接 Host"""
        try:
            host_ip = self.client_ip_entry.get().strip()
            port_str = self.client_port_entry.get().strip()
            shm_id = self.client_shm_id_entry.get().strip()
            
            if not host_ip or not port_str or not shm_id:
                messagebox.showerror("错误", "请填写完整的连接信息")
                return
                
            try:
                port = int(port_str)
            except ValueError:
                raise ValueError(f"端口号格式错误: '{port_str}'，请输入数字")
            
            # 连接服务器
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10.0)
            
            # 更新状态显示连接尝试
            self.status_var.set(f"正在连接到 {host_ip}:{port}...")
            
            try:
                self.client_socket.connect((host_ip, port))
            except socket.timeout:
                self.client_socket.close()
                self.client_socket = None
                raise RuntimeError(
                    f"连接超时！\n"
                    f"无法连接到 {host_ip}:{port}\n\n"
                    f"请检查：\n"
                    f"1. Host IP 是否正确：{host_ip}\n"
                    f"2. 端口号是否正确：{port}\n"
                    f"3. Host 程序是否已启动\n"
                    f"4. 防火墙是否阻止了连接"
                )
            except ConnectionRefusedError:
                self.client_socket.close()
                self.client_socket = None
                raise RuntimeError(
                    f"连接被拒绝！\n"
                    f"无法连接到 {host_ip}:{port}\n\n"
                    f"请确认：\n"
                    f"1. Host 程序是否已启动\n"
                    f"2. 端口号是否正确：{port}"
                )
            except OSError as e:
                self.client_socket.close()
                self.client_socket = None
                raise RuntimeError(
                    f"连接失败：{e}\n\n"
                    f"请检查网络连接和 Host 状态。"
                )
            
            # 接收元数据（带超时保护）
            self.status_var.set(f"正在接收元数据...")
            meta = b""
            start_time = time.time()
            try:
                while not meta.endswith(b"\n"):
                    # 检查是否超时（给一个合理的超时时间）
                    if time.time() - start_time > 15.0:
                        raise socket.timeout("接收元数据超时")
                    chunk = self.client_socket.recv(1024)
                    if not chunk:
                        raise RuntimeError("服务器关闭连接，未收到完整元数据")
                    meta += chunk
            except socket.timeout:
                self.client_socket.close()
                self.client_socket = None
                raise RuntimeError(
                    f"接收数据超时！\n"
                    f"服务器未及时响应。\n\n"
                    f"可能的原因：\n"
                    f"1. Host 程序未正确启动\n"
                    f"2. 网络延迟过大\n"
                    f"3. Host 程序崩溃或卡住\n"
                    f"4. 防火墙阻止了数据传输\n\n"
                    f"请检查 Host 程序状态，并重试。"
                )
                
            parts = meta.decode("utf-8").strip().split()
            if len(parts) == 6:
                name, size, start, end, lock_offset, data_offset = parts
                lock_offset = int(lock_offset)
                data_offset = int(data_offset)
            else:
                raise ValueError("无效的元数据格式")
            
            # 验证用户输入的 shm_id 是否与服务器返回的一致
            if name != shm_id:
                self.client_socket.close()
                self.client_socket = None
                raise ValueError(
                    f"共享内存 ID 不匹配！\n"
                    f"您输入的: {shm_id}\n"
                    f"服务器实际的: {name}\n"
                    f"请使用正确的共享内存 ID 重新连接。"
                )
            
            # 跨网络模式：不直接访问共享内存，而是通过TCP协议通信
            # 保存连接信息，不创建本地共享内存对象
            self.remote_shm_id = name
            self.shm = None  # 跨网络时不使用本地共享内存
            self.lock = None
            
            # 更新界面
            self.client_connect_btn.config(state=tk.DISABLED)
            self.client_disconnect_btn.config(state=tk.NORMAL)
            self.client_write_btn.config(state=tk.NORMAL)
            self.client_lock_var.set("锁状态: 空闲（远程模式）")
            
            # 通过TCP读取初始内容
            try:
                initial_text = self.client_read_remote()
                self.client_text.delete("1.0", tk.END)
                self.client_text.insert("1.0", initial_text)
                self.last_content = initial_text
                byte_count = len(initial_text.encode("utf-8"))
                self.client_count_var.set(f"{byte_count} / {MAX_DATA_SIZE} bytes")
            except Exception as e:
                # 如果读取失败，显示空内容
                self.client_text.delete("1.0", tk.END)
                self.last_content = ""
            
            # 启动自动刷新
            self.start_auto_refresh()
            
            self.status_var.set(f"已连接到 {host_ip}:{port} (远程模式)")
            messagebox.showinfo("成功", 
                              f"连接成功！\n\n"
                              f"共享内存 ID: {name}\n"
                              f"模式: 远程访问（通过TCP）\n\n"
                              f"注意：跨网络访问时，数据通过TCP传输。")
            
        except socket.timeout as e:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
            error_msg = (
                f"连接超时！\n\n"
                f"无法连接到 {host_ip}:{port}\n\n"
                f"请检查：\n"
                f"1. Host IP 是否正确：{host_ip}\n"
                f"2. 端口号是否正确：{port}\n"
                f"3. Host 程序是否已启动并显示端口号\n"
                f"4. 防火墙是否阻止了连接\n"
                f"5. 如果使用本机 IP，请确认 IP 地址正确\n"
                f"6. 可以尝试使用 127.0.0.1 代替本机 IP"
            )
            messagebox.showerror("连接超时", error_msg)
            self.status_var.set(f"连接超时 - {host_ip}:{port}")
        except Exception as e:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
            error_msg = str(e)
            # 如果错误信息已经包含详细说明，直接显示
            if "\n" in error_msg or len(error_msg) > 50:
                messagebox.showerror("连接失败", error_msg)
            else:
                messagebox.showerror("连接失败", 
                    f"连接失败: {error_msg}\n\n"
                    f"请检查：\n"
                    f"1. Host IP: {self.client_ip_entry.get()}\n"
                    f"2. 端口: {self.client_port_entry.get()}\n"
                    f"3. 共享内存 ID: {self.client_shm_id_entry.get()}\n"
                    f"4. Host 程序是否已启动")
            self.status_var.set(f"连接失败: {error_msg}")
            
    def client_disconnect(self):
        """Client 断开连接"""
        try:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
                
            if self.shm:
                self.shm.close()
                self.shm = None
                self.lock = None
                
            # 更新界面
            self.client_connect_btn.config(state=tk.NORMAL)
            self.client_disconnect_btn.config(state=tk.DISABLED)
            self.client_write_btn.config(state=tk.DISABLED)
            self.client_lock_var.set("锁状态: 未连接")
            
            # 停止自动刷新
            self.stop_auto_refresh()
            
            self.status_var.set("已断开连接")
            messagebox.showinfo("成功", "已断开连接")
            
        except Exception as e:
            messagebox.showerror("错误", f"断开连接失败: {e}")
            
    def client_write(self):
        """Client 写入共享内存（通过TCP远程写入）"""
        if not self.client_socket:
            messagebox.showwarning("警告", "未连接")
            return
            
        text = self.client_text.get("1.0", tk.END).rstrip('\n')
        byte_count = len(text.encode("utf-8"))
        
        if byte_count > MAX_DATA_SIZE:
            messagebox.showerror("错误", f"文本太长: {byte_count} > {MAX_DATA_SIZE} bytes")
            return
            
        try:
            # 写入时自动上锁（对用户透明），写入完成后立即释放
            self.client_lock_var.set("锁状态: 写入中...")
            self.client_write_btn.config(state=tk.DISABLED)
            
            # 通过TCP远程写入
            self.client_write_remote(text)
            
            # 写入完成，立即更新状态
            self.client_lock_var.set("锁状态: 空闲（远程模式）")
            self.client_write_btn.config(state=tk.NORMAL)
            self.is_locked = False
            
            # 更新last_content，避免立即被覆盖
            self.last_content = text
            
            self.status_var.set("写入成功，已同步")
            messagebox.showinfo("成功", "写入成功！内容已同步到host")
            
        except Exception as e:
            self.client_lock_var.set("锁状态: 空闲（远程模式）")
            self.client_write_btn.config(state=tk.NORMAL)
            self.is_locked = False
            messagebox.showerror("错误", f"写入失败: {e}")
    
    def client_read_remote(self):
        """通过TCP从远程Host读取共享内存内容"""
        if not self.client_socket:
            raise RuntimeError("未连接到服务器")
        
        try:
            # 发送READ命令
            self.client_socket.sendall(b"READ\n")
            
            # 接收响应（设置超时）
            self.client_socket.settimeout(10.0)
            response = b""
            while not response.endswith(b"\n"):
                chunk = self.client_socket.recv(4096)
                if not chunk:
                    raise RuntimeError("服务器关闭连接")
                response += chunk
            
            # 解析响应: "OK <content>\n" 或 "ERROR <message>\n"
            response_str = response.decode("utf-8", errors="replace").strip()
            if response_str.startswith("OK "):
                # 提取内容（跳过"OK "前缀）
                content = response_str[3:]  # 跳过"OK "
                return content
            elif response_str.startswith("ERROR "):
                error_msg = response_str[6:]  # 跳过"ERROR "
                raise RuntimeError(f"服务器错误: {error_msg}")
            else:
                raise RuntimeError(f"无效的服务器响应: {response_str}")
        except socket.timeout:
            raise RuntimeError("读取超时：服务器未响应")
        except Exception as e:
            raise RuntimeError(f"读取失败: {e}")
    
    def client_write_remote(self, text):
        """通过TCP向远程Host写入共享内存内容"""
        if not self.client_socket:
            raise RuntimeError("未连接到服务器")
        
        try:
            # 发送WRITE命令和内容
            # 格式: "WRITE <length>\n<content>\n"
            content_bytes = text.encode("utf-8")
            length = len(content_bytes)
            
            # 发送命令: "WRITE <length>\n"
            cmd = f"WRITE {length}\n".encode("utf-8")
            self.client_socket.sendall(cmd)
            
            # 发送内容
            self.client_socket.sendall(content_bytes)
            
            # 发送结束标记\n
            self.client_socket.sendall(b"\n")
            
            # 接收响应（设置超时）
            self.client_socket.settimeout(10.0)
            response = b""
            while not response.endswith(b"\n"):
                chunk = self.client_socket.recv(1024)
                if not chunk:
                    raise RuntimeError("服务器关闭连接")
                response += chunk
            
            # 解析响应: "OK\n" 或 "ERROR <message>\n"
            response_str = response.decode("utf-8", errors="replace").strip()
            if response_str == "OK":
                return  # 成功
            elif response_str.startswith("ERROR "):
                error_msg = response_str[6:]
                raise RuntimeError(f"服务器错误: {error_msg}")
            else:
                raise RuntimeError(f"无效的服务器响应: {response_str}")
        except socket.timeout:
            raise RuntimeError("写入超时：服务器未响应")
        except Exception as e:
            raise RuntimeError(f"写入失败: {e}")
    
    def client_auto_refresh(self):
        """Client 自动刷新共享内存内容到输入框（通过TCP远程读取）"""
        if not self.client_socket:
            return
        try:
            # 通过TCP远程读取
            text = self.client_read_remote()
            if text != self.last_content:
                # 直接覆盖输入框内容，即使正在编辑
                current_pos = self.client_text.index(tk.INSERT)
                self.client_text.delete("1.0", tk.END)
                self.client_text.insert("1.0", text)
                # 尝试恢复光标位置（如果可能）
                try:
                    self.client_text.mark_set(tk.INSERT, current_pos)
                except:
                    pass
                self.last_content = text
                # 更新字符计数
                byte_count = len(text.encode("utf-8"))
                self.client_count_var.set(f"{byte_count} / {MAX_DATA_SIZE} bytes")
        except Exception as e:
            pass  # 静默失败，避免频繁弹窗
            
    
    def start_auto_refresh(self):
        """启动自动刷新（定期检查共享内存变化）"""
        if self.auto_refresh_running:
            return
        self.auto_refresh_running = True
        
        def refresh_loop():
            if not self.auto_refresh_running:
                return
            try:
                if self.mode.get() == "host" and self.shm:
                    self.host_auto_refresh()
                elif self.mode.get() == "client":
                    # 远程模式：检查socket连接；本地模式：检查共享内存
                    if self.client_socket or self.shm:
                        self.client_auto_refresh()
            except:
                pass
            # 每500ms检查一次
            self.root.after(500, refresh_loop)
        
        refresh_loop()
    
    def stop_auto_refresh(self):
        """停止自动刷新"""
        self.auto_refresh_running = False


def main():
    root = tk.Tk()
    app = SharedMemoryGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

