"""
parser.py — 語法分析器
使用遞迴下降法將 token 串列解析成 AST（以 dict 表示）
"""

from lexer import Token, INT_LIT, CHAR_LIT, STR_LIT, IDENT, KEYWORD, OP, PUNCT, EOF


class Parser:
    """遞迴下降語法分析器"""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[0]

    # ---------- 基本工具方法 ----------

    def advance(self):
        """前進到下一個 token"""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        return self.current

    def peek(self, offset=1):
        """偷看後面第 offset 個 token"""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(EOF, None, 0)

    def expect(self, type, value=None):
        """檢查目前 token 是否符合預期，符合就前進，否則丟出語法錯誤"""
        if self.current.type != type:
            raise SyntaxError(
                f"Expected {type} but got {self.current.type} "
                f"'{self.current.value}' at line {self.current.line}")
        if value is not None and self.current.value != value:
            raise SyntaxError(
                f"Expected '{value}' but got '{self.current.value}' "
                f"at line {self.current.line}")
        tok = self.current
        self.advance()
        return tok

    def match(self, type, value=None):
        """如果目前 token 符合就前進並回傳 True，否則回傳 False"""
        if self.current.type == type and (value is None or self.current.value == value):
            self.advance()
            return True
        return False

    def is_type_keyword(self):
        """判斷目前 token 是否為型別關鍵字"""
        return (self.current.type == KEYWORD and
                self.current.value in ('int', 'char', 'void'))

    # ========== 頂層解析 ==========

    def parse_program(self):
        """program → (func_def | var_decl)*"""
        declarations = []
        while self.current.type != EOF:
            decl = self.parse_top_level()
            if decl:
                declarations.append(decl)
        return {'type': 'program', 'declarations': declarations}

    def parse_top_level(self):
        """解析頂層宣告：讀型別和名稱，再依 '(' 判斷是函式或變數"""
        if not self.is_type_keyword():
            raise SyntaxError(
                f"Expected type keyword at line {self.current.line}, "
                f"got '{self.current.value}'")

        ret_type = self.current.value
        self.advance()

        is_pointer = False
        if self.current.type == OP and self.current.value == '*':
            is_pointer = True
            self.advance()

        name = self.expect(IDENT).value

        if self.current.type == PUNCT and self.current.value == '(':
            return self.parse_func_def(ret_type, name)

        return self.parse_var_decl_rest(ret_type, name, is_pointer)

    def parse_func_def(self, ret_type, name):
        """func_def → type name '(' params ')' block"""
        line = self.current.line
        self.expect(PUNCT, '(')
        params = self.parse_params()
        self.expect(PUNCT, ')')
        body = self.parse_block()
        return {
            'type': 'func_def',
            'return_type': ret_type,
            'name': name,
            'params': params,
            'body': body,
            'line': line
        }

    def parse_params(self):
        """params → param (',' param)* | ε"""
        params = []
        if self.current.type == PUNCT and self.current.value == ')':
            return params

        while True:
            p = self.parse_one_param()
            params.append(p)
            if not self.match(PUNCT, ','):
                break
        return params

    def parse_one_param(self):
        """解析單一參數"""
        if not self.is_type_keyword():
            raise SyntaxError(f"Expected type in parameter at line {self.current.line}")
        ptype = self.current.value
        self.advance()

        is_pointer = False
        if self.current.type == OP and self.current.value == '*':
            is_pointer = True
            self.advance()

        pname = self.expect(IDENT).value

        # 陣列參數 int arr[] 視為指標
        is_array_param = False
        if self.current.type == PUNCT and self.current.value == '[':
            self.advance()
            self.expect(PUNCT, ']')
            is_array_param = True

        return {
            'name': pname,
            'param_type': ptype,
            'is_pointer': is_pointer or is_array_param
        }

    # ========== 語句解析 ==========

    def parse_statement(self):
        """根據目前 token 分派到對應的語句解析方法"""
        if self.current.type == PUNCT and self.current.value == '{':
            return self.parse_block()

        if self.current.type == KEYWORD:
            kw = self.current.value

            if kw in ('int', 'char', 'void'):
                return self.parse_var_decl()
            if kw == 'if':
                return self.parse_if()
            if kw == 'while':
                return self.parse_while()
            if kw == 'for':
                return self.parse_for()
            if kw == 'do':
                return self.parse_do_while()
            if kw == 'return':
                return self.parse_return()
            if kw == 'break':
                self.advance()
                self.expect(PUNCT, ';')
                return {'type': 'break', 'line': self.tokens[self.pos - 2].line}
            if kw == 'continue':
                self.advance()
                self.expect(PUNCT, ';')
                return {'type': 'continue', 'line': self.tokens[self.pos - 2].line}

        return self.parse_expr_stmt()

    def parse_block(self):
        """解析區塊 { statement* }"""
        line = self.current.line
        self.expect(PUNCT, '{')
        stmts = []
        while not (self.current.type == PUNCT and self.current.value == '}'):
            if self.current.type == EOF:
                raise SyntaxError("Unexpected end of input, missing '}'")
            stmts.append(self.parse_statement())
        self.expect(PUNCT, '}')
        return {'type': 'block', 'body': stmts, 'line': line}

    def parse_var_decl(self):
        """var_decl → type ('*')? name ('[' size ']')? ('=' expr)? ';'"""
        vtype = self.current.value
        self.advance()

        is_pointer = False
        if self.current.type == OP and self.current.value == '*':
            is_pointer = True
            self.advance()

        name = self.expect(IDENT).value
        return self.parse_var_decl_rest(vtype, name, is_pointer)

    def parse_var_decl_rest(self, vtype, name, is_pointer):
        """解析變數宣告名稱之後的部分（陣列大小、初始值）"""
        line = self.current.line

        array_size = None
        if self.current.type == PUNCT and self.current.value == '[':
            self.advance()
            array_size = self.expect(INT_LIT).value
            self.expect(PUNCT, ']')

        init = None
        if self.current.type == OP and self.current.value == '=':
            self.advance()
            init = self.parse_expression()

        self.expect(PUNCT, ';')
        return {
            'type': 'var_decl',
            'var_type': vtype,
            'name': name,
            'is_pointer': is_pointer,
            'array_size': array_size,
            'init': init,
            'line': line
        }

    def parse_if(self):
        """解析 if / else"""
        line = self.current.line
        self.expect(KEYWORD, 'if')
        self.expect(PUNCT, '(')
        cond = self.parse_expression()
        self.expect(PUNCT, ')')
        then_body = self.parse_statement()

        else_body = None
        if self.current.type == KEYWORD and self.current.value == 'else':
            self.advance()
            else_body = self.parse_statement()

        return {
            'type': 'if', 'condition': cond,
            'then_body': then_body, 'else_body': else_body,
            'line': line
        }

    def parse_while(self):
        """解析 while 迴圈"""
        line = self.current.line
        self.expect(KEYWORD, 'while')
        self.expect(PUNCT, '(')
        cond = self.parse_expression()
        self.expect(PUNCT, ')')
        body = self.parse_statement()
        return {
            'type': 'while', 'condition': cond, 'body': body,
            'line': line
        }

    def parse_for(self):
        """解析 for(init; condition; update) body"""
        line = self.current.line
        self.expect(KEYWORD, 'for')
        self.expect(PUNCT, '(')

        # init 可能是宣告、表達式、或空的
        if self.current.type == PUNCT and self.current.value == ';':
            init = None
            self.advance()
        elif self.is_type_keyword():
            init = self.parse_var_decl()
        else:
            init_expr = self.parse_expression()
            self.expect(PUNCT, ';')
            init = {'type': 'expr_stmt', 'expr': init_expr, 'line': line}

        if self.current.type == PUNCT and self.current.value == ';':
            cond = None
            self.advance()
        else:
            cond = self.parse_expression()
            self.expect(PUNCT, ';')

        if self.current.type == PUNCT and self.current.value == ')':
            update = None
        else:
            update = self.parse_expression()

        self.expect(PUNCT, ')')
        body = self.parse_statement()

        return {
            'type': 'for', 'init': init, 'condition': cond,
            'update': update, 'body': body, 'line': line
        }

    def parse_do_while(self):
        """解析 do-while 迴圈"""
        line = self.current.line
        self.expect(KEYWORD, 'do')
        body = self.parse_statement()
        self.expect(KEYWORD, 'while')
        self.expect(PUNCT, '(')
        cond = self.parse_expression()
        self.expect(PUNCT, ')')
        self.expect(PUNCT, ';')
        return {
            'type': 'do_while', 'body': body, 'condition': cond,
            'line': line
        }

    def parse_return(self):
        """解析 return 語句"""
        line = self.current.line
        self.expect(KEYWORD, 'return')
        value = None
        if not (self.current.type == PUNCT and self.current.value == ';'):
            value = self.parse_expression()
        self.expect(PUNCT, ';')
        return {'type': 'return', 'value': value, 'line': line}

    def parse_expr_stmt(self):
        """解析表達式語句"""
        line = self.current.line
        expr = self.parse_expression()
        self.expect(PUNCT, ';')
        return {'type': 'expr_stmt', 'expr': expr, 'line': line}

    # ========== 表達式解析（按優先順序由低到高）==========

    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        """指定運算（右結合）"""
        left = self.parse_logical_or()

        assign_ops = ('=', '+=', '-=', '*=', '/=', '%=')
        if self.current.type == OP and self.current.value in assign_ops:
            op = self.current.value
            line = self.current.line
            self.advance()
            right = self.parse_assignment()
            return {
                'type': 'assign', 'op': op,
                'target': left, 'value': right, 'line': line
            }
        return left

    def parse_logical_or(self):
        left = self.parse_logical_and()
        while self.current.type == OP and self.current.value == '||':
            self.advance()
            right = self.parse_logical_and()
            left = {'type': 'binary_op', 'op': '||', 'left': left, 'right': right}
        return left

    def parse_logical_and(self):
        left = self.parse_bitwise_or()
        while self.current.type == OP and self.current.value == '&&':
            self.advance()
            right = self.parse_bitwise_or()
            left = {'type': 'binary_op', 'op': '&&', 'left': left, 'right': right}
        return left

    def parse_bitwise_or(self):
        left = self.parse_bitwise_xor()
        while self.current.type == OP and self.current.value == '|':
            self.advance()
            right = self.parse_bitwise_xor()
            left = {'type': 'binary_op', 'op': '|', 'left': left, 'right': right}
        return left

    def parse_bitwise_xor(self):
        left = self.parse_bitwise_and()
        while self.current.type == OP and self.current.value == '^':
            self.advance()
            right = self.parse_bitwise_and()
            left = {'type': 'binary_op', 'op': '^', 'left': left, 'right': right}
        return left

    def parse_bitwise_and(self):
        left = self.parse_equality()
        while self.current.type == OP and self.current.value == '&':
            self.advance()
            right = self.parse_equality()
            left = {'type': 'binary_op', 'op': '&', 'left': left, 'right': right}
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.current.type == OP and self.current.value in ('==', '!='):
            op = self.current.value
            self.advance()
            right = self.parse_relational()
            left = {'type': 'binary_op', 'op': op, 'left': left, 'right': right}
        return left

    def parse_relational(self):
        left = self.parse_shift()
        while self.current.type == OP and self.current.value in ('<', '<=', '>', '>='):
            op = self.current.value
            self.advance()
            right = self.parse_shift()
            left = {'type': 'binary_op', 'op': op, 'left': left, 'right': right}
        return left

    def parse_shift(self):
        left = self.parse_additive()
        while self.current.type == OP and self.current.value in ('<<', '>>'):
            op = self.current.value
            self.advance()
            right = self.parse_additive()
            left = {'type': 'binary_op', 'op': op, 'left': left, 'right': right}
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.current.type == OP and self.current.value in ('+', '-'):
            op = self.current.value
            self.advance()
            right = self.parse_multiplicative()
            left = {'type': 'binary_op', 'op': op, 'left': left, 'right': right}
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.current.type == OP and self.current.value in ('*', '/', '%'):
            op = self.current.value
            self.advance()
            right = self.parse_unary()
            left = {'type': 'binary_op', 'op': op, 'left': left, 'right': right}
        return left

    def parse_unary(self):
        """一元運算：+x, -x, !x, &x(取址), *p(解參照)"""
        if self.current.type == OP and self.current.value in ('+', '-', '!'):
            op = self.current.value
            self.advance()
            operand = self.parse_unary()
            return {'type': 'unary_op', 'op': op, 'operand': operand}

        if self.current.type == OP and self.current.value == '&':
            self.advance()
            operand = self.parse_unary()
            return {'type': 'addr_of', 'operand': operand}

        if self.current.type == OP and self.current.value == '*':
            self.advance()
            operand = self.parse_unary()
            return {'type': 'deref', 'operand': operand}

        return self.parse_postfix()

    def parse_postfix(self):
        """後綴運算：函式呼叫 func(args)、陣列索引 arr[i]"""
        node = self.parse_primary()

        while True:
            if self.current.type == PUNCT and self.current.value == '(':
                self.advance()
                args = []
                if not (self.current.type == PUNCT and self.current.value == ')'):
                    args.append(self.parse_expression())
                    while self.match(PUNCT, ','):
                        args.append(self.parse_expression())
                self.expect(PUNCT, ')')
                node = {'type': 'call', 'func': node, 'args': args}

            elif self.current.type == PUNCT and self.current.value == '[':
                self.advance()
                index = self.parse_expression()
                self.expect(PUNCT, ']')
                node = {'type': 'index', 'array': node, 'index': index}

            else:
                break

        return node

    def parse_primary(self):
        """基本元素：數字、字元、字串、識別字、括號"""
        tok = self.current

        if tok.type == INT_LIT:
            self.advance()
            return {'type': 'int_literal', 'value': tok.value, 'line': tok.line}

        if tok.type == CHAR_LIT:
            self.advance()
            return {'type': 'int_literal', 'value': tok.value, 'line': tok.line}

        if tok.type == STR_LIT:
            self.advance()
            return {'type': 'string_literal', 'value': tok.value, 'line': tok.line}

        if tok.type == IDENT:
            self.advance()
            return {'type': 'identifier', 'name': tok.value, 'line': tok.line}

        if tok.type == KEYWORD and tok.value in ('int', 'char', 'void'):
            raise SyntaxError(
                f"Unexpected keyword '{tok.value}' in expression "
                f"at line {tok.line}")

        if tok.type == PUNCT and tok.value == '(':
            self.advance()
            expr = self.parse_expression()
            self.expect(PUNCT, ')')
            return expr

        raise SyntaxError(
            f"Unexpected token '{tok.value}' at line {tok.line}")

    # ========== 互動模式用 ==========

    def parse_single_statement(self):
        """解析單一語句"""
        return self.parse_statement()

    def parse_statements(self):
        """解析多個語句直到 EOF"""
        stmts = []
        while self.current.type != EOF:
            stmts.append(self.parse_statement())
        return stmts
