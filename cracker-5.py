import itertools
import string
import time

def setup_password():
    while True:
        password = input("Set a 5-character password (lowercase letters and/or numbers) ")
        password = password.lower()

        if len(password) != 5:
            print("Password must be exactly 5 characters long.")
            continue

        if not all(ch in string.ascii_lowercase + string.digits for ch in password):
            print("Only lowercase letters and numbers are allowed.")
            continue

        return password


def crack_password(target_password):
    characters = string.digits + string.ascii_lowercase
    attempts = 0

    start_time = time.time()

    for guess_tuple in itertools.product(characters, repeat=5):
        guess = ''.join(guess_tuple)
        attempts += 1

        # print(f"Trying: {guess}")

        if guess == target_password:
            end_time = time.time()
            elapsed_time = end_time - start_time

            print("\nPassword cracked!")
            print(f"Correct password: {guess}")
            print(f"Total attempts: {attempts}")
            print(f"Time taken: {elapsed_time:.4f} seconds")
            return


def main():
    password = setup_password()
    crack_password(password)


if __name__ == "__main__":
    main()