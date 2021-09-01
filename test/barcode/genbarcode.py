from random import randrange
import functools

def generate_12_random_numbers():
    numbers = [4,2,1]
    for x in range(9):
        numbers.append(randrange(10))
    return numbers

def calculate_checksum(ean):
    """
    Calculates the checksum for an EAN13
    @param list ean: List of 12 numbers for first part of EAN13
    :returns: The checksum for `ean`.
    :rtype: Integer
    """
    assert len(ean) == 12, "EAN must be a list of 12 numbers"
    sum_ = lambda x, y: int(x) + int(y)
    evensum = functools.reduce(sum_, ean[::2])
    oddsum = functools.reduce(sum_, ean[1::2])
    return (10 - ((evensum + oddsum * 3) % 10)) % 10

numbers = generate_12_random_numbers()
numbers.append(calculate_checksum(numbers))
print (''.join(map(str, numbers)))