#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "linked_list.h"

typedef struct Employee {
    int number;
    char name[50];
    int department;
    double salary;
} Employee;

static Employee *create_employee(int number, const char *name, int department, double salary) {
    Employee *emp = (Employee *)malloc(sizeof(Employee));
    if (!emp) {
        perror("Failed to allocate employee");
        exit(EXIT_FAILURE);
    }
    emp->number = number;
    strncpy(emp->name, name, sizeof(emp->name) - 1);
    emp->name[sizeof(emp->name) - 1] = '\0';
    emp->department = department;
    emp->salary = salary;
    return emp;
}

static void free_employee(void *data) {
    free(data);
}

static void print_employee(const void *data) {
    const Employee *emp = (const Employee *)data;
    printf("No:%d\tName:%s\tDept:%d\tSalary:%.2f\n", emp->number, emp->name, emp->department, emp->salary);
}

static ListNode *find_previous_by_number(SinglyList *list, int number) {
    if (!list) {
        return NULL;
    }
    ListNode *prev = list->head;
    while (prev->next) {
        Employee *emp = (Employee *)prev->next->data;
        if (emp->number == number) {
            return prev;
        }
        prev = prev->next;
    }
    return NULL;
}

static void add_employee_record(SinglyList *list) {
    int number, department;
    double salary;
    char name[50];

    printf("Enter employee number: ");
    if (scanf("%d", &number) != 1) {
        fprintf(stderr, "Invalid number.\n");
        return;
    }
    printf("Enter employee name: ");
    if (scanf("%49s", name) != 1) {
        fprintf(stderr, "Invalid name.\n");
        return;
    }
    printf("Enter department number: ");
    if (scanf("%d", &department) != 1) {
        fprintf(stderr, "Invalid department.\n");
        return;
    }
    printf("Enter salary: ");
    if (scanf("%lf", &salary) != 1) {
        fprintf(stderr, "Invalid salary.\n");
        return;
    }

    Employee *emp = create_employee(number, name, department, salary);
    ListNode *tail = list->head;
    while (tail->next) {
        tail = tail->next;
    }
    list->current = tail;
    list_insert_after_current(list, emp);
    printf("Employee added successfully.\n");
}

static void display_all_records(SinglyList *list) {
    if (list_is_empty(list)) {
        printf("No records to display.\n");
        return;
    }
    list_print(list, print_employee);
}

static void display_by_department(SinglyList *list) {
    int dep;
    printf("Enter department number: ");
    if (scanf("%d", &dep) != 1) {
        fprintf(stderr, "Invalid department number.\n");
        return;
    }
    ListNode *node = list->head->next;
    size_t count = 0;
    while (node) {
        Employee *emp = (Employee *)node->data;
        if (emp->department == dep) {
            print_employee(emp);
            count++;
        }
        node = node->next;
    }
    if (count == 0) {
        printf("No records found for department %d.\n", dep);
    }
}

static void delete_by_number(SinglyList *list) {
    int number;
    printf("Enter employee number to delete: ");
    if (scanf("%d", &number) != 1) {
        fprintf(stderr, "Invalid number.\n");
        return;
    }
    ListNode *prev = find_previous_by_number(list, number);
    if (!prev) {
        printf("Employee %d not found.\n", number);
        return;
    }
    list->previous = prev;
    list->current = prev->next;
    list_delete_current(list, free_employee);
    printf("Employee deleted.\n");
}

static void delete_all_records(SinglyList *list) {
    list_clear(list, free_employee);
    printf("All records deleted.\n");
}

static void find_by_exact_name(SinglyList *list) {
    char name[50];
    printf("Enter exact name to search: ");
    if (scanf("%49s", name) != 1) {
        fprintf(stderr, "Invalid name.\n");
        return;
    }
    ListNode *node = list->head->next;
    size_t count = 0;
    while (node) {
        Employee *emp = (Employee *)node->data;
        if (strcmp(emp->name, name) == 0) {
            print_employee(emp);
            count++;
        }
        node = node->next;
    }
    if (count == 0) {
        printf("No employee found with name %s.\n", name);
    }
}

