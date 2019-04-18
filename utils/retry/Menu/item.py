class Item:
    def __init__(self, name, function, *args):
        self.name = name
        self.function = function
        self.args = args
        #self.args = args lets keep this way for now

    def execute(self):
        if self.function and self.args:
            return self.function(*self.args)
        else:
            return self.function()

    def draw(self):
        print("    " + self.name)