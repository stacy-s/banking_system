import random


def generate_account_number():
    for num in range(Card.max_account_number + 1):
        yield num
    raise StopIteration('There are no free card numbers.')


class Card:
    list = []
    iin = '400000'
    account_number_len = 9
    max_account_number = int(10e10) - 1
    account_number_generator = generate_account_number()

    def __init__(self):
        self.card_number = self.make_card_number()
        self.pin = self.generate_pin()
        self.balance = 0
        Card.list.append(self)

    def generate_pin(self):
        return ''.join([str(random.randint(0, 9)) for _ in range(4)])

    def make_card_number(self):
        def last_digit(card_number):
            numbers = [int(x) for x in card_number]
            for i in range(len(numbers)):
                if i % 2 == 0:
                    numbers[i] *= 2
                if numbers[i] > 9:
                    numbers[i] -= 9
            return str((10 - (sum(numbers) % 10)) % 10)

        account_number = str(next(Card.account_number_generator))
        account_number = '0' * (Card.account_number_len - len(account_number)) + account_number
        card_number = Card.iin + account_number
        return card_number + last_digit(card_number)

    @classmethod
    def find_card(cls, card_number, pin):
        for x in Card.list:
            if x.card_number == card_number and x.pin == pin:
                return x


class Interface:
    def __init__(self, command_names, command_functions, parameter_list):
        self.command_names = command_names
        self.command_functions = command_functions
        self.parameter_list = parameter_list
        if len(self.command_names) != len(self.command_functions) != len(self.parameter_list):
            raise ValueError('Lists of command names and command functions must be the same length.')

    def __call__(self):
        is_next = True
        while is_next:
            for i, message in enumerate(self.command_names):
                print(f'{i}. {message}')
            command = int(input())
            is_next = self.command_functions[command](**self.parameter_list[command])


class Command:
    @classmethod
    def exit(cls, **kwargs):
        print('Bye!')
        exit(0)
        return False

    @classmethod
    def create_account(cls, **kwargs):
        card = Card()
        print('Your card has been created')
        print(f'Your card number:\n{card.card_number}')
        print(f'Your card PIN:\n{card.pin}')
        return True

    @classmethod
    def login(cls, **kwargs):
        def run_personal_interface(obj_account):
            command_names = ['Exit', 'Balance', 'Log out']
            command_functions = [Command.exit, Command.balance, Command.logout]
            parameter_list = [{}, {'obj': obj}, {}]
            personal_interface = Interface(command_names=command_names,
                                           command_functions=command_functions,
                                           parameter_list=parameter_list)
            personal_interface()

        card_number = input('Enter your card number:\n')
        pin = input('Enter your PIN:\n')
        obj = Card.find_card(card_number=card_number, pin=pin)
        if obj:
            print('You have successfully logged in!')
            run_personal_interface(obj)
        else:
            print('Wrong card number or PIN!')
        return True

    @classmethod
    def balance(cls, **kwargs):
        print(kwargs['obj'].balance)
        return True

    @classmethod
    def logout(cls, **kwargs):
        print('You have successfully logged out!')
        return False


def run():
    command_names = ['Exit', 'Create an account', 'Log into account']
    command_functions = [Command.exit, Command.create_account, Command.login]
    common_helper = Interface(command_names=command_names,
                              command_functions=command_functions,
                              parameter_list=[{} for _ in range(len(command_functions))])
    common_helper()


def main():
    run()


if __name__ == '__main__':
    main()