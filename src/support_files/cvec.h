#ifndef C_VEC_H
#define C_VEC_H

#include <stdlib.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif
typedef struct {
    void * data;
    uint32_t width;
    uint32_t capacity;
    uint32_t size;
} cvec;

void cvec_init(cvec * p, uint32_t size, size_t width);
void cvec_cleanup(cvec * p);

cvec * cvec_create(uint32_t size, size_t width);
void cvec_delete(cvec *);
int cvec_get(cvec * p, uint32_t index, void * res);
int cvec_append(cvec *p, void * val);
int cvec_set(cvec * p, uint32_t index, void* val);
int cvec_resize(cvec *p, uint32_t size);
uint32_t cvec_next_pwr_of_two(size_t start);


#ifdef __cplusplus
} // extern "C"
#endif
#endif
