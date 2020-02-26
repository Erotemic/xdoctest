#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/embed.h>
#include <string>

namespace py = pybind11;

namespace my_ext {

class MyClass
{
  public:

    std::string hello_from_cpp() const { return "Hello CPP"; };

};

PYBIND11_MODULE(my_ext, m)
{
  m.attr("my_global_var") = 42;

  py::class_<MyClass > (m, "MyClass", R"(
    A simple pybind11 class with a doctest

    Example:
        >>> self = MyClass()
        >>> print(self.hello_from_cpp())
        >>> print(self.hello_from_python())
    )")

    .def(py::init<>())

    .def("hello_from_cpp", &MyClass::hello_from_cpp)

    .def("hello_from_python", [](MyClass& self) -> std::string {
        auto locals = py::dict(py::arg("self")=self);
        py::exec(R"(
        retval = 'Hello World'
        )", py::globals(), locals);
        return locals["retval"].cast<std::string>();
      })
    ;
}

}
