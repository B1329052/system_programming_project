"""
test_all.py — 自動測試腳本
測試 Small-C 解譯器的各項功能
"""

import sys
import io
from lexer import tokenize, preprocess_defines
from parser import Parser
from interpreter import Interpreter
from environment import Memory, Environment
from smallc_builtins import get_all_builtins


def run_statements(source):
    """執行一段 Small-C 程式碼，回傳標準輸出"""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        source = preprocess_defines(source)
        tokens = tokenize(source)
        parser = Parser(tokens)
        stmts = parser.parse_statements()

        memory = Memory()
        env = Environment()
        builtins = get_all_builtins()
        interp = Interpreter(memory=memory, global_env=env, builtins_funcs=builtins)

        for stmt in stmts:
            if stmt['type'] == 'func_def':
                env.declare_func(stmt['name'], stmt)
            else:
                interp.exec_statement(stmt)

        output = sys.stdout.getvalue()
    except Exception as e:
        output = f"ERROR: {e}"
    finally:
        sys.stdout = old_stdout

    return output


def run_program(source):
    """執行一段有 main() 的完整程式，回傳 (輸出, return_value)"""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        source = preprocess_defines(source)
        tokens = tokenize(source)
        parser = Parser(tokens)
        program = parser.parse_program()

        memory = Memory()
        env = Environment()
        builtins = get_all_builtins()
        interp = Interpreter(memory=memory, global_env=env, builtins_funcs=builtins)

        interp.exec_program(program)
        ret = interp.run_main()

        output = sys.stdout.getvalue()
        return output, ret
    except Exception as e:
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return output + f"ERROR: {e}", -1
    finally:
        sys.stdout = old_stdout


def test(name, actual, expected):
    """比較實際輸出與預期"""
    actual = actual.strip()
    expected = expected.strip()
    if actual == expected:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name}")
        print(f"    Expected: {expected!r}")
        print(f"    Actual:   {actual!r}")


# ====== 測試 1：基本算術 ======
print("=== Test 1: Basic Arithmetic ===")
out = run_statements("""
printf("%d\\n", 3 + 4 * 5 - 2);
printf("%d\\n", (3 + 4) * (5 - 2));
printf("%d\\n", 100 / 7);
printf("%d\\n", 100 % 7);
printf("%d\\n", -15 / 4);
""")
test("arithmetic", out, "21\n21\n14\n2\n-3")

# ====== 測試 2：關係、邏輯、位元運算 ======
print("\n=== Test 2: Relational, Logical, Bitwise ===")
out = run_statements("""
printf("%d %d %d\\n", 10 > 5, 10 < 5, 10 == 10);
printf("%d %d\\n", 10 > 5 && 3 < 1, 10 > 5 || 3 < 1);
printf("%d\\n", 0xAB & 0x0F);
printf("%d\\n", 1 << 10);
printf("0x%x\\n", 0xF0 | 0x0D);
""")
test("relational/logical/bitwise", out, "1 0 1\n0 1\n11\n1024\n0xfd")

# ====== 測試 3：變數、字元、內建函式 ======
print("\n=== Test 3: Variables, Chars, Builtins ===")
out = run_statements("""
int x = 25;
int y = -18;
printf("abs(%d) = %d\\n", y, abs(y));
printf("max=%d, min=%d\\n", max(x, 30), min(x, 30));
printf("pow(2,16) = %d\\n", pow(2, 16));
printf("sqrt(625) = %d\\n", sqrt(625));
char ch = 'Z';
printf("ch=%c, code=%d, next=%c\\n", ch, ch, ch + 1);
""")
test("vars/chars/builtins", out,
     'abs(-18) = 18\nmax=30, min=25\npow(2,16) = 65536\nsqrt(625) = 25\nch=Z, code=90, next=[')

# ====== 測試 4：字串函式 ======
print("\n=== Test 4: String Functions ===")
out = run_statements("""
char buf[50];
strcpy(buf, "System");
strcat(buf, " Software");
printf("buf=\\"%s\\", len=%d\\n", buf, strlen(buf));
printf("atoi=%d\\n", atoi("2026"));
char numstr[20];
itoa(12345, numstr);
printf("itoa result: %s\\n", numstr);
""")
# strcmp test separately (just needs to be negative)
out2 = run_statements('printf("%d\\n", strcmp("apple", "banana"));')
cmp_val = int(out2.strip())

test("string functions", out,
     'buf="System Software", len=15\natoi=2026\nitoa result: 12345')
test("strcmp negative", "ok" if cmp_val < 0 else "fail", "ok")

# ====== 測試 5：完整 Selection Sort 程式 ======
print("\n=== Test 5: Selection Sort Program ===")
selection_sort_code = """
#define SIZE 8

void swap(int *a, int *b) {
    int temp;
    temp = *a;
    *a = *b;
    *b = temp;
}

void selection_sort(int *arr, int n) {
    int i;
    int j;
    int min_idx;
    for (i = 0; i < n - 1; i = i + 1) {
        min_idx = i;
        for (j = i + 1; j < n; j = j + 1) {
            if (arr[j] < arr[min_idx]) {
                min_idx = j;
            }
        }
        if (min_idx != i) {
            swap(&arr[i], &arr[min_idx]);
        }
    }
}

int compute_sum(int *arr, int n) {
    int i;
    int total = 0;
    for (i = 0; i < n; i = i + 1) {
        total += arr[i];
    }
    return total;
}

int find_max(int *arr, int n) {
    int i;
    int m = arr[0];
    for (i = 1; i < n; i = i + 1) {
        m = max(m, arr[i]);
    }
    return m;
}

int find_min(int *arr, int n) {
    int i;
    int m = arr[0];
    for (i = 1; i < n; i = i + 1) {
        m = min(m, arr[i]);
    }
    return m;
}

int main() {
    int data[SIZE];
    int i;
    int total;

    data[0] = 64; data[1] = 25; data[2] = 12; data[3] = 22;
    data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 33;

    printf("Original: ");
    for (i = 0; i < SIZE; i = i + 1) {
        printf("%d ", data[i]);
    }
    printf("\\n");

    printf("Max = %d\\n", find_max(data, SIZE));
    printf("Min = %d\\n", find_min(data, SIZE));

    total = compute_sum(data, SIZE);
    printf("Sum = %d\\n", total);
    printf("Avg = %d\\n", total / SIZE);

    selection_sort(data, SIZE);

    printf("Sorted:   ");
    for (i = 0; i < SIZE; i = i + 1) {
        printf("%d ", data[i]);
    }
    printf("\\n");

    return 0;
}
"""
out, ret = run_program(selection_sort_code)
expected = """Original: 64 25 12 22 11 90 45 33 
Max = 90
Min = 11
Sum = 302
Avg = 37
Sorted:   11 12 22 25 33 45 64 90 """
test("selection sort output", out, expected)
test("selection sort return value", str(ret), "0")

print("\n=== All tests done ===")
