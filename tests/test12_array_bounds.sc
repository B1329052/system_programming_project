// test12: 錯誤處理 — 陣列越界存取
int main() {
    int arr[3];
    arr[0] = 10;
    arr[1] = 20;
    arr[2] = 30;
    int val = arr[5];
    printf("should not reach here\n");
    return 0;
}
