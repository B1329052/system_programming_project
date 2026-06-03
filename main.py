"""
main.py — Small-C 互動式直譯器主程式
提供 REPL 環境，支援互動指令與直接輸入 C 語句
"""

import os
import sys

from lexer import tokenize, preprocess_defines
from parser import Parser
from interpreter import Interpreter
from environment import Memory, Environment
from smallc_builtins import get_all_builtins


VERSION = "1.0.0"
AUTHOR = "鄭弘昇、涂佑溦、顏姿寧"
SEMESTER = "114-2"


class SmallCREPL:
    """Small-C 互動式直譯器：管理程式緩衝區、指令處理、即時執行"""

    def __init__(self):
        self.program_buffer = []
        self.trace_mode = False
        self.builtins = get_all_builtins()
        self.reset_interactive()

    def reset_interactive(self):
        """重設互動模式的狀態"""
        self.interactive_memory = Memory()
        self.interactive_env = Environment()
        self.interactive_interp = Interpreter(
            memory=self.interactive_memory,
            global_env=self.interactive_env,
            builtins_funcs=self.builtins
        )

    # ========== 主迴圈 ==========

    def run(self):
        """啟動 REPL"""
        print(f"Small-C Interactive Interpreter v{VERSION}")
        print(f"Type 'HELP' for available commands.\n")

        while True:
            try:
                line = input("sc> ")
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue

            line = line.strip()
            if not line:
                continue

            if self.try_command(line):
                continue

            self.execute_interactive(line)

    # ========== 指令處理 ==========

    def try_command(self, line):
        """嘗試將輸入當作指令處理，回傳 True 表示已處理"""
        parts = line.split(None, 1)
        cmd = parts[0].upper()
        arg = parts[1].strip() if len(parts) > 1 else ''

        commands = {
            'ABOUT':    self.cmd_about,
            'HELP':     self.cmd_help,
            'APPEND':   self.cmd_append,
            'LIST':     self.cmd_list,
            'EDIT':     self.cmd_edit,
            'DELETE':   self.cmd_delete,
            'INSERT':   self.cmd_insert,
            'CHECK':    self.cmd_check,
            'RUN':      self.cmd_run,
            'SAVE':     self.cmd_save,
            'LOAD':     self.cmd_load,
            'NEW':      self.cmd_new,
            'TRACE':    self.cmd_trace,
            'VARS':     self.cmd_vars,
            'FUNCS':    self.cmd_funcs,
            'CLEAR':    self.cmd_clear,
            'QUIT':     self.cmd_quit,
            'EXIT':     self.cmd_quit,
        }

        if cmd in commands:
            try:
                commands[cmd](arg)
            except Exception as e:
                print(f"Error: {e}")
            return True
        return False

    def cmd_about(self, arg):
        """ABOUT — 顯示版本資訊"""
        print(f"╔══════════════════════════════════════╗")
        print(f"║   Small-C Interactive Interpreter    ║")
        print(f"║   Version: {VERSION:<25s} ║")
        print(f"║   Author: {AUTHOR:<16s}║")
        print(f"║   Semester: {SEMESTER:<24s} ║")
        print(f"║   Python {sys.version.split()[0]:<27s} ║")
        print(f"╚══════════════════════════════════════╝")

    def cmd_help(self, arg):
        """HELP — 顯示指令說明"""
        help_text = """
Available Commands:
  ABOUT          Show interpreter info
  HELP           Show this help message
  APPEND         Enter multi-line input mode
  LIST [n|n1-n2] List program lines
  EDIT n         Edit line n
  DELETE n       Delete line n
  INSERT n       Insert lines before line n
  CHECK          Syntax check (no execution)
  RUN            Compile and run main()
  SAVE filename  Save program to file
  LOAD filename  Load program from file
  NEW            Clear all program and state
  TRACE ON/OFF   Toggle execution tracing
  VARS           Show current variables
  FUNCS          Show defined functions
  CLEAR          Clear terminal screen
  QUIT / EXIT    Exit interpreter

You can also type C statements directly at the sc> prompt.
"""
        print(help_text.strip())

    def cmd_append(self, arg):
        """APPEND — 多行輸入模式"""
        print("Enter program lines (type '.' on a line by itself to finish):")
        line_num = len(self.program_buffer) + 1
        while True:
            try:
                text = input(f"{line_num}> ")
            except EOFError:
                break
            if text.strip() == '.':
                break
            self.program_buffer.append(text)
            line_num += 1
        print(f"{len(self.program_buffer)} lines in buffer.")

    def cmd_list(self, arg):
        """LIST — 列出程式碼"""
        if not self.program_buffer:
            print("(empty program)")
            return

        if not arg:
            start, end = 1, len(self.program_buffer)
        elif '-' in arg:
            parts = arg.split('-')
            start = int(parts[0])
            end = int(parts[1])
        else:
            start = int(arg)
            end = start

        start = max(1, start)
        end = min(end, len(self.program_buffer))

        for i in range(start, end + 1):
            print(f"  {i:4d}: {self.program_buffer[i - 1]}")

    def cmd_edit(self, arg):
        """EDIT n — 編輯第 n 行"""
        if not arg:
            print("Usage: EDIT n")
            return
        n = int(arg)
        if n < 1 or n > len(self.program_buffer):
            print(f"Line {n} out of range (1-{len(self.program_buffer)})")
            return
        print(f"  Current: {self.program_buffer[n - 1]}")
        new_line = input(f"  New    : ")
        self.program_buffer[n - 1] = new_line
        print(f"Line {n} updated.")

    def cmd_delete(self, arg):
        """DELETE n — 刪除第 n 行"""
        if not arg:
            print("Usage: DELETE n")
            return
        n = int(arg)
        if n < 1 or n > len(self.program_buffer):
            print(f"Line {n} out of range (1-{len(self.program_buffer)})")
            return
        deleted = self.program_buffer.pop(n - 1)
        print(f"Deleted line {n}: {deleted}")

    def cmd_insert(self, arg):
        """INSERT n — 在第 n 行前插入"""
        if not arg:
            print("Usage: INSERT n")
            return
        n = int(arg)
        if n < 1:
            n = 1
        if n > len(self.program_buffer) + 1:
            n = len(self.program_buffer) + 1

        print(f"Insert before line {n} (type '.' to finish):")
        new_lines = []
        line_num = n
        while True:
            try:
                text = input(f"{line_num}> ")
            except EOFError:
                break
            if text.strip() == '.':
                break
            new_lines.append(text)
            line_num += 1

        for i, line in enumerate(new_lines):
            self.program_buffer.insert(n - 1 + i, line)
        print(f"Inserted {len(new_lines)} lines.")

    def cmd_check(self, arg):
        """CHECK — 語法檢查"""
        if not self.program_buffer:
            print("No program to check.")
            return
        try:
            source = '\n'.join(self.program_buffer)
            source = preprocess_defines(source)
            tokens = tokenize(source)
            parser = Parser(tokens)
            parser.parse_program()
            print("No errors found.")
        except SyntaxError as e:
            print(f"Syntax error: {e}")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_run(self, arg):
        """RUN — 編譯並執行 main()"""
        if not self.program_buffer:
            print("No program to run.")
            return
        try:
            source = '\n'.join(self.program_buffer)
            source = preprocess_defines(source)
            tokens = tokenize(source)
            parser = Parser(tokens)
            program = parser.parse_program()

            memory = Memory()
            env = Environment()
            interp = Interpreter(
                memory=memory,
                global_env=env,
                builtins_funcs=self.builtins
            )
            interp.trace_mode = self.trace_mode
            interp.source_lines = list(self.program_buffer)

            interp.exec_program(program)
            ret = interp.run_main()
            print(f"Program exited with return value {ret}.")

        except SyntaxError as e:
            print(f"Syntax error: {e}")
        except RuntimeError as e:
            print(f"{e}")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_save(self, arg):
        """SAVE filename — 儲存程式到檔案"""
        if not arg:
            print("Usage: SAVE filename")
            return
        try:
            with open(arg, 'w', encoding='utf-8') as f:
                for line in self.program_buffer:
                    f.write(line + '\n')
            print(f"Saved {len(self.program_buffer)} lines to '{arg}'.")
        except IOError as e:
            print(f"Error saving file: {e}")

    def cmd_load(self, arg):
        """LOAD filename — 載入程式"""
        if not arg:
            print("Usage: LOAD filename")
            return
        try:
            with open(arg, 'r', encoding='utf-8') as f:
                self.program_buffer = [line.rstrip('\n') for line in f]
            print(f"Loaded {len(self.program_buffer)} lines from '{arg}'.")
        except FileNotFoundError:
            print(f"File not found: '{arg}'")
        except IOError as e:
            print(f"Error loading file: {e}")

    def cmd_new(self, arg):
        """NEW — 清除所有狀態"""
        self.program_buffer = []
        self.reset_interactive()
        print("All cleared.")

    def cmd_trace(self, arg):
        """TRACE ON/OFF — 切換追蹤模式"""
        if arg.upper() == 'ON':
            self.trace_mode = True
            print("Trace mode ON.")
        elif arg.upper() == 'OFF':
            self.trace_mode = False
            print("Trace mode OFF.")
        else:
            print("Usage: TRACE ON / TRACE OFF")

    def cmd_vars(self, arg):
        """VARS — 顯示互動模式的變數"""
        all_vars = self.interactive_env.get_all_vars()
        if not all_vars:
            print("No variables defined.")
            return
        for name, var in all_vars.items():
            val = self.interactive_memory.read(var.addr)
            type_str = var.var_type
            if var.is_pointer:
                type_str += '*'
            if var.is_array:
                type_str += f'[{var.array_size}]'
                print(f"  {type_str} {name} (addr={var.addr})")
            elif var.var_type == 'char':
                ch = chr(val & 0xFF) if 32 <= val < 127 else '?'
                print(f"  {type_str} {name} = {val} ('{ch}')")
            else:
                print(f"  {type_str} {name} = {val}")

    def cmd_funcs(self, arg):
        """FUNCS — 顯示函式列表"""
        user_funcs = self.interactive_env.get_all_funcs()
        if user_funcs:
            print("User-defined functions:")
            for name, fdef in user_funcs.items():
                params = ', '.join(
                    p['param_type'] + ('*' if p.get('is_pointer') else '') + ' ' + p['name']
                    for p in fdef['params']
                )
                print(f"  {fdef['return_type']} {name}({params})")

        print("Built-in functions:")
        for name in sorted(self.builtins.keys()):
            print(f"  {name}() [built-in]")

    def cmd_clear(self, arg):
        """CLEAR — 清除終端畫面"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def cmd_quit(self, arg):
        """QUIT/EXIT — 離開程式"""
        print("Goodbye!")
        sys.exit(0)

    # ========== 互動模式：直接執行 C 語句 ==========

    def execute_interactive(self, line):
        """在互動模式直接執行 C 語句，支援大括號配對的多行輸入"""
        accumulated = line
        open_braces = line.count('{') - line.count('}')

        while open_braces > 0:
            try:
                more = input("  > ")
            except EOFError:
                break
            accumulated += '\n' + more
            open_braces += more.count('{') - more.count('}')

        try:
            source = preprocess_defines(accumulated)
            tokens = tokenize(source)
            parser = Parser(tokens)
            stmts = parser.parse_statements()

            for stmt in stmts:
                if stmt['type'] == 'func_def':
                    self.interactive_env.declare_func(stmt['name'], stmt)
                else:
                    self.interactive_interp.exec_statement(stmt)

        except SyntaxError as e:
            print(f"Syntax error: {e}")
        except RuntimeError as e:
            print(f"{e}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    repl = SmallCREPL()
    repl.run()
