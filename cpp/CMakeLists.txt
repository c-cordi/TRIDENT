cmake_minimum_required(VERSION 3.18)
project(trident LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Make pybind11 use CMake's FindPython results
set(PYBIND11_FINDPYTHON NEW CACHE STRING "Use CMake's FindPython" FORCE)

# Pick EXACTLY Python 3.10 and its dev/module bits (+ NumPy if you need it)
find_package(Python3 3.10 EXACT REQUIRED
             COMPONENTS Interpreter Development.Module NumPy)

message(STATUS "Using Python3: ${Python3_EXECUTABLE}")
if (Python3_NumPy_FOUND)
  message(STATUS "NumPy include: ${Python3_NumPy_INCLUDE_DIRS}")
endif()

# Now bring in pybind11 (it will reuse the Python we just found)
add_subdirectory(extern/pybind11)

pybind11_add_module(trident MODULE trident.cpp)

# If you use NumPy C-API:
if (Python3_NumPy_FOUND)
  target_include_directories(trident PRIVATE ${Python3_NumPy_INCLUDE_DIRS})
endif()

if (MSVC)
  target_compile_options(trident PRIVATE /bigobj)
  set_target_properties(trident PROPERTIES MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
endif()

set(ADDON_DIR "${CMAKE_SOURCE_DIR}/../trident_add-on")
set_target_properties(trident PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY  "${ADDON_DIR}"
  LIBRARY_OUTPUT_DIRECTORY  "${ADDON_DIR}"
  ARCHIVE_OUTPUT_DIRECTORY  "${ADDON_DIR}"
  RUNTIME_OUTPUT_DIRECTORY_RELEASE "${ADDON_DIR}"
  LIBRARY_OUTPUT_DIRECTORY_RELEASE "${ADDON_DIR}"
  ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${ADDON_DIR}"
  RUNTIME_OUTPUT_DIRECTORY_DEBUG "${ADDON_DIR}"
  LIBRARY_OUTPUT_DIRECTORY_DEBUG "${ADDON_DIR}"
  ARCHIVE_OUTPUT_DIRECTORY_DEBUG "${ADDON_DIR}"
)

# (Optional) Show the extension suffix CMake/Python picked (should be .cp310-win_amd64.pyd)
execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"
  OUTPUT_VARIABLE EXT_SUFFIX
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
message(STATUS "Python EXT_SUFFIX: ${EXT_SUFFIX}")
