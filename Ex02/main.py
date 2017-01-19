from threading import Thread, Lock

i = 0
lock = Lock()

def someThreadFunction():
    global i

    print("Hello from thread 1!")

    for j in range(1000000):
        lock.acquire()
        ++i
        lock.release()

def someThreadFunction2():
    global i

    print("Hello from thread 2!")

    for j in range(1000000):
        lock.acquire()
        --i
        lock.release()


def main():
    someThread = Thread(target = someThreadFunction, args = (),)
    someThread2 = Thread(target = someThreadFunction2, args = (),)

    someThread.start()
    someThread2.start()

    someThread.join()
    someThread2.join()

    print("Hello from main!")
    print(i)


main()