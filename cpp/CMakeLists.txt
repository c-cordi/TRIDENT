cmake_minimum_required(VERSION 3.18)
project(_trident LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Make pybind11 use CMake's FindPython results
set(PYBIND11_FINDPYTHON NEW CACHE STRING "Use CMake's FindPython" FORCE)

# Find Python 3.11 or higher (instead of EXACT 3.11)
find_package(Python3 3.11 REQUIRED
             COMPONENTS Interpreter Development.Module NumPy)

message(STATUS "Using Python3: ${Python3_EXECUTABLE}")
message(STATUS "Python version: ${Python3_VERSION}")
if (Python3_NumPy_FOUND)
  message(STATUS "NumPy include: ${Python3_NumPy_INCLUDE_DIRS}")
endif()

# pybind11
add_subdirectory(extern/pybind11)

pybind11_add_module(_trident MODULE trident.cpp)

if (Python3_NumPy_FOUND)
  target_include_directories(_trident PRIVATE ${Python3_NumPy_INCLUDE_DIRS})
endif()

if (MSVC)
  target_compile_options(_trident PRIVATE /bigobj)
  set_target_properties(_trident PROPERTIES MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
endif()

set(ADDON_DIR "${CMAKE_SOURCE_DIR}/../trident_extension")
set_target_properties(_trident PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY  "${ADDON_DIR}/bin"
  LIBRARY_OUTPUT_DIRECTORY  "${ADDON_DIR}/bin"
  ARCHIVE_OUTPUT_DIRECTORY  "${ADDON_DIR}/bin"
  RUNTIME_OUTPUT_DIRECTORY_RELEASE "${ADDON_DIR}/bin"
  LIBRARY_OUTPUT_DIRECTORY_RELEASE "${ADDON_DIR}/bin"
  ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${ADDON_DIR}/bin"
  RUNTIME_OUTPUT_DIRECTORY_DEBUG "${ADDON_DIR}/bin"
  LIBRARY_OUTPUT_DIRECTORY_DEBUG "${ADDON_DIR}/bin"
  ARCHIVE_OUTPUT_DIRECTORY_DEBUG "${ADDON_DIR}/bin"
)

execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"
  OUTPUT_VARIABLE EXT_SUFFIX
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
message(STATUS "Python EXT_SUFFIX: ${EXT_SUFFIX}")