cmake_minimum_required(VERSION 3.5.0)

project(my_ext)


function(pycmd outvar cmd)
  execute_process(
    COMMAND "${PYTHON_EXECUTABLE}" -c "${cmd}"
    RESULT_VARIABLE _exitcode
    OUTPUT_VARIABLE _output)
  if(NOT ${_exitcode} EQUAL 0)
    message(ERROR "Failed when running python code: \"\"\"
${cmd}\"\"\"")
    message(FATAL_ERROR "Python command failed with error code: ${_exitcode}")
  endif()
  # Remove supurflous newlines (artifacts of print)
  string(STRIP "${_output}" _output)
  set(${outvar} "${_output}" PARENT_SCOPE)
endfunction()


###
# Find scikit-build and include its cmake resource scripts
#
if (NOT SKBUILD)
  # Find current python major version user option
  find_package(PythonInterp REQUIRED)
  find_package(PythonLibs REQUIRED)
  include_directories(SYSTEM ${PYTHON_INCLUDE_DIR})
  pycmd(skbuild_location "import os, skbuild; print(os.path.dirname(skbuild.__file__))")
  set(skbuild_cmake_dir "${skbuild_location}/resources/cmake")
  # If skbuild is not the driver, then we need to include its utilities in our CMAKE_MODULE_PATH
  list(APPEND CMAKE_MODULE_PATH ${skbuild_cmake_dir})
endif()


message(STATUS "!!! ATTEMPTING FIND PYTHON EXTENSIONS !!!")
find_package(PythonExtensions REQUIRED)


# Fetch pybind11
message(STATUS "!!! ATTEMPTING TO FETCH PYBIND11 CONTENT !!!")
include(FetchContent)

message(STATUS " (1) FetchContent_Declare")
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11
  GIT_TAG v2.4.3
)

# new method for cmake 3.16
#message(STATUS " (2) FetchContent_MakeAvailable")
#FetchContent_MakeAvailable(pybind11)

# old method for cmake < 3.16
message(STATUS " (2) FetchContent_GetProperties")
FetchContent_GetProperties(pybind11)
if(NOT pybind11_POPULATED)
  message(STATUS " (3) FetchContent_Populate")
  FetchContent_Populate(pybind11)
  add_subdirectory(${pybind11_SOURCE_DIR} ${pybind11_BINARY_DIR})
endif()

message(STATUS "pybind11_POPULATED = ${pybind11_POPULATED}")
message(STATUS "pybind11_BINARY_DIR = ${pybind11_BINARY_DIR}")
message(STATUS "pybind11_SOURCE_DIR = ${pybind11_SOURCE_DIR}")

add_library(my_ext MODULE my_ext.cxx)
python_extension_module(my_ext)

# Not sure why I need this on the CI
target_include_directories(my_ext PUBLIC "${pybind11_SOURCE_DIR}/include")
set_property(TARGET my_ext PROPERTY CXX_STANDARD 11)

install(TARGETS my_ext LIBRARY DESTINATION .)
