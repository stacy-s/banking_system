import sqlite3
import random


class NotEnoughMoneyError(Exception):
    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NotExistAccountError(Exception):
    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return repr(self.value)


class LunhAlgorithmError(Exception):
    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SameAccountError(Exception):
    def __init__(self, previous, next, message):
        self.previous = previous
        self.next = next
        self.message = message




class Cards:
    max_account_number = int(10e10) - 1

    class __Card:
        iin = '400000'
        account_number_len = 9

        def __init__(self, id=None, card_number=None, pin=None, balance=None, max_id=None):
            args = [id, card_number, pin, balance]
            args = [x is not None for x in args]
            if any(args) and not all(args):
                raise ValueError(f'All the parameters must be None or have not None value.')
            if not id:
                if max_id is None or max_id < -1:
                    raise ValueError(f'If you create a new card, max_id dont have to be equal to {max_id}')
                self.id = Cards.generate_account_number(max_id)
                self.card_number = self.make_card_number()
                self.pin = self.generate_pin()
                self.balance = 0
            else:
                self.id = id
                self.card_number = card_number
                self.pin = pin
                self.balance = balance

        def generate_pin(self):
            return ''.join([str(random.randint(0, 9)) for _ in range(4)])

        @classmethod
        def last_digit(cls, card_number):
            numbers = [int(x) for x in card_number]
            for i in range(len(numbers)):
                if i % 2 == 0:
                    numbers[i] *= 2
                if numbers[i] > 9:
                    numbers[i] -= 9
            return str((10 - (sum(numbers) % 10)) % 10)

        def make_card_number(self):
            account_number = str(self.id)
            account_number = '0' * (self.account_number_len - len(account_number)) + account_number
            card_number = self.iin + account_number
            return card_number + self.last_digit(card_number)

        @classmethod
        def is_lunh(cls, card_number):
            return ord(card_number[-1]) == ord(cls.last_digit(card_number[:-1])[-1])

    def __init__(self, db_name, table_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()
        self.table_name = table_name

    def create_or_open_table(self):
        self.cur.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name} (id INT, number VARCHAR(16), pin VARCHAR(4),'
                         f' balance INT DEFAULT 0);')
        self.conn.commit()

    def get_max_id(self):
        self.cur.execute(f"""SELECT MAX(SUBSTR(number, 6, 10)) FROM {self.table_name};""")
        max_number = self.cur.fetchone()
        if max_number[0] is not None:
            return int(max_number[0])
        else:
            return -1

    @classmethod
    def generate_account_number(cls, max_id):
        max_number = max_id
        if max_number >= Cards.max_account_number:
            raise StopIteration('There are no free card numbers.')
        return max_number + 1

    def add_card(self):
        card = Cards.__Card(max_id=self.get_max_id())
        self.cur.execute(f"""INSERT INTO card(id, number, pin) 
                                    VALUES ({card.id}, {card.card_number}, {card.pin});""")
        self.conn.commit()
        return card

    def get_card(self, card_number, pin):
        self.cur.execute(f'SELECT * FROM {self.table_name} WHERE number = {card_number} AND pin = {pin}')
        card_info = self.cur.fetchone()
        if not card_info:
            return None
        return Cards.__Card(id=card_info[0], card_number=card_info[1], pin=card_info[2], balance=card_info[3])

    def find_card(self, card_number):
        self.cur.execute(f'SELECT * FROM {self.table_name} WHERE number = {card_number}')
        card_info = self.cur.fetchone()
        if card_info is None:
            return None
        return Cards.__Card(id=card_info[0], card_number=card_info[1], pin=card_info[2], balance=card_info[3])

    def get_balance(self, card):
        self.cur.execute(f'SELECT balance FROM {self.table_name} WHERE id={card.id}')
        return self.cur.fetchone()[0]

    def remove_card(self):
        pass

    def add_income(self, card, income):
        self.cur.execute(f'UPDATE {self.table_name} SET balance=balance+{income} WHERE id={card.id};')
        self.conn.commit()

    def do_correct_transfer(self, card, transfer_card_number, transfer_amount=None):
        balance = self.get_balance(card)
        if not self.__Card.is_lunh(transfer_card_number):
            raise LunhAlgorithmError
        if card.card_number == transfer_card_number:
            raise SameAccountError
        transfer_card = self.find_card(transfer_card_number)
        if transfer_card is None:
            raise NotExistAccountError
        if transfer_amount is None:
            return True
        if balance < transfer_amount:
            raise NotEnoughMoneyError
        self.add_income(transfer_card, transfer_amount)
        self.add_income(card, -transfer_amount)
        return True

    def close_account(self, card):
        self.cur.execute(f'DELETE FROM {self.table_name} WHERE id={card.id}')
        self.conn.commit()

    def __del__(self):
        self.conn.close()


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
        card = kwargs['cards'].add_card()
        print('Your card has been created')
        print(f'Your card number:\n{card.card_number}')
        print(f'Your card PIN:\n{card.pin}')
        return True

    @classmethod
    def login(cls, **kwargs):
        def run_personal_interface(obj_account):
            cards = kwargs['cards']
            command_names = ['Exit',
                             'Balance',
                             'Add income',
                             'Do transfer',
                             'Close account',
                             'Log out']
            command_functions = [Command.exit,
                                 Command.balance,
                                 Command.add_income,
                                 Command.do_transfer,
                                 Command.close_account,
                                 Command.logout]
            parameter_list = [{},
                              {'obj': obj_account, 'cards': cards},
                              {'obj': obj_account, 'cards': cards},
                              {'obj': obj_account, 'cards': cards},
                              {'obj': obj_account, 'cards': cards},
                              {}]
            personal_interface = Interface(command_names=command_names,
                                           command_functions=command_functions,
                                           parameter_list=parameter_list)
            personal_interface()

        card_number = input('Enter your card number:\n')
        pin = input('Enter your PIN:\n')
        card = kwargs['cards'].get_card(card_number=card_number, pin=pin)
        if card:
            print('You have successfully logged in!')
            run_personal_interface(card)
        else:
            print('Wrong card number or PIN!')
        return True

    @classmethod
    def balance(cls, **kwargs):
        balance = kwargs['cards'].get_balance(card=kwargs['obj'])
        print(balance)
        return True

    @classmethod
    def add_income(cls, **kwargs):
        cards = kwargs['cards']
        income = int(input('Enter income: '))
        cards.add_income(kwargs['obj'], income)
        return True

    @classmethod
    def do_transfer(cls, **kwargs):
        cards = kwargs['cards']
        card = kwargs['obj']
        print('Transfer')
        transfer_card_number = input('Enter card number: ')
        try:
            cards.do_correct_transfer(card, transfer_card_number)
            amount = int(input('Enter how much money you want to transfer: '))
            cards.do_correct_transfer(card, transfer_card_number, amount)
        except NotEnoughMoneyError:
            print('Not enough money!')
            return True
        except LunhAlgorithmError:
            print('Probably you made a mistake in the card number. Please try again!')
            return True
        except SameAccountError:
            print('You can\'t transfer money to the same account!')
            return True
        except NotExistAccountError:
            print('Such a card does not exist.')
            return True
        print('Success!')
        return True

    @classmethod
    def close_account(cls, **kwargs):
        cards = kwargs['cards']
        card = kwargs['obj']
        cards.close_account(card)
        print('The account has been closed!')
        return False

    @classmethod
    def logout(cls, **kwargs):
        print('You have successfully logged out!')
        return False


def run():
    cards = Cards('card.s3db', 'card')
    cards.create_or_open_table()
    command_names = ['Exit', 'Create an account', 'Log into account']
    command_functions = [Command.exit, Command.create_account, Command.login]
    common_helper = Interface(command_names=command_names,
                              command_functions=command_functions,
                              parameter_list=[{}, {'cards': cards}, {'cards': cards}])
    common_helper()


def main():
    run()


if __name__ == '__main__':
    main()