static void find_by_partial_name(SinglyList *list) {
    char pattern[50];
    printf("Enter name pattern: ");
    if (scanf("%49s", pattern) != 1) {
        fprintf(stderr, "Invalid input.\n");
        return;
    }
    ListNode *node = list->head->next;
    size_t count = 0;
    while (node) {
        Employee *emp = (Employee *)node->data;
        if (strstr(emp->name, pattern)) {
            print_employee(emp);
            count++;
        }
        node = node->next;
    }
    if (count == 0) {
        printf("No employee names matched pattern %s.\n", pattern);
    }
}

static void find_by_salary_range(SinglyList *list) {
    double lower, upper;
    printf("Enter salary lower bound: ");
    if (scanf("%lf", &lower) != 1) {
        fprintf(stderr, "Invalid lower bound.\n");
        return;
    }
    printf("Enter salary upper bound: ");
    if (scanf("%lf", &upper) != 1 || upper < lower) {
        fprintf(stderr, "Invalid upper bound.\n");
        return;
    }
    ListNode *node = list->head->next;
    size_t count = 0;
    while (node) {
        Employee *emp = (Employee *)node->data;
        if (emp->salary >= lower && emp->salary <= upper) {
            print_employee(emp);
            count++;
        }
        node = node->next;
    }
    if (count == 0) {
        printf("No employees found in salary range %.2f - %.2f.\n", lower, upper);
    }
}

static SinglyList create_sorted_by_salary(SinglyList *list) {
    SinglyList sorted;
    list_init(&sorted);
    ListNode *node = list->head->next;
    while (node) {
        Employee *original = (Employee *)node->data;
        Employee *copy = create_employee(original->number, original->name, original->department, original->salary);
        ListNode *prev = sorted.head;
        while (prev->next) {
            Employee *emp = (Employee *)prev->next->data;
            if (copy->salary < emp->salary) {
                break;
            }
            prev = prev->next;
        }
        sorted.current = prev;
        list_insert_after_current(&sorted, copy);
        node = node->next;
    }
    return sorted;
}

static void print_menu(void) {
    printf("\nHospital Employee Management System\n");
    printf("1. Add employee record\n");
    printf("2. Display all records\n");
    printf("3. Display records by department\n");
    printf("4. Delete record by employee number\n");
    printf("5. Delete all records\n");
    printf("6. Find employee by exact name\n");
    printf("7. Find employees by name pattern\n");
    printf("8. Find employees by salary range\n");
    printf("9. Display employees sorted by salary\n");
    printf("0. Exit\n");
    printf("Select an option: ");
}

int main(void) {
    SinglyList employees;
    list_init(&employees);

    int choice;
    do {
        print_menu();
        if (scanf("%d", &choice) != 1) {
            fprintf(stderr, "Invalid choice.\n");
            break;
        }
        switch (choice) {
            case 1:
                add_employee_record(&employees);
                break;
            case 2:
                display_all_records(&employees);
                break;
            case 3:
                display_by_department(&employees);
                break;
            case 4:
                delete_by_number(&employees);
                break;
            case 5:
                delete_all_records(&employees);
                break;
            case 6:
                find_by_exact_name(&employees);
                break;
            case 7:
                find_by_partial_name(&employees);
                break;
            case 8:
                find_by_salary_range(&employees);
                break;
            case 9: {
                SinglyList sorted = create_sorted_by_salary(&employees);
                if (list_is_empty(&sorted)) {
                    printf("No records to sort.\n");
                } else {
                    printf("Employees sorted by salary (ascending):\n");
                    list_print(&sorted, print_employee);
                }
                list_destroy(&sorted, free_employee);
                break;
            }
            case 0:
                printf("Exiting...\n");
                break;
            default:
                printf("Unknown option. Try again.\n");
                break;
        }
    } while (choice != 0);

    list_destroy(&employees, free_employee);
    return 0;
}
