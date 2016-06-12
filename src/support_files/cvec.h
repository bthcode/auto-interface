#ifndef C_VEC_H
#define C_VEC_H

#include <stdlib.h>
#include <stdio.h>

typedef struct {
    void * data;
    size_t width;
    size_t capacity;
    size_t size;
} cvec;

cvec * cvec_create(size_t size, size_t width);
void cvec_delete(cvec *);
int cvec_get(cvec * p, size_t index, void * res);
int cvec_append(cvec *p, void * val);
int cvec_set(cvec * p, size_t index, void* val);


#endif
