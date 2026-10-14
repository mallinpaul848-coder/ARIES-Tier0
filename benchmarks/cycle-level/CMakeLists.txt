cmake_minimum_required(VERSION 3.16)
project(aries_tier0_benchmark LANGUAGES CXX)

if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux" OR NOT CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
  message(FATAL_ERROR "ARIES cycle benchmark currently supports Linux x86_64 only.")
endif()

add_executable(aries_benchmark aries_tier0_benchmark.cpp)
target_compile_features(aries_benchmark PRIVATE cxx_std_17)
target_compile_options(aries_benchmark PRIVATE -O3 -Wall -Wextra -Wpedantic)
target_link_libraries(aries_benchmark PRIVATE pthread)
