# -*- coding: utf-8 -*-
import string
import random


class Generator:
    def __init__(self):
        self.small = string.ascii_lowercase
        self.big = string.ascii_uppercase
        self.digits = string.digits
        self.spec = string.punctuation

    def shuffle_digits(self, range_=10):
        digits_list = list(self.digits)
        random.shuffle(digits_list)
        first_seq = ''.join([random.choice(digits_list) for _ in range(range_)])

        return first_seq

    def shuffle_s_and_b(self, range_=20):
        lett_list = list(self.small + self.big)
        random.shuffle(lett_list)
        second_seq = ''.join([random.choice(lett_list) for _ in range(range_)])

        return second_seq

    def shuffle_all(self):
        new_mix = list(self.small + self.big + self.digits + self.spec)
        random.shuffle(new_mix)
        third_seq = ''.join([random.choice(new_mix) for _ in range(15)])

        return third_seq

    def mix(self):
        return 'S' + self.shuffle_digits() + self.shuffle_s_and_b() + self.shuffle_all()
