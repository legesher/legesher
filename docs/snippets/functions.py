def fibonacci(count):
    values = [0, 1]
    while len(values) < count:
        values.append(values[-1] + values[-2])
    return values[:count]


print(fibonacci(8))
