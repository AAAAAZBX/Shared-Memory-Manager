"""共享内存工具模块
包含共享内存相关的常量、类和工具函数
"""
import socket
import struct
import time
import threading
from multiprocessing import shared_memory

# 常量定义
BUF_SIZE = 4096
LOCK_SIZE = 1
LEN_SIZE = 4
DATA_OFFSET = LOCK_SIZE + LEN_SIZE
LEN_FMT = "<I"
LOCK_FREE = 0
LOCK_HELD = 1
MAX_DATA_SIZE = BUF_SIZE - DATA_OFFSET  # 4091 bytes
SYNC_UPDATE_CMD = "SYNC_UPDATE"  # 同步更新命令


def get_local_ip():
    """获取本机的实际 IP 地址（非 127.0.0.1）"""
    try:
        # 方法1: 通过连接外部地址获取本机 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # 连接到外部地址（不会实际发送数据）
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            # 方法2: 通过主机名获取
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            # 如果返回的是 127.0.0.1，尝试获取所有 IP
            if ip == "127.0.0.1":
                ip_list = socket.gethostbyname_ex(hostname)[2]
                # 过滤掉 127.x.x.x 和 ::1
                for ip_addr in ip_list:
                    if not ip_addr.startswith("127.") and ":" not in ip_addr:
                        return ip_addr
            return ip
        except:
            return "127.0.0.1"


class SharedMemoryLock:
    """基于共享内存的简单锁机制（整块锁）"""
    def __init__(self, shm: shared_memory.SharedMemory, lock_offset: int = 0):
        self.shm = shm
        self.lock_offset = lock_offset
        self.local_lock = threading.Lock()
        
    def acquire(self, timeout=5.0):
        """获取锁，带超时机制"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.local_lock:
                if self.shm.buf[self.lock_offset] == LOCK_FREE:
                    self.shm.buf[self.lock_offset] = LOCK_HELD
                    if self.shm.buf[self.lock_offset] == LOCK_HELD:
                        return True
            time.sleep(0.01)
        raise TimeoutError(f"获取锁超时（{timeout}秒）")
    
    def release(self):
        """释放锁"""
        with self.local_lock:
            if self.shm.buf[self.lock_offset] == LOCK_HELD:
                self.shm.buf[self.lock_offset] = LOCK_FREE
            else:
                raise RuntimeError("尝试释放未持有的锁")
    
    def is_locked(self):
        """检查锁是否被占用"""
        return self.shm.buf[self.lock_offset] == LOCK_HELD


def shm_write(shm: shared_memory.SharedMemory, text: str, lock: SharedMemoryLock, 
              data_offset: int = DATA_OFFSET, buf_size: int = BUF_SIZE):
    """原子性写入共享内存，写入完成后立即释放锁"""
    # 移除文本末尾的空白字符，避免写入多余的空格
    text = text.rstrip()
    data = text.encode("utf-8")
    max_data_size = buf_size - data_offset
    if len(data) > max_data_size:
        raise ValueError(f"文本太长: {len(data)} > {max_data_size} bytes")
    
    # 获取锁
    lock.acquire()
    try:
        # 写入数据
        len_offset = lock.lock_offset + 4
        # 确保长度字段正确写入实际数据长度
        shm.buf[len_offset:len_offset+4] = struct.pack(LEN_FMT, len(data))
        # 写入实际数据
        shm.buf[data_offset:data_offset+len(data)] = data
        # 清空剩余区域（使用空字节填充，不是空格）
        remaining = buf_size - data_offset - len(data)
        if remaining > 0:
            shm.buf[data_offset+len(data):buf_size] = b"\x00" * remaining
    finally:
        # 写入完成后立即释放锁
        lock.release()


def shm_read(shm: shared_memory.SharedMemory, lock: SharedMemoryLock, 
             data_offset: int = DATA_OFFSET):
    """读取共享内存"""
    lock.acquire()
    try:
        len_offset = lock.lock_offset + 4
        (n,) = struct.unpack(LEN_FMT, bytes(shm.buf[len_offset:len_offset+4]))
        
        # 验证长度字段的合理性，防止读取到无效数据
        max_valid_len = BUF_SIZE - data_offset
        if n < 0 or n > max_valid_len:
            # 长度字段异常，尝试找到实际数据结束位置
            # 查找第一个空字节或缓冲区结束
            actual_data = bytes(shm.buf[data_offset:BUF_SIZE])
            # 找到第一个空字节的位置
            null_pos = actual_data.find(b'\x00')
            if null_pos > 0:
                n = null_pos
            else:
                # 如果没有空字节，使用整个缓冲区（但限制在合理范围内）
                n = min(len(actual_data.rstrip(b'\x00')), max_valid_len)
        
        # 只读取指定长度的数据
        data = bytes(shm.buf[data_offset:data_offset+n])
        # 移除末尾的空字节
        data = data.rstrip(b'\x00')
        return data.decode("utf-8", errors="replace")
    finally:
        lock.release()

