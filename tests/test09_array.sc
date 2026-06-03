// test09: 陣列操作（初始化、遍歷、排序）
void bubble_sort(int arr[], int n) {
    int i = 0;
    while (i < n - 1) {
        int j = 0;
        while (j < n - 1 - i) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
            j += 1;
        }
        i += 1;
    }
}

int main() {
    int arr[5];
    arr[0] = 42;
    arr[1] = 17;
    arr[2] = 93;
    arr[3] = 5;
    arr[4] = 68;

    printf("Before sort: ");
    for (int i = 0; i < 5; i += 1) {
        printf("%d ", arr[i]);
    }
    printf("\n");

    bubble_sort(arr, 5);

    printf("After sort:  ");
    for (int i = 0; i < 5; i += 1) {
        printf("%d ", arr[i]);
    }
    printf("\n");

    // 計算陣列總和
    int sum = 0;
    for (int i = 0; i < 5; i += 1) {
        sum += arr[i];
    }
    printf("Sum = %d\n", sum);

    return 0;
}
