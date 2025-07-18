#!/usr/bin/env python3
"""
Example demonstrating the new CodeBlock functionality with language support.
"""

from theoriq.dialog import CodeBlock


def main():
    # Create a generic code block
    generic_code = CodeBlock.from_code("print('Hello, World!')")
    print("Generic code block:")
    print(f"Block type: {generic_code.block_type}")
    print(f"Language: {generic_code.language}")
    print(f"Code: {generic_code.data.code}")
    print(f"String representation: {generic_code.data.to_str()}")
    print()

    # Create a Python-specific code block
    python_code = CodeBlock.from_python(
        """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
    )
    print("Python code block:")
    print(f"Block type: {python_code.block_type}")
    print(f"Language: {python_code.language}")
    print(f"Code: {python_code.data.code}")
    print(f"String representation: {python_code.data.to_str()}")
    print()

    # Create a JavaScript code block
    js_code = CodeBlock.from_javascript(
        """
function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

console.log(factorial(5));
"""
    )
    print("JavaScript code block:")
    print(f"Block type: {js_code.block_type}")
    print(f"Language: {js_code.language}")
    print(f"Code: {js_code.data.code}")
    print(f"String representation: {js_code.data.to_str()}")
    print()

    # Create a Go code block
    go_code = CodeBlock.from_go(
        """
package main

import "fmt"

func main() {
    fmt.Println("Hello from Go!")
}
"""
    )
    print("Go code block:")
    print(f"Block type: {go_code.block_type}")
    print(f"Language: {go_code.language}")
    print(f"Code: {go_code.data.code}")
    print(f"String representation: {go_code.data.to_str()}")


if __name__ == "__main__":
    main()
