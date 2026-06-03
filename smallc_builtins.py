"""
builtins.py — 內建函式
提供 Small-C 的內建函式（printf, strlen, abs 等）
每個函式接收 (args, interpreter) 參數
"""

import random
import math
import sys


# ========== I/O 函式 ==========

def builtin_printf(args, interp):
    """
    printf(format, ...) — 格式化輸出
    支援 %d, %c, %s, %x, %%
    支援 \n, \t 等跳脫字元（已在 lexer 處理）
    """
    if len(args) < 1:
        return 0

    # 第一個參數是格式字串的地址
    fmt_addr = args[0]
    fmt = interp.memory.read_string(fmt_addr)

    # 解析格式字串並代入參數
    output = ''
    arg_idx = 1
    i = 0
    while i < len(fmt):
        if fmt[i] == '%' and i + 1 < len(fmt):
            i += 1
            spec = fmt[i]
            if spec == 'd':
                val = args[arg_idx] if arg_idx < len(args) else 0
                output += str(int(val))
                arg_idx += 1
            elif spec == 'c':
                val = args[arg_idx] if arg_idx < len(args) else 0
                output += chr(int(val) & 0xFF)
                arg_idx += 1
            elif spec == 's':
                addr = args[arg_idx] if arg_idx < len(args) else 0
                output += interp.memory.read_string(addr)
                arg_idx += 1
            elif spec == 'x':
                val = args[arg_idx] if arg_idx < len(args) else 0
                output += format(int(val) & 0xFFFFFFFF, 'x')
                arg_idx += 1
            elif spec == '%':
                output += '%'
            else:
                output += '%' + spec
        else:
            output += fmt[i]
        i += 1

    print(output, end='')
    return len(output)


def builtin_getchar(args, interp):
    """getchar() — 讀取一個字元"""
    try:
        ch = sys.stdin.read(1)
        return ord(ch) if ch else -1
    except:
        return -1


def builtin_putchar(args, interp):
    """putchar(ch) — 輸出一個字元"""
    if len(args) >= 1:
        print(chr(int(args[0]) & 0xFF), end='')
    return args[0] if args else 0


def builtin_puts(args, interp):
    """puts(str) — 輸出字串並換行"""
    if len(args) >= 1:
        s = interp.memory.read_string(args[0])
        print(s)
    return 0


def builtin_scanf(args, interp):
    """
    scanf(format, &var) — 簡化版，只支援 %d 讀取整數
    """
    if len(args) < 2:
        return 0

    fmt_addr = args[0]
    fmt = interp.memory.read_string(fmt_addr)

    count = 0
    arg_idx = 1
    for i, ch in enumerate(fmt):
        if ch == '%' and i + 1 < len(fmt) and fmt[i + 1] == 'd':
            try:
                val = int(input())
                if arg_idx < len(args):
                    interp.memory.write(args[arg_idx], val)
                    arg_idx += 1
                    count += 1
            except:
                break
    return count


# ========== 字串函式 ==========

def builtin_strlen(args, interp):
    """strlen(str) — 回傳字串長度"""
    if len(args) < 1:
        return 0
    s = interp.memory.read_string(args[0])
    return len(s)


def builtin_strcpy(args, interp):
    """strcpy(dest, src) — 複製字串"""
    if len(args) < 2:
        return 0
    dest_addr = args[0]
    src = interp.memory.read_string(args[1])
    interp.memory.write_string(dest_addr, src)
    return dest_addr


def builtin_strcat(args, interp):
    """strcat(dest, src) — 串接字串"""
    if len(args) < 2:
        return 0
    dest_addr = args[0]
    dest_str = interp.memory.read_string(dest_addr)
    src_str = interp.memory.read_string(args[1])
    interp.memory.write_string(dest_addr, dest_str + src_str)
    return dest_addr


def builtin_strcmp(args, interp):
    """strcmp(s1, s2) — 比較字串，相等回 0，s1<s2 回負數，s1>s2 回正數"""
    if len(args) < 2:
        return 0
    s1 = interp.memory.read_string(args[0])
    s2 = interp.memory.read_string(args[1])
    if s1 < s2:
        return -1
    elif s1 > s2:
        return 1
    return 0


