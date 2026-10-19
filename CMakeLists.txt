cmake_minimum_required(VERSION 3.20)
project(AriesAIGateway LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(ARIES_ENABLE_AVX512 "Compile the optional AVX-512 path (requires compatible CPU at runtime)" OFF)

add_executable(aries_gateway src/main.cpp)
target_include_directories(aries_gateway PRIVATE include)

if(MSVC)
  target_compile_options(aries_gateway PRIVATE /O2 /W4)
else()
  target_compile_options(aries_gateway PRIVATE -O3 -Wall -Wextra -Wpedantic)
  if(ARIES_ENABLE_AVX512)
    target_compile_options(aries_gateway PRIVATE -mavx512f)
  endif()
endif()
