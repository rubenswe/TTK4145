
#include <pthread.h>
#include <stdio.h>

int i = 0;
pthread_mutex_t mutex;

void* someThreadFunction(){

    int j;

    for (j = 0; j < 1000000; ++j)
    {
        pthread_mutex_lock(&mutex);
        ++i;
        pthread_mutex_unlock(&mutex);
    }

    printf("Hello from thread 1!\n");
    return NULL;
}

void* someThreadFunction2(){

    int j;

    for (j = 0; j < 1000000; ++j)
    {
        pthread_mutex_lock(&mutex);
        --i;
        pthread_mutex_unlock(&mutex);
    }

    printf("Hello from thread2!\n");
    return NULL;
}



int main()
{

    pthread_t someThread;
    pthread_t someThread2;

    pthread_mutex_init(&mutex, NULL);

    pthread_create(&someThread, NULL, someThreadFunction, NULL);
    pthread_create(&someThread2, NULL, someThreadFunction2, NULL);

    pthread_join(someThread, NULL);
    pthread_join(someThread2, NULL);

    pthread_mutex_destroy(&mutex);

    printf("i = %d\n", i);

    return 0;
}
