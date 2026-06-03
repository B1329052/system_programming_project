"""
interpreter.py — 直譯器
走訪 AST 節點並執行對應的動作
這是整個解譯器的核心：讀取 parser 產生的 AST，然後一步一步執行
"""

import math
from environment import Memory, VarInfo, Environment


# ========== 流程控制用的例外 ==========
# 用 Python 的 exception 來實作 break / continue / return
# 這是直譯器常見的技巧，不是真的「錯誤」

class BreakSignal(Exception):
    """break 語句的信號"""
    pass

class ContinueSignal(Exception):
    """continue 語句的信號"""
    pass

class ReturnSignal(Exception):
    """return 語句的信號，帶有回傳值"""
    def __init__(self, value=0):
        self.value = value


# ========== Interpreter 類別 ==========

class Interpreter:
    """
    AST 直譯器
    走訪每個 AST 節點，根據節點類型執行對應的動作
    """

    def __init__(self, memory=None, global_env=None, builtins_funcs=None):
        # 記憶體空間
        self.memory = memory or Memory()
        # 全域環境
        self.global_env = global_env or Environment()
        # 目前的環境（執行時會切換）
        self.env = self.global_env
        # 內建函式表（由 builtins.py 提供）
        self.builtin_funcs = builtins_funcs or {}
        # 追蹤模式
        self.trace_mode = False
        # 原始碼行（用於 TRACE 顯示）
        self.source_lines = []

    # ========== 語句執行 ==========

    def exec_program(self, program_node):
        """執行整個程式（註冊函式和全域變數）"""
        for decl in program_node['declarations']:
            if decl['type'] == 'func_def':
                self.env.declare_func(decl['name'], decl)
            elif decl['type'] == 'var_decl':
                self.exec_var_decl(decl)

    def exec_statement(self, stmt):
        """根據語句類型分派執行"""
        if self.trace_mode and 'line' in stmt:
            line_num = stmt.get('line', 0)
            if 0 < line_num <= len(self.source_lines):
                line_text = self.source_lines[line_num - 1].strip()
                if line_text:
                    print(f"[line {line_num}] {line_text}")

        stype = stmt['type']

        if stype == 'var_decl':
            self.exec_var_decl(stmt)
        elif stype == 'expr_stmt':
            self.eval_expr(stmt['expr'])
        elif stype == 'block':
            self.exec_block(stmt)
        elif stype == 'if':
            self.exec_if(stmt)
        elif stype == 'while':
            self.exec_while(stmt)
        elif stype == 'for':
            self.exec_for(stmt)
        elif stype == 'do_while':
            self.exec_do_while(stmt)
        elif stype == 'return':
            val = 0
            if stmt.get('value'):
                val = self.eval_expr(stmt['value'])
            raise ReturnSignal(val)
        elif stype == 'break':
            raise BreakSignal()
        elif stype == 'continue':
            raise ContinueSignal()
        else:
            raise RuntimeError(f"Unknown statement type: {stype}")

    def exec_block(self, block):
        """執行區塊（建立新的子作用域）"""
        old_env = self.env
        self.env = self.env.create_child()
        try:
            for stmt in block['body']:
                self.exec_statement(stmt)
        finally:
            self.env = old_env

    def exec_var_decl(self, decl):
        """
        執行變數宣告
        處理 int x; / int x = 10; / int arr[10]; / int *p; / char s[50];
        """
        name = decl['name']
        vtype = decl['var_type']
        is_pointer = decl.get('is_pointer', False)
        array_size = decl.get('array_size')

        if array_size is not None:
            # 陣列宣告：分配多格記憶體
            addr = self.memory.allocate(array_size)
            var = VarInfo(name, vtype, addr, is_array=True, array_size=array_size)
        elif is_pointer:
            # 指標宣告：分配 1 格存地址
            addr = self.memory.allocate(1)
            self.memory.write(addr, 0)  # 初始化為 NULL
            var = VarInfo(name, vtype, addr, is_pointer=True)
        else:
            # 一般變數：分配 1 格
            addr = self.memory.allocate(1)
            self.memory.write(addr, 0)  # 初始化為 0
            var = VarInfo(name, vtype, addr)

        self.env.declare_var(name, var)

        # 如果有初始值
        if decl.get('init') is not None:
            val = self.eval_expr(decl['init'])
            if is_pointer:
                self.memory.write(addr, val)
            elif vtype == 'char' and isinstance(val, int):
                self.memory.write(addr, val & 0xFF)
            else:
                self.memory.write(addr, val)

    def exec_if(self, stmt):
        """執行 if / else"""
        cond = self.eval_expr(stmt['condition'])
        if cond:
            self.exec_statement(stmt['then_body'])
        elif stmt.get('else_body'):
            self.exec_statement(stmt['else_body'])

    def exec_while(self, stmt):
        """執行 while 迴圈"""
        while True:
            cond = self.eval_expr(stmt['condition'])
            if not cond:
                break
            try:
                self.exec_statement(stmt['body'])
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def exec_for(self, stmt):
        """執行 for 迴圈"""
        # init
        if stmt.get('init'):
            self.exec_statement(stmt['init'])

        while True:
            # condition
            if stmt.get('condition'):
                cond = self.eval_expr(stmt['condition'])
                if not cond:
                    break
            # body
            try:
                self.exec_statement(stmt['body'])
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            # update
            if stmt.get('update'):
                self.eval_expr(stmt['update'])

    def exec_do_while(self, stmt):
        """執行 do-while 迴圈"""
        while True:
            try:
                self.exec_statement(stmt['body'])
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            cond = self.eval_expr(stmt['condition'])
            if not cond:
                break

    # ========== 表達式求值 ==========

    def eval_expr(self, expr):
        """根據表達式類型分派求值"""
        etype = expr['type']

        if etype == 'int_literal':
            return expr['value']

        if etype == 'string_literal':
            return self.alloc_string(expr['value'])

        if etype == 'identifier':
            return self.eval_identifier(expr)

        if etype == 'binary_op':
            return self.eval_binary_op(expr)

        if etype == 'unary_op':
            return self.eval_unary_op(expr)

        if etype == 'assign':
            return self.eval_assign(expr)

        if etype == 'call':
            return self.eval_call(expr)

        if etype == 'index':
            return self.eval_index(expr)

        if etype == 'deref':
            return self.eval_deref(expr)

        if etype == 'addr_of':
            return self.eval_addr_of(expr)

        raise RuntimeError(f"Unknown expression type: {etype}")

    def eval_identifier(self, expr):
        """求值識別字（讀取變數的值）"""
        name = expr['name']
        var = self.env.lookup_var(name)
        if var is None:
            raise RuntimeError(f"Undefined variable '{name}'")

        # 陣列名稱直接回傳基底地址（類似 C 的陣列退化為指標）
        if var.is_array:
            return var.addr

        # 一般變數或指標：讀取記憶體中的值
        return self.memory.read(var.addr)

    def eval_binary_op(self, expr):
        """計算二元運算"""
        op = expr['op']
        left = self.eval_expr(expr['left'])
        
        # 短路求值：&& 和 || 不一定要算右邊
        if op == '&&':
            return 1 if (left and self.eval_expr(expr['right'])) else 0
        if op == '||':
            return 1 if (left or self.eval_expr(expr['right'])) else 0

        right = self.eval_expr(expr['right'])

        if op == '+':  return int(left + right)
        if op == '-':  return int(left - right)
        if op == '*':  return int(left * right)
        if op == '/':
            if right == 0:
                raise RuntimeError("runtime error: division by zero")
            # C 語言整數除法：往 0 取整
            return int(left / right) if (left * right >= 0) else -int(abs(left) / abs(right))
        if op == '%':
            if right == 0:
                raise RuntimeError("runtime error: division by zero")
            # C 語言取餘：結果的符號與被除數相同
            result = abs(left) % abs(right)
            return result if left >= 0 else -result

        if op == '<':   return 1 if left < right else 0
        if op == '<=':  return 1 if left <= right else 0
        if op == '>':   return 1 if left > right else 0
        if op == '>=':  return 1 if left >= right else 0
        if op == '==':  return 1 if left == right else 0
        if op == '!=':  return 1 if left != right else 0

        if op == '&':   return left & right
        if op == '|':   return left | right
        if op == '^':   return left ^ right
        if op == '<<':  return left << right
        if op == '>>':  return left >> right

        raise RuntimeError(f"Unknown operator: {op}")

    def eval_unary_op(self, expr):
        """計算一元運算"""
        op = expr['op']
        val = self.eval_expr(expr['operand'])
        if op == '+':  return val
        if op == '-':  return -val
        if op == '!':  return 1 if not val else 0
        raise RuntimeError(f"Unknown unary operator: {op}")

    def eval_assign(self, expr):
        """
        執行指定運算 (=, +=, -=, *=, /=, %=)
        目標可能是：變數、陣列元素、解參照的指標
        """
        op = expr['op']
        target = expr['target']
        rhs = self.eval_expr(expr['value'])

        # 取得目標的記憶體地址
        addr = self.get_lvalue_addr(target)

        if op == '=':
            self.memory.write(addr, rhs)
            return rhs

        # 複合指定：先讀舊值再運算
        old_val = self.memory.read(addr)
        if op == '+=':   result = old_val + rhs
        elif op == '-=': result = old_val - rhs
        elif op == '*=': result = old_val * rhs
        elif op == '/=':
            if rhs == 0:
                raise RuntimeError("runtime error: division by zero")
            result = int(old_val / rhs) if (old_val * rhs >= 0) else -int(abs(old_val) / abs(rhs))
        elif op == '%=':
            if rhs == 0:
                raise RuntimeError("runtime error: division by zero")
            r = abs(old_val) % abs(rhs)
            result = r if old_val >= 0 else -r
        else:
            raise RuntimeError(f"Unknown assignment operator: {op}")

        self.memory.write(addr, int(result))
        return int(result)

    def eval_call(self, expr):
        """
        執行函式呼叫
        先檢查是否為內建函式，否則找使用者定義的函式
        """
        # 取得函式名稱
        func_expr = expr['func']
        if func_expr['type'] == 'identifier':
            func_name = func_expr['name']
        else:
            raise RuntimeError("Invalid function call")

        # 先求值所有引數
        args = [self.eval_expr(a) for a in expr['args']]

        # 檢查內建函式
        if func_name in self.builtin_funcs:
            return self.builtin_funcs[func_name](args, self)

        # 查找使用者定義的函式
        func_def = self.env.lookup_func(func_name)
        if func_def is None:
            raise RuntimeError(f"Undefined function '{func_name}'")

        return self.call_user_func(func_def, args)

    def call_user_func(self, func_def, args):
        """呼叫使用者定義的函式"""
        # 儲存記憶體狀態和目前環境
        saved_mem = self.memory.save_state()
        old_env = self.env

        # 建立函式的新環境（parent 是全域環境）
        func_env = self.global_env.create_child()
        self.env = func_env

        # 綁定參數
        params = func_def['params']
        for i, param in enumerate(params):
            pname = param['name']
            ptype = param['param_type']
            is_ptr = param.get('is_pointer', False)

            # 分配參數的記憶體
            addr = self.memory.allocate(1)
            val = args[i] if i < len(args) else 0
            self.memory.write(addr, val)

            var = VarInfo(pname, ptype, addr, is_pointer=is_ptr)
            self.env.declare_var(pname, var)

        # 執行函式本體
        try:
            for stmt in func_def['body']['body']:
                self.exec_statement(stmt)
            result = 0  # 沒有 return 的話回傳 0
        except ReturnSignal as r:
            result = r.value

        # 還原環境（但不還原記憶體，因為指標可能指向函式內分配的記憶體）
        self.env = old_env
        # 對於非指標回傳的情況，可以還原記憶體
        # 但為了簡化，我們不還原（記憶體夠大不會用完）
        return result

    def eval_index(self, expr):
        """計算陣列索引 arr[i] 的值"""
        base_addr = self.eval_expr(expr['array'])
        index = self.eval_expr(expr['index'])

        # 檢查陣列越界（如果能取得陣列資訊的話）
        if expr['array']['type'] == 'identifier':
            var = self.env.lookup_var(expr['array']['name'])
            if var and var.is_array and (index < 0 or index >= var.array_size):
                raise RuntimeError(
                    f"runtime error: array index out of bounds "
                    f"(index {index}, size {var.array_size})")

        return self.memory.read(base_addr + index)

    def eval_deref(self, expr):
        """解參照 *p：讀取指標指向的值"""
        addr = self.eval_expr(expr['operand'])
        if addr == 0:
            raise RuntimeError("runtime error: null pointer dereference")
        return self.memory.read(addr)

    def eval_addr_of(self, expr):
        """取址 &x：取得變數的記憶體地址"""
        return self.get_lvalue_addr(expr['operand'])

    # ========== 左值處理 ==========

    def get_lvalue_addr(self, expr):
        """
        取得表達式的記憶體地址（左值）
        只有變數、陣列元素、解參照的指標才有地址
        """
        if expr['type'] == 'identifier':
            var = self.env.lookup_var(expr['name'])
            if var is None:
                raise RuntimeError(f"Undefined variable '{expr['name']}'")
            return var.addr

        if expr['type'] == 'index':
            # arr[i] 的地址 = arr 的基底地址 + i
            base_addr = self.eval_expr(expr['array'])
            index = self.eval_expr(expr['index'])

            # 檢查越界
            if expr['array']['type'] == 'identifier':
                var = self.env.lookup_var(expr['array']['name'])
                if var and var.is_array and (index < 0 or index >= var.array_size):
                    raise RuntimeError(
                        f"runtime error: array index out of bounds "
                        f"(index {index}, size {var.array_size})")

            return base_addr + index

        if expr['type'] == 'deref':
            # *p 的地址就是 p 的值
            return self.eval_expr(expr['operand'])

        raise RuntimeError("Expression is not an lvalue (cannot assign to it)")

    # ========== 字串處理輔助 ==========

    def alloc_string(self, s):
        """把字串存進記憶體，回傳起始地址"""
        addr = self.memory.allocate(len(s) + 1)
        self.memory.write_string(addr, s)
        return addr

    # ========== 執行 main() ==========

    def run_main(self):
        """
        找到 main() 函式並執行
        回傳 main() 的 return value
        """
        main_func = self.env.lookup_func('main')
        if main_func is None:
            raise RuntimeError("No main() function found")
        return self.call_user_func(main_func, [])
