/* Mini-C Test Program */
int x;
float y = 10.5;
int list[10];

int main() {
    int a = 5;
    int b = 3;
    float result;

    a = a + b * 2;
    result = y + 1.5;

    if (a > b) {
        print(a);
    } else {
        print(b);
    }

    int i = 0;
    while (i < 10) {
        list[i] = i * 2;
        i = i + 1;
    }

    for (int k = 0; k < 5; k = k + 1) {
        print(k);
    }

    int c = a + b;
    if (c == 8) {
        print(result);
    }

    return 0;
}
