# -*- coding -*-
import linecache


def read_file_from_specific_line(file, range_, lock):
    """
    Read file from specific line.
    :param file:
    :param range_:
    :param lock:
    :return:
    """
    begin = range_[0] if range_[0] != 0 else 1

    with lock:
        for line_num in range(begin, range_[1] + 1):
            yield linecache.getline(file, line_num)


def check_on_not_eq_vals(val1, val2):
    """
    Func which check values on non equivalent and return tuple of vals.
    :param val1:
    :param val2:
    :return:
    """
    return (val1, val2) if val1 != val2 else (val1,)


def check_difference_on_lt(val1, val2):
    """
    Func which calculate difference of values and check it on __lt__ num 20.
    Additional func for func split_on_ranges_by_step.
    :param val1:
    :param val2:
    :return:
    """
    difference = val2 - val1

    if difference < 20:     # < 20 are nums on which func split on rages return incorrect ranges.
        return val1, val2


def split_on_ranges_by_step(begin, end, num_ranges):
    """
    Func which beginning split on ranges num from param begin to param end by step.
    :param begin:
    :param end:
    :param num_ranges:
    :return:
    """
    last_val = (end - begin) % num_ranges
    end_ = end - last_val
    step = round((end - begin) / num_ranges) if last_val == 0 else round((end_ - begin) / num_ranges)
    lst = []
    result = check_difference_on_lt(begin, end)

    if result:
        lst.append(result)
        return lst

    for count, i in enumerate(range(begin, end_, step)):
        if count == 0:
            lst.append((i, i + step))

        else:
            lst.append((i + 1, i + step))

            if count == num_ranges - 1 and last_val != 0:
                lst.append(check_on_not_eq_vals(i + step + 1, i + step + last_val))

    return lst

