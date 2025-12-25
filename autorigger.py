from system import test
import importlib

importlib.reload(test)


def run():
    test.test()


if __name__ == "Main":
    run()
