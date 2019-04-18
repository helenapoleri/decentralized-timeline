from Menu.item import Item


class Menu:
    def __init__(self, name, items=None):
        self.name = name
        self.items = items or []

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, item):
        self.items.remove(item)

    def draw(self):
        print('_______________ ' + self.name + ' _______________')
        print()
        for item in self.items:
            item.draw()
        print('____________________________________')

    def run(self, option, loop):
        if not option > len(self.items) - 1: 
            return self.items[option-1].execute(loop)

def clear():
    for i in range(50):
        print()