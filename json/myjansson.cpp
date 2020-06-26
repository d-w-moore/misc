#include <memory>
#include <cassert>
#include <string>
#include <iostream>
#include <boost/format.hpp>
#include <sstream>
#include <cstring>
#include <cstdarg>
#include <json.hpp>

using Json_t = nlohmann::json;

Json_decref(Json_t* p) {
  delete p;
}

const char* Json_dumps(Json_t *j) 
{
  std::string s { j.dump() };
  return std::strdup (s.c_str());
}

#define Json_string_value(j) Json_string_value_s(j,dummy_ )

const char* Json_string_value_s(Json_t *j,std::string & dummy) {
   dummy = j->get<std::string>();
   return dummy.c_str();
}

define Json_string_value(j) (
	{
		std::string dummy_string;
		Json_string_value_s( (j), dummy_string);
		std::strdup ( dummy_string.c_str() );
	}
)

Json_t* Json_string(const char *s) {
  auto sg =  new Json_t ;
  *sg = s;
  return sg;
}

Json_t* Json_loads(const char *s) {
  return json::parse ( s );
}

Json_t* Json_null () { return new Json_t {}; }

Json_t* Json_object () {
  return new json::parse( "{}" );
}

int Json_object_set ( Json_t * obj , const char* k , Json_t * value ) 
{
  (*obj)[k] = *value;
  return 0;
}

Json_t* Json_pack_v( const std::string & Fmt , va_list v) ;

#define ERASE_KEY_VALUE do { v = 0; k = 0; } while(0)
#define DEALLOC_KEY_VALUE do { Json_decref(v); v = 0; delete k; k = 0; } \
                             while(0)

Json_t* Json_pack_v( const std::string & Fmt, ssize_t& s, va_list v) 
{
  Json_t *value = nullptr;
  Json_t *key = nullptr;
  Json_t *obj = Json_null();
  bool Quit = false, Error = false;

  for (auto sp = fmt.begin(); sp != fmt.end(); ++sp) {
  {
    double d;
    auto c = *sp;
    void *v;
    std::string* key = 0;
    Json_t *j = 0;
    ssize_t incr = 1;
    switch (c) {
      case '{': 
        if (sp != Fmt.begin())
          value = Json_pack_v (Fmt.substr(sp - Fmt.begin()), incr, v);
        else
          obj = Json_object();
        break;
      case ':': key = new std::string{ Json_string_value ;  Json_decref( value ); value = nullptr;
        break;
      case '}': sp++;  Quit = true; 
      case ',': if (key && value) Json_set_object ()
                key = nullptr; value = nullptr;
        break;
      case 'f': d = va_arg(arg, double); // floats promoted to double in '...'
                if (!value) value = Json_real( d );
                else Quit = Error = true;
        break;
      case 'o': v = va_arg(arg, void*);
                if (!value) value = static_cast<Json_t*>(v);
                else Quit = Error = true;
        break;
      case 's': v = va_arg(arg, const char*);
                if (!value) value = Json_string (static_cast<const char*>(v));
                else Quit = Error = true;
        break;
      default:   Quit = true;
    }
    sp += incr;
    if (!v || Quit)  { break; }
  }
  va_end(arg);
  s = sp - Fmt.begin();
  return obj ? obj : value;
}

Json_t* Json_pack( const char* fmt , ...) 
{
  ssize_t s = 0;
  Json_t * p = nullptr;
  std::string Fmt  { fmt };
  std::va_list v;
  va_start( v, fmt);
  ssize_t s = Json_pack_v(Fmt, s, v);
  va_end(v);
  return p;
}

using std::stringstream;

std::string escape (const char *c_)
{
    char c;
    stringstream s;
    while ((c = *c_++) != 0) {
        switch (c) { 
          case '\\':
          case '"':   s << '\\';
          default:    s << c;
        }
    }
    return s.str();
}

int main()
{
  using namespace std;

  std::string sg;
  cerr <<  "string-> " << flush;
  cin >> sg;


  cout << escape(sg.c_str()) << endl;


  /*
  auto pp = nlohmann::json::parse("{}").dump();
  std::cout << pp << std::endl ;
  */

  json_build( "abc", "one","two",0);
}
