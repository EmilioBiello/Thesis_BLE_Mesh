//
// Created by emilio on 29/01/20.
//

#include "my_queue.h"

struct QNode *new_node(int key) {
    struct QNode *newNode = (struct QNode *) malloc(sizeof(struct QNode));
    newNode->data = key;
    newNode->next = NULL;
    return newNode;
}

struct MyQueue *create_queue() {
    struct MyQueue *q = (struct MyQueue *) malloc(sizeof(struct MyQueue));
    q->front = q->rear = NULL;
    return q;
}

void enQueue(struct MyQueue *q, int k) {
    // Create a new LL node
    struct QNode *temp = new_node(k);

    // If queue is empty, then new node is front and rear both
    if (q->rear == NULL) {
        q->front = q->rear = temp;
        // printf("FIRST ADD %d\n", k);
        return;
    }

    // Add the new node at the end of queue and change rear
    q->rear->next = temp;
    q->rear = temp;

    // printf("ADD %d\n", k);
}

int deQueue(struct MyQueue *q) {
    // If queue is empty, return NULL.
    if (q->front == NULL) {
        // printf("Empty Queue\n");
        return -1;
    }

    // Store previous front and move front one node ahead
    struct QNode *temp = q->front;
    int result = temp->data;
    free(temp);

    q->front = q->front->next;

    // If front becomes NULL, then change rear also as NULL
    if (q->front == NULL) {
        q->rear = NULL;
    }
    // printf("Remove %d\n", result);
    return result;
}

int delete_node(struct MyQueue *q, int key) {
    // Remove first Node
    if (q->front != NULL && q->front->data == key) {
        int value = deQueue(q);
        return value;
    }

    struct QNode *temp = q->front;
    struct QNode *prev = temp;
    while (temp != NULL && temp->data != key) {
        prev = temp;
        temp = temp->next;
    }

    // Key not present in queue
    if (temp == NULL) {
        // printf("key not present\n");
        return -1;
    }

    // Remove last node
    if (temp->next == NULL) {
        q->rear = prev;
    }

    int value = temp->data;
    prev->next = temp->next;
    free(temp);
    // printf("Remove : %d\n", value);
    return value;
}

int get_front_mex(struct MyQueue *q) {
    if (q->front == NULL)
        return -1;
    return q->front->data;
}

void printQueue(struct MyQueue *q) {
    struct QNode *ptr = q->front;

    int i = 0;
    while (ptr) {
        printf("%d -> ", ptr->data);
        ptr = ptr->next;
        i += 1;
    }
    printf("\nSize Queue: %d\n", i);
}

int empty_queue(struct MyQueue *q) {
    if (q->front == NULL)
        return 0;

    struct QNode *temp;
    int i = 0;
    while (q->front) {
        temp = q->front;
        printf("%d -> ", temp->data);
        q->front = q->front->next;
        free(temp);
        if (q->front == NULL) {
            q->rear = NULL;
        }
        i += 1;
    }

    printf("Empty Queue\n");
    return i;
}