# ========== 數學函式 ==========

def builtin_abs(args, interp):
    """abs(x) — 絕對值"""
    return abs(int(args[0])) if args else 0


def builtin_max(args, interp):
    """max(a, b) — 取較大值"""
    if len(args) >= 2:
        return max(int(args[0]), int(args[1]))
    return args[0] if args else 0


def builtin_min(args, interp):
    """min(a, b) — 取較小值"""
    if len(args) >= 2:
        return min(int(args[0]), int(args[1]))
    return args[0] if args else 0


def builtin_pow(args, interp):
    """pow(base, exp) — 次方"""
    if len(args) >= 2:
        return int(args[0] ** args[1])
    return 0


def builtin_sqrt(args, interp):
    """sqrt(x) — 平方根（回傳整數）"""
    if len(args) < 1:
        return 0
    val = args[0]
    if val < 0:
        raise RuntimeError("runtime error: sqrt of negative number")
    return int(math.sqrt(val))


# ========== 工具函式 ==========

def builtin_atoi(args, interp):
    """atoi(str) — 字串轉整數"""
    if len(args) < 1:
        return 0
    s = interp.memory.read_string(args[0])
    try:
        return int(s)
    except:
        return 0


def builtin_itoa(args, interp):
    """itoa(num, str) — 整數轉字串（存入 str）"""
    if len(args) < 2:
        return 0
    num = int(args[0])
    dest_addr = args[1]
    s = str(num)
    interp.memory.write_string(dest_addr, s)
    return dest_addr


_rand_state = [12345]  # 隨機數種子

def builtin_rand(args, interp):
    """rand() — 產生隨機整數"""
    return random.randint(0, 32767)


def builtin_srand(args, interp):
    """srand(seed) — 設定隨機數種子"""
    if args:
        random.seed(int(args[0]))
    return 0


def builtin_memset(args, interp):
    """memset(ptr, value, size) — 填充記憶體"""
    if len(args) < 3:
        return 0
    addr = args[0]
    value = int(args[1]) & 0xFF
    size = int(args[2])
    for i in range(size):
        interp.memory.write(addr + i, value)
    return addr


def builtin_sizeof(args, interp):
    """sizeof(x) — 回傳大小（簡化版：int=1, array=array_size）"""
    # 在互動模式下，sizeof 會被當成函式呼叫
    # 這裡簡化處理，回傳 1（int 的大小）
    return 1 if args else 0


def builtin_isdigit(args, interp):
    """isdigit(ch) — 判斷是否為數字字元"""
    if args:
        ch = int(args[0])
        return 1 if (48 <= ch <= 57) else 0  # '0'=48, '9'=57
    return 0


def builtin_isalpha(args, interp):
    """isalpha(ch) — 判斷是否為英文字母"""
    if args:
        ch = int(args[0])
        return 1 if (65 <= ch <= 90 or 97 <= ch <= 122) else 0
    return 0


# ========== 註冊所有內建函式 ==========

def get_all_builtins():
    """
    回傳所有內建函式的字典
    key = 函式名稱, value = Python 函式
    """
    return {
        # I/O
        'printf':   builtin_printf,
        'getchar':  builtin_getchar,
        'putchar':  builtin_putchar,
        'puts':     builtin_puts,
        'scanf':    builtin_scanf,
        # 字串
        'strlen':   builtin_strlen,
        'strcpy':   builtin_strcpy,
        'strcat':   builtin_strcat,
        'strcmp':    builtin_strcmp,
        # 數學
        'abs':      builtin_abs,
        'max':      builtin_max,
        'min':      builtin_min,
        'pow':      builtin_pow,
        'sqrt':     builtin_sqrt,
        # 工具
        'atoi':     builtin_atoi,
        'itoa':     builtin_itoa,
        'rand':     builtin_rand,
        'srand':    builtin_srand,
        'memset':   builtin_memset,
        'sizeof':   builtin_sizeof,
        'isdigit':  builtin_isdigit,
        'isalpha':  builtin_isalpha,
    }
