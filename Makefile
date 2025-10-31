CXX := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -pedantic -Iinclude
LDFLAGS :=

SRC := $(wildcard src/*.cpp)
OBJ := $(SRC:.cpp=.o)
TARGET := dictionary_app

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
