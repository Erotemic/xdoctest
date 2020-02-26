cmake_minimum_required(VERSION 3.5.0)

project(my_ext)


# Fetch pybind11
include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11
  GIT_TAG v2.4.3
)
FetchContent_GetProperties(pybind11)
if(NOT pybind11_POPULATED)
  FetchContent_Populate(pybind11)
  add_subdirectory(${pybind11_SOURCE_DIR} ${pybind11_BINARY_DIR})
endif()
#find_package(pybind11 REQUIRED)

find_package(PythonExtensions REQUIRED)

#pybind11_add_module(my_ext my_ext.cxx)

add_library(my_ext MODULE my_ext.cxx)
#set_property(TARGET my_ext PROPERTY POSITION_INDEPENDENT_CODE ON)
python_extension_module(my_ext)

install(TARGETS my_ext LIBRARY DESTINATION .)
