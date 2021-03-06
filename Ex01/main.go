package main

import (
    . "fmt"
    "runtime"
    "time"
)

var i = 0

func someGoroutine() {

	for j := 0; j < 1000000; j++{
		i++
	}

    Println("Hello from goroutine 1!")
}

func someGoroutine2() {

	for j := 0; j < 1000000; j++{
			i--
		}

    Println("Hello from goroutine 2!")
}

func main() {
    runtime.GOMAXPROCS(runtime.NumCPU())    // I guess this is a hint to what GOMAXPROCS does...
                                            // Try doing the exercise both with and without it!
    go someGoroutine()                      // This spawns someGoroutine() as a goroutine
	go someGoroutine2()
    // We have no way to wait for the completion of a goroutine (without additional syncronization of some sort)
    // We'll come back to using channels in Exercise 2. For now: Sleep.
    time.Sleep(1000*time.Millisecond)

    Println("Hello from main!")
	Printf("%d",i)

}