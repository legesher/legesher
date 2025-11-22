#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple test script in English to verify basic Python execution.

This script can be executed with:
    $ legesher run test_script_en.py --lang en
    $ python test_script_en.py
"""


def greet(name):
    """Simple greeting function."""
    message = f"Hello, {name}!"
    print(message)
    return message


def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    total = 0
    for number in numbers:
        total = total + number
    return total


def main():
    """Main program function."""
    print("=== Test Program in English ===")
    print()

    # Greeting
    greet("World")
    print()

    # Calculate sum
    numbers = [1, 2, 3, 4, 5]
    print(f"Numbers: {numbers}")
    total = calculate_sum(numbers)
    print(f"Total sum: {total}")
    print()

    # Conditionals
    if total > 10:
        print("The sum is greater than 10")
    else:
        print("The sum is 10 or less")
    print()

    # Loop
    print("Counting from 1 to 5:")
    for i in range(1, 6):
        print(f"  {i}")
    print()

    print("=== Program completed successfully ===")


# Run the program
if __name__ == "__main__":
    main()
