"""
lexer.py — 詞法分析器
將 Small-C 原始碼切成 token 串列
例如 "int x = 10;" → [KEYWORD:int, IDENT:x, OP:=, INT_LIT:10, PUNCT:;]
"""

import re


class Token:
    """一個詞法單元"""
    def __init__(self, type, value, line=0):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, line={self.line})'


# Token 類型常數
INT_LIT   = 'INT_LIT'
CHAR_LIT  = 'CHAR_LIT'
STR_LIT   = 'STR_LIT'
IDENT     = 'IDENT'
KEYWORD   = 'KEYWORD'
OP        = 'OP'
PUNCT     = 'PUNCT'
EOF       = 'EOF'

KEYWORDS = {
    'int', 'char', 'void',
    'if', 'else',
    'while', 'for', 'do',
    'break', 'continue', 'return'
}

# 兩字元運算子要先檢查，避免被拆成兩個單字元
TWO_CHAR_OPS = {
    '==', '!=', '<=', '>=',
    '&&', '||',
    '<<', '>>',
    '+=', '-=', '*=', '/=', '%='
}

ONE_CHAR_OPS = set('+-*/%=<>!&|^~')
PUNCTUATIONS = set(';{}()[],:')

ESCAPE_CHARS = {
    'n': '\n', 't': '\t', '\\': '\\',
    "'": "'", '"': '"', '0': '\0',
    'r': '\r', 'a': '\a', 'b': '\b'
}


def preprocess_defines(source):
    """
    預處理 #define 常數定義
    只支援簡單常數替換，不支援巨集函式
    """
    defines = {}
    lines = source.split('\n')
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#define'):
            parts = stripped.split(None, 2)
            if len(parts) >= 3:
                defines[parts[1]] = parts[2]
            # 用空行取代以保持行號正確
            new_lines.append('')
        else:
            new_lines.append(line)

    result = '\n'.join(new_lines)
    for name, value in defines.items():
        # \b 確保只替換完整單字，不會誤換如 SIZE2 中的 SIZE
        result = re.sub(r'\b' + re.escape(name) + r'\b', value, result)

    return result


def tokenize(source):
    """
    將原始碼轉換成 token 串列
    回傳 Token 物件的 list，最後一個是 EOF token
    """
    tokens = []
    i = 0
    line = 1
    length = len(source)

    while i < length:
        ch = source[i]

        # 空白
        if ch in ' \t\r':
            i += 1
            continue

        # 換行
        if ch == '\n':
            line += 1
            i += 1
            continue

        # 單行註解 //
        if ch == '/' and i + 1 < length and source[i + 1] == '/':
            i += 2
            while i < length and source[i] != '\n':
                i += 1
            continue

        # 區塊註解 /* ... */
        if ch == '/' and i + 1 < length and source[i + 1] == '*':
            i += 2
            while i + 1 < length:
                if source[i] == '*' and source[i + 1] == '/':
                    break
                if source[i] == '\n':
                    line += 1
                i += 1
            i += 2
            continue

        # 數字常數（十六進位或十進位）
        if ch.isdigit():
            start = i
            if ch == '0' and i + 1 < length and source[i + 1] in 'xX':
                i += 2
                while i < length and source[i] in '0123456789abcdefABCDEF':
                    i += 1
                tokens.append(Token(INT_LIT, int(source[start:i], 16), line))
            else:
                while i < length and source[i].isdigit():
                    i += 1
                tokens.append(Token(INT_LIT, int(source[start:i]), line))
            continue

        # 字元常數
        if ch == "'":
            i += 1
            if i < length and source[i] == '\\':
                i += 1
                esc_ch = source[i] if i < length else '?'
                char_val = ord(ESCAPE_CHARS.get(esc_ch, esc_ch))
                i += 1
            elif i < length:
                char_val = ord(source[i])
                i += 1
            else:
                char_val = 0
            if i < length and source[i] == "'":
                i += 1
            tokens.append(Token(CHAR_LIT, char_val, line))
            continue

        # 字串常數
        if ch == '"':
            i += 1
            s = ''
            while i < length and source[i] != '"':
                if source[i] == '\\' and i + 1 < length:
                    i += 1
                    s += ESCAPE_CHARS.get(source[i], source[i])
                else:
                    if source[i] == '\n':
                        line += 1
                    s += source[i]
                i += 1
            if i < length:
                i += 1
            tokens.append(Token(STR_LIT, s, line))
            continue

        # 識別字或關鍵字
        if ch.isalpha() or ch == '_':
            start = i
            while i < length and (source[i].isalnum() or source[i] == '_'):
                i += 1
            word = source[start:i]
            if word in KEYWORDS:
                tokens.append(Token(KEYWORD, word, line))
            else:
                tokens.append(Token(IDENT, word, line))
            continue

        # 兩字元運算子（優先檢查）
        if i + 1 < length and source[i:i+2] in TWO_CHAR_OPS:
            tokens.append(Token(OP, source[i:i+2], line))
            i += 2
            continue

        # 單字元運算子
        if ch in ONE_CHAR_OPS:
            tokens.append(Token(OP, ch, line))
            i += 1
            continue

        # 標點符號
        if ch in PUNCTUATIONS:
            tokens.append(Token(PUNCT, ch, line))
            i += 1
            continue

        raise SyntaxError(f"Unexpected character '{ch}' at line {line}")

    tokens.append(Token(EOF, None, line))
    return tokens
