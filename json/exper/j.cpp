#include <iostream>
#include <string>
#include <json.hpp>

int main()
{
  using nlohmann::json;
  json t = "helo";
  std::string s ;
  std::cout <<  s.size() << " ";
  s = t    ;
  std::cout <<  s.size() << " ";
}
