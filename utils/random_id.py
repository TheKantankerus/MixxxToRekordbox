import random

rng = random.Random()

existing_ids = []


def generate_random_number() -> str:
    gen_id = rng.randint(0, 2147483647)
    while gen_id in existing_ids:
        gen_id = rng.randint(0, 2147483647)
    return f"{gen_id:010}"
