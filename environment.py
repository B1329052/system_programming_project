"""
environment.py — 環境與記憶體管理
管理變數、函式的儲存與查找，以及模擬 C 語言的記憶體空間
"""


# ========== 記憶體模擬 ==========

class Memory:
    """
    模擬 C 語言的記憶體空間
    用一個大 list 當作記憶體，每個位置存一個整數值
    - int 變數佔 1 格
    - int arr[10] 佔 10 格
    - char arr[50] 佔 50 格
    - 指標變數佔 1 格（存的是另一個變數的地址）
    """
    def __init__(self, size=65536):
        self.data = [0] * size   # 記憶體空間
        self.next_addr = 100     # 下一個可用的地址（從 100 開始，0 保留給 NULL）
        self.size = size

    def allocate(self, count=1):
        """分配 count 格記憶體，回傳起始地址"""
        addr = self.next_addr
        if addr + count > self.size:
            raise RuntimeError("Out of memory")
        self.next_addr += count
        return addr

    def read(self, addr):
        """讀取指定地址的值"""
        if 0 <= addr < self.size:
            return self.data[addr]
        raise RuntimeError(f"Memory access out of bounds: address {addr}")

    def write(self, addr, value):
        """寫入值到指定地址"""
        if 0 <= addr < self.size:
            self.data[addr] = value
        else:
            raise RuntimeError(f"Memory access out of bounds: address {addr}")

    def read_string(self, addr):
        """從指定地址讀取字串（讀到 0 結束，模擬 C 字串）"""
        chars = []
        while 0 <= addr < self.size:
            val = self.data[addr]
            if val == 0:
                break
            chars.append(chr(val & 0xFF))
            addr += 1
        return ''.join(chars)

    def write_string(self, addr, s):
        """把字串寫入指定地址（包含結尾的 0）"""
        for ch in s:
            if addr >= self.size:
                break
            self.data[addr] = ord(ch)
            addr += 1
        if addr < self.size:
            self.data[addr] = 0  # 結尾 null

    def save_state(self):
        """儲存目前的分配狀態（用於函式呼叫前保存）"""
        return self.next_addr

    def restore_state(self, saved_addr):
        """還原分配狀態（函式返回後釋放區域變數的記憶體）"""
        self.next_addr = saved_addr


# ========== 變數資訊 ==========

class VarInfo:
    """
    記錄一個變數的完整資訊
    - name: 變數名稱
    - var_type: 型別（'int', 'char'）
    - addr: 在記憶體中的地址
    - is_pointer: 是否為指標變數
    - is_array: 是否為陣列
    - array_size: 陣列大小（若為陣列）
    """
    def __init__(self, name, var_type, addr, is_pointer=False,
                 is_array=False, array_size=0):
        self.name = name
        self.var_type = var_type
        self.addr = addr
        self.is_pointer = is_pointer
        self.is_array = is_array
        self.array_size = array_size

    def __repr__(self):
        type_str = self.var_type
        if self.is_pointer:
            type_str += '*'
        if self.is_array:
            type_str += f'[{self.array_size}]'
        return f'VarInfo({type_str} {self.name}, addr={self.addr})'


# ========== 環境（作用域）管理 ==========

class Environment:
    """
    管理變數和函式的作用域
    用 parent 鏈實作巢狀作用域：
    - 全域環境 (parent=None)
      └─ 函式環境 (parent=全域)
           └─ 區塊環境 (parent=函式)
    查找變數時，從內層往外層找
    """
    def __init__(self, parent=None):
        self.parent = parent          # 上層環境
        self.variables = {}           # 變數表: name → VarInfo
        self.functions = {}           # 函式表: name → func_def AST 節點
        self.return_type = None       # 目前函式的回傳型別

    def declare_var(self, name, var_info):
        """在目前作用域宣告變數"""
        self.variables[name] = var_info

    def lookup_var(self, name):
        """查找變數（從內層往外層找）"""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.lookup_var(name)
        return None

    def declare_func(self, name, func_node):
        """宣告函式（存到最外層的全域環境）"""
        env = self
        while env.parent:
            env = env.parent
        env.functions[name] = func_node

    def lookup_func(self, name):
        """查找函式（從全域環境找）"""
        env = self
        while env.parent:
            env = env.parent
        return env.functions.get(name, None)

    def get_all_vars(self):
        """取得目前作用域（含上層）的所有變數"""
        result = {}
        if self.parent:
            result.update(self.parent.get_all_vars())
        result.update(self.variables)
        return result

    def get_all_funcs(self):
        """取得所有函式"""
        env = self
        while env.parent:
            env = env.parent
        return dict(env.functions)

    def create_child(self):
        """建立子作用域"""
        return Environment(parent=self)
