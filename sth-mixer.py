# -*- coding: utf-8 -*-
"""
TODO Сделать чтобы каждый раз при запуске скрипта генерировался новый файл с выходными аккаунтами , привязанный к дате.
TODO Прикрутить прогрессбар
TODO Добавить логгирование по отправленным транзакциям
TODO Создать папку для бэкапов где тоже создавать файлы с выходными аккаунтами
TODO Доработать библиотеку писмарт
TODO Проверить что будет если к примеру 2 файла оставить, а 1 удалить и запустить скрипт
TODO Добавить paused.conf если программа оборвется
TODO Для оптимизации выбрать структуру данных байтовый массив вместо списка
"""

import os
import random

from datetime import datetime
from operator import add, sub
from multiprocessing import Process, RLock
from functools import partial
from collections import namedtuple

from libs.pysmart import smartapi
from libs import passwdgenerator
from libs import utils


cfg_data = """privkey:
own_addr:
coins_num_for_sending:
destination_addr:
"""


class CoinMixer(object):
    def __init__(self):
        self.balance = None
        self.net_fee = 10_000_000
        self.num_mix_iters = 3
        self.max_num_processes = 9
        self.smartholdem = smartapi.PySmart()
        self.generator = passwdgenerator.Generator()

        self.files_ways_lst = list(self.get_ways_to_files('sth-mixer.cfg', 'mix_accs', 'output_accs'))
        self.mixer_cfg_path, self.mix_accs_path, self.out_accs_path = self.files_ways_lst

    @staticmethod
    def get_ways_to_files(*args):
        for arg in args:
            yield os.path.join(os.getcwd(), arg)

    @staticmethod
    def files_exists(seq):
        for path in seq:
            if os.path.isfile(path) is False:
                with open(path, 'w') as file:
                    file.write(cfg_data)

    @staticmethod
    def get_data_from_cfg(path_to_cfg):
        with open(path_to_cfg, 'r') as file:
            data_lst = [line.split(':')[1].replace('\n', '') for line in file]

        if any(data_lst) is False:
            raise Exception('Non data in config.')

        return data_lst

    def validate_balance(self, balance):
        if balance < 1000 or balance > 100_000:
            raise Exception(f'Balance must be more than 1000 STH and low than 100,000 STH. Available: {self.balance}')

    def get_balance(self, addr, required_coins_quantity):
        balance = int(self.smartholdem.get_balance(addr)) / 100_000_000
        self.validate_balance(balance)
        self.balance = int(required_coins_quantity) * 100_000_000

    def calculate_addrs_quantity(self, *args):
        """
        :param args: percentage number
        :return:
        """
        return [round((self.balance / 100_000_000) * arg / 100) for arg in args]

    def generate_ratios(self):
        base_mix_ratio = 0.3 + random.uniform(0.01, 0.05)
        base_output_ratio = 0.1 + random.uniform(0.01, 0.05)
        step = 1000
        step *= round(self.balance / step)

        for _ in range(0, self.balance, step):
            base_mix_ratio += 0.01
            base_output_ratio += 0.01

        return base_mix_ratio, base_output_ratio

    @staticmethod
    def split_num_on_parts(quantity_parts, num, max_percentage_shift=50):
        """
        Split number on parts with random shift for each part of number.
        :param num:
        :param quantity_parts:
        :param max_percentage_shift:
        :return:
        """
        avg_val = num / quantity_parts
        operations = (add, sub)
        parts_lst = []

        for i in range(quantity_parts):
            operation = random.choice(operations)
            val2 = avg_val * random.randint(5, max_percentage_shift) / 100
            part = operation(avg_val, val2)
            parts_lst.append(part)

        dif = num - sum(parts_lst)
        avg_val = dif / quantity_parts
        rand_parts_lst = list(map(lambda x: round(x + avg_val), parts_lst))

        dif = num - sum(rand_parts_lst)
        rand_parts_lst[random.randint(0, quantity_parts - 1)] += dif

        return rand_parts_lst

    @staticmethod
    def write_account_creds(file, addr, passwd):
        with open(file, 'a') as file:
            file.write(f'{addr}:{passwd}\n')

    # def create_accounts(self, file, quantity, test):
    #     for _ in range(quantity):
    #         paswd = self.generator.mix()
    #         addr = self.smartholdem.create_account(paswd)
    #         self.write_account_creds(file, addr, paswd)

    def create_accounts(self, file, quantity):
        for _ in range(quantity):
            paswd = self.generator.mix()
            addr = self.smartholdem.create_account(paswd)
            self.write_account_creds(file, addr, paswd)

    @staticmethod
    def gen_mix_iters_quantity(num, max_iters):
        """
        Generate quantity of mix iterations by number and not more than max value of iterations.
        :param num:
        :param max_iters: value of max iterations
        :return:
        """
        new_iters_quantity = round(num / max_iters)

        return new_iters_quantity if new_iters_quantity < max_iters else max_iters

    def prepare_data_for_mixing(self):
        random.seed(datetime.now())
        mix_ratio, output_ratio = self.generate_ratios()
        num_mix_addrs, num_output_addrs = self.calculate_addrs_quantity(mix_ratio, output_ratio)
        file_data_lst = [(self.mix_accs_path, num_mix_addrs), (self.out_accs_path, num_output_addrs)]
        processes = []

        for data in file_data_lst:
            processes.append(Process(target=self.create_accounts, args=(*data,)))

        [process.start() for process in processes]
        [process.join() for process in processes]

        DataForMixing = namedtuple('DataForMixing', ['iters', 'mix_accs_quantities', 'quantities_coins_for_txs'])
        DataForMixing.iters = self.gen_mix_iters_quantity(num_mix_addrs, self.num_mix_iters)
        DataForMixing.mix_accs_quantities = self.split_num_on_parts(DataForMixing.iters, num_mix_addrs)
        DataForMixing.quantities_coins_for_txs = list(map(partial(self.split_num_on_parts, num=self.balance),
                                                          DataForMixing.mix_accs_quantities))
        return DataForMixing

    def send_txs(self, lines):
        for line in lines:
            print(line)

    def prepare_and_send_txs(self, file, txs_sizes_seq):
        total_processes = 0

        for i in range(0, len(txs_sizes_seq), self.max_num_processes):
            if total_processes == self.max_num_processes:
                break

            total_processes += 1

        total_ranges = utils.split_on_ranges_by_step(0, len(txs_sizes_seq), total_processes)
        lock = RLock()
        line_num = 1

        for range_ in total_ranges:
            self.send_txs(utils.read_file_from_specific_line(file, range_, lock))
            line_num += 1

    def mix(self):
        data_for_mixing = self.prepare_data_for_mixing()
        print(data_for_mixing.iters)
        print(data_for_mixing.mix_accs_quantities)
        print(data_for_mixing.quantities_coins_for_txs)

    def run(self):
        self.files_exists(self.files_ways_lst)
        privkey, own_addr, coins_amount_for_using, dest_addr = self.get_data_from_cfg(self.mixer_cfg_path)
        self.get_balance(own_addr, coins_amount_for_using)
        self.mix()


if __name__ == '__main__':
    CoinMixer().run()
