//
// Created by emilio on 29/01/20.
//

#ifndef LEVEL_CLIENT_UDP_MY_QUEUE_H
#define LEVEL_CLIENT_UDP_MY_QUEUE_H

#include <stdio.h>
#include <stdlib.h>

// A linked list (LL) node to store a queue entry
struct QNode {
    int data;
    struct QNode *next;
};

// The queue, front stores the front node of LL and rear stores the last node of LL
struct MyQueue {
    struct QNode *front, *rear;
};

// A utility function to create a new linked list node.
struct QNode *new_node(int data);

// A utility function to create an empty queue
struct MyQueue *create_queue();

// The function to add a data k to q
void enQueue(struct MyQueue *q, int k);

// Function to remove a key from given queue q
int deQueue(struct MyQueue *q);

// Function to print queue
void printQueue(struct MyQueue *q);

// Delete specific key
int delete_node(struct MyQueue *q, int key);

// Get First mex
int get_front_mex(struct MyQueue *q);

// Empty Queue
int empty_queue(struct MyQueue *q);

#endif //LEVEL_CLIENT_UDP_MY_QUEUE_H
