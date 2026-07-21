def greet(name):
    try:
        print("Hello, " + name)
    except TypeError:
        print("Please pass a string")


greet("world")
