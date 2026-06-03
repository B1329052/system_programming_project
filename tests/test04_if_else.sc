// test04: if / else if / else 控制結構
int main() {
    int score = 85;

    if (score >= 90) {
        printf("Grade: A\n");
    } else if (score >= 80) {
        printf("Grade: B\n");
    } else if (score >= 70) {
        printf("Grade: C\n");
    } else {
        printf("Grade: F\n");
    }

    int x = 10;
    int y = 20;
    if (x < y) {
        printf("%d < %d\n", x, y);
    }
    if (x == y) {
        printf("equal\n");
    } else {
        printf("not equal\n");
    }

    return 0;
}
