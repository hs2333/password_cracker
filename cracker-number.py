import itertools
import string
import time

def setup_password():
    while True:
        password = input("Set a 6-character password (numeric only) ")
        password = password.lower()

        if len(password) != 6:
            print("Password must be exactly 6 characters long.")
            continue

        if not all(string.digits for ch in password):
        #if not all(ch in string.ascii_lowercase + string.digits for ch in password):
            print("Only numbers 0-9 are allowed.")
            continue

        return password


def crack_password(target_password):
    characters = string.digits
    attempts = 0

    start_time = time.time()

    for guess_tuple in itertools.product(characters, repeat=6):
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