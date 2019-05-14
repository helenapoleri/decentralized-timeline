import asyncio
import inspect


class MenuItem:
    def __init__(self, name, function, *args):
        self.name = name
        self.function = function
        self.args = args

    def run(self):
        loop = asyncio.get_event_loop()
        if self.args and inspect.iscoroutinefunction(self.function):
            future = asyncio.run_coroutine_threadsafe(
                self.function(*self.args),
                loop)
            return future.result()
        elif inspect.iscoroutinefunction(self.function):
            future = asyncio.run_coroutine_threadsafe(self.function(), loop)
            return future.result()
        elif self.args:
            return self.function(*self.args)
        else:
            return self.function()

    def get_name(self):
        return self.name
