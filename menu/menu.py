class Menu:
    def __init__(self, name):
        self.name = name
        self.items = []
        self.option = -1

    def append_item(self, item):
        self.items.append(item)
    
    def print_menu(self):
        nr = int((79 - len(self.name) - 2)/2)
        if (nr * 2 + len(self.name) + 2) != 79:
            print("=" * nr + " " + self.name + " " + "=" * (nr + 1))
        else:
            print("=" * nr + " " + self.name + " " + "=" * nr)
        option = 1
        for item in self.items:
            spaces = 79 - 6 - len(str(option)) - len(item.get_name())
            print("| " + str(option) + ": " + item.get_name() + spaces * " " + " |")
            option += 1
        
        print("=" * 79)

    def execute(self):
        while(self.option == -1):
            self.print_menu()
            self.read_option()

            if self.option != -1 and self.option <= len(self.items):
                op = self.option
                self.option = -1
                return self.items[op - 1].run()


    def read_option(self):
        option = input("> ")
        if int(option) <= 0 or int(option) > len(self.items):
            self.option = -1
            print("Escolhida opção inválida!")
        else:
            self.option = int(option)
