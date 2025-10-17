#ifndef LINKED_LIST_H
#define LINKED_LIST_H

#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

/*
 * A generic singly linked list implementation tailored for working with a
 * "current" pointer. The list always maintains a dummy head node to simplify
 * insertions and deletions at the front of the list.
 */
typedef struct ListNode {
    void *data;
    struct ListNode *next;
} ListNode;

typedef struct SinglyList {
    ListNode *head;     /* Dummy head node */
    ListNode *current;  /* Points to the logical current node */
    ListNode *previous; /* Points to the node before current */
    size_t length;      /* Number of data nodes in the list */
} SinglyList;

/*
 * Initializes the singly linked list (with a dummy head node).
 */
static inline void list_init(SinglyList *list) {
    if (list == NULL) {
        return;
    }
    list->head = (ListNode *)malloc(sizeof(ListNode));
    if (!list->head) {
        perror("Failed to allocate head node");
        exit(EXIT_FAILURE);
    }
    list->head->data = NULL;
    list->head->next = NULL;
    list->current = list->head;
    list->previous = NULL;
    list->length = 0;
}

/*
 * Resets the current pointer to the first data node (if any).
 */
static inline void list_move_to_first(SinglyList *list) {
    if (!list) {
        return;
    }
    list->previous = list->head;
    list->current = list->head->next;
}

/*
 * Advances the current pointer to the next node.
 */
static inline void list_move_next(SinglyList *list) {
    if (!list || !list->current) {
        return;
    }
    list->previous = list->current;
    list->current = list->current->next;
}

/*
 * Inserts a new node after the current node.
 * After insertion the current pointer references the new node.
 */
static inline bool list_insert_after_current(SinglyList *list, void *data) {
    if (!list || !list->current) {
        return false;
    }
    ListNode *node = (ListNode *)malloc(sizeof(ListNode));
    if (!node) {
        perror("Failed to allocate list node");
        return false;
    }
    node->data = data;
    node->next = list->current->next;
    list->current->next = node;
    list->previous = list->current;
    list->current = node;
    list->length++;
    return true;
}

/*
 * Deletes the current node. After deletion the current pointer references the
 * next node (or NULL if none).
 */
static inline bool list_delete_current(SinglyList *list, void (*free_data)(void *)) {
    if (!list || !list->current || list->current == list->head) {
        return false;
    }
    if (!list->previous) {
        /* When current is the first data node and previous is not yet set. */
        list->previous = list->head;
        while (list->previous && list->previous->next != list->current) {
            list->previous = list->previous->next;
        }
    }
    if (!list->previous) {
        return false;
    }
    ListNode *to_delete = list->current;
    list->previous->next = list->current->next;
    list->current = list->current->next;
    if (free_data) {
        free_data(to_delete->data);
    }
    free(to_delete);
    list->length--;
    return true;
}

/*
 * Outputs the list elements using the supplied print function and prints the
 * total length of the list.
 */
static inline void list_print(const SinglyList *list, void (*print_data)(const void *)) {
    if (!list) {
        return;
    }
    size_t count = 0;
    ListNode *node = list->head->next;
    while (node) {
        if (print_data) {
            print_data(node->data);
        }
        node = node->next;
        count++;
    }
    printf("Total nodes: %zu\n", count);
}

/*
 * Returns true if the list is empty.
 */
static inline bool list_is_empty(const SinglyList *list) {
    if (!list) {
        return true;
    }
    return list->head->next == NULL;
}

/*
 * Releases every node in the list, calling the provided free function for each
 * stored data pointer.
 */
static inline void list_clear(SinglyList *list, void (*free_data)(void *)) {
    if (!list) {
        return;
    }
    ListNode *node = list->head->next;
    while (node) {
        ListNode *next = node->next;
        if (free_data) {
            free_data(node->data);
        }
        free(node);
        node = next;
    }
    list->head->next = NULL;
    list->current = list->head;
    list->previous = NULL;
    list->length = 0;
}

/*
 * Destroys the list completely.
 */
static inline void list_destroy(SinglyList *list, void (*free_data)(void *)) {
    if (!list) {
        return;
    }
    list_clear(list, free_data);
    free(list->head);
    list->head = NULL;
    list->current = NULL;
    list->previous = NULL;
}

#endif /* LINKED_LIST_H */
