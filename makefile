build: main.o
	gcc -o main main.o

main.o: main.c
	gcc -o main.o -c main.c
