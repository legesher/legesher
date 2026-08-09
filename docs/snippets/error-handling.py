def divide(numerator, denominator):
    try:
        return numerator / denominator
    except ZeroDivisionError:
        print("cannot divide", numerator, "by zero")
        return None
    finally:
        print("attempted", numerator, "/", denominator)


print(divide(10, 2))
print(divide(1, 0))
