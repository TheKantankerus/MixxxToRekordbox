import random

rng = random.Random()


def generate_random_number(length):
    total_characters = "0123456789"
    randomString = ""
    for i in range(0, length):
        index = rng.randint(0, len(total_characters) - 1)
        randomString += total_characters[index]
    return randomString
