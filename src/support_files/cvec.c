#include "cvec.h"
#include <string.h> // memcpy

#define DEBUG_CVEC 0
#define GROWTH_FACTOR 4

size_t cvec_next_pwr_of_two(size_t start)
{
    size_t power = 1;
    while(power <= start)
        power*=2;
    return power;
}

cvec * cvec_create(size_t size, size_t width)
{
    cvec * ret = (cvec *) malloc(sizeof(cvec));
    ret->size = size;
    ret->capacity = cvec_next_pwr_of_two(size);
    // always start with at least some capacity
    if (ret->capacity < 4)
    {
        ret->capacity = 4;
    }
    ret->width = width;
    ret->data = (void *) malloc( ret->capacity*width );
    memset((char*)(ret->data), 0, ret->capacity*width);
    return ret;
}

int cvec_get(cvec * p, size_t index, void * res )
{
    if (index+1 > p->size)
    {
        if (DEBUG_CVEC) printf("ERROR 2: index out of bounds\n");
        return 1;
    }
    else
    {
        memcpy( (char*) res, ((char*) (p->data)) + index*(p->width), 
                p->width);
    }
    return 0;

}

int cvec_set(cvec * p, size_t index, void * val)
{
    if (index+1 > p->size)
    {
        if (DEBUG_CVEC) printf("ERROR 1: index out of bounds\n");
        return 1;
    }
    else
    {
        memcpy( ((char*) (p->data)) + index*(p->width), 
                (char*) val, p->width);
    }
    return 0;
}

int cvec_append(cvec * p, void *val)
{
    if (p->size >= p->capacity)
    {
        if (DEBUG_CVEC) printf("RESIZE OPERATION\n");
        // 1. create a new vector
        size_t new_size = p->capacity*GROWTH_FACTOR;
        void * buf = (void*) malloc (new_size*p->width);
        // 2. memcpy
        memcpy(buf, p->data, p->width*p->size);
        p->capacity = new_size;

        // 3. free the old one
        free(p->data);
        p->data = buf;
        
    }

    memcpy( ((char*) (p->data)) + (p->size)*(p->width), 
            (char*) val, p->width);
    p->size++;
    return 0;
}

int cvec_resize(cvec *p, size_t size)
{
    size_t new_capacity = cvec_next_pwr_of_two(size);
    void * buf = (void*) malloc (new_capacity*p->width);
    memcpy(buf, p->data, p->width*size);
    p->capacity = new_capacity;

    // 3. free the old one
    free(p->data);
    p->data = buf;
    p->size = size;
    if (DEBUG_CVEC) printf("new size = %lu:%lu\n", p->size, p->capacity);
    return 0;
}

void cvec_delete(cvec * p)
{
    // Clear the data array
    if (NULL != p->data)
    {
        free(p->data);
    }
    // Clear the main pointer
    if (NULL != p)
    {
        free(p);    
    }
}
