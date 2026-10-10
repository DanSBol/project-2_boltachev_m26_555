import prompt


def welcome():
    name = prompt.string("May I have your name? ")
    print(f"Hello, {name}! Welcome to primitive_db.")

def working(command: str):
    if command == "help":
        print("<command> exit - выйти из программы")
        print("<command> help - справочная информация")
    elif command == "exit":
        return False
    else:
        print(f"Unknown command: {command}. Type 'help' for available commands.")
    return True

def start_working():
    welcome()
    while True:
        command = prompt.string(">> ")
        if not working(command):
            break