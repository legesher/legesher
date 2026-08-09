class Animal:
    def __init__(self, name, sound):
        self.name = name
        self.sound = sound

    def speak(self):
        return self.name + " says " + self.sound


class Dog(Animal):
    def __init__(self, name):
        super().__init__(name, "woof")


print(Animal("Cat", "meow").speak())
print(Dog("Rex").speak())
