#include <stdio.h>
#include <jansson.h>

int nref(json_t *o) {return printf("%lu\n",(unsigned long)o->refcount);}

int main()
{
  json_t* p = json_real(3); json_incref(p);
  json_t* o = json_object();
  nref(p);
  json_object_set_new( o, "hello", p);
  nref(p);
  json_decref(o);
}
