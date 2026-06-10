'''
Thread 1: 0 1 2 3 4 5 6 7 8
Thread 2: 9 a b c d e f g h
Thread 3: i j k l m n o p q
Thread 4: r s t u v w x y z
'''

import itertools
import string
import time
import threading
import queue
import tkinter as tk
from tkinter import messagebox


CHARACTERS = string.digits + string.ascii_lowercase
# UPDATE_EVERY = 1000
UPDATE_INTERVAL = 0.1 #0.05
MAX_OUTPUT_LINES = 200
NUM_THREADS = 4

class PasswordCrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Password Cracker Demo (one-thread)")
        self.root.geometry("560x470")

        self.target_password = ""
        self.attempts = 0
        self.start_time = None
        self.paused_time = 0
        self.pause_start = None

        self.running = False
        self.paused = False

        # threading tools
        self.worker_threads = []
        self.attempts_lock = threading.Lock()
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        self.title_label = tk.Label(
            root,
            text="CPU Password Cracker Demo",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=10)

        self.password_label = tk.Label(
            root,
            text="Set 6-character password (letters and/or numbers)"
        )
        self.password_label.pack()

        self.password_entry = tk.Entry(root, width=25, show="*")
        self.password_entry.pack(pady=5)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.start_button = tk.Button(
            self.button_frame,
            text="Start Cracking",
            command=self.start_cracking
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = tk.Button(
            self.button_frame,
            text="Pause",
            command=self.pause_cracking,
            state=tk.DISABLED
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.resume_button = tk.Button(
            self.button_frame,
            text="Resume",
            command=self.resume_cracking,
            state=tk.DISABLED
        )
        self.resume_button.grid(row=0, column=2, padx=5)

        self.restart_button = tk.Button(
            self.button_frame,
            text="Restart",
            command=self.restart_cracking,
            state=tk.DISABLED
        )
        self.restart_button.grid(row=0, column=3, padx=5)

        self.current_guess_label = tk.Label(
            root,
            text="Current guess: None",
            font=("Arial", 12)
        )
        self.current_guess_label.pack(pady=5)

        self.attempts_label = tk.Label(
            root,
            text="Attempts: 0",
            font=("Arial", 12)
        )
        self.attempts_label.pack(pady=5)

        self.time_label = tk.Label(
            root,
            text="Time: 0.0000 seconds",
            font=("Arial", 12)
        )
        self.time_label.pack(pady=5)

        self.output_box = tk.Text(root, height=10, width=60)
        self.output_box.pack(pady=10)

        # Keep checking messages from the worker thread
        self.check_queue()
    
    #helper
    def split_characters_evenly(self, chars, num_threads):
        chunk_size = len(chars) // num_threads
        chunks = []

        for i in range(num_threads):
            start = i * chunk_size

            if i == num_threads - 1:
                end = len(chars)
            else:
                end = (i + 1) * chunk_size

            chunks.append(chars[start:end])

        return chunks

    def validate_password(self, password):
        password = password.lower()

        if len(password) != 6:
            return None, "Password must be exactly 6 characters long."

        allowed = string.ascii_lowercase + string.digits
        if not all(ch in allowed for ch in password):
            return None, "Only letters and numbers are allowed."

        return password, None

    def start_cracking(self):
        password = self.password_entry.get()
        password, error = self.validate_password(password)

        if error:
            messagebox.showerror("Invalid Password", error)
            return

        self.target_password = password
        self.attempts = 0
        self.start_time = time.time()
        self.paused_time = 0
        self.pause_start = None

        self.running = True
        self.paused = False

        self.stop_event.clear()
        self.pause_event.clear()

        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, "Starting cracker in worker thread...\n")

        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.NORMAL)
        self.password_entry.config(state=tk.DISABLED)

        self.worker_threads = []
        chunks = self.split_characters_evenly(CHARACTERS, NUM_THREADS)
        for thread_id, starting_chars in enumerate(chunks, start=1):
            thread = threading.Thread(
                target=self.crack_worker,
                args=(thread_id, starting_chars),
                daemon=True
            )
            self.worker_threads.append(thread)
            thread.start()
        self.output_box.insert(tk.END, f"Started {NUM_THREADS} worker threads.\n")


    def crack_worker(self, thread_id, starting_chars):
        # run in the background worker thread
        # NO directly update Tkinter widgets here
        # only checks passwords with first character inside starting_chars.

        last_update_time = time.time()

        for first_char in starting_chars:
            for rest_tuple in itertools.product(CHARACTERS, repeat=5):
                if self.stop_event.is_set():
                    return

                while self.pause_event.is_set():
                    if self.stop_event.is_set():
                        return
                    time.sleep(0.05)

                guess = first_char + ''.join(rest_tuple)

                # Multiple threads update attempts, so use a lock.
                with self.attempts_lock:
                    self.attempts += 1
                    attempts_snapshot = self.attempts

                current_time = time.time()
                elapsed_time = self.get_elapsed_time()

                if current_time - last_update_time >= UPDATE_INTERVAL:
                    self.message_queue.put({
                        "type": "update",
                        "thread_id": thread_id,
                        "guess": guess,
                        "attempts": attempts_snapshot,
                        "time": elapsed_time
                    })
                    last_update_time = current_time

                if guess == self.target_password:
                    # Tell all other threads to stop.
                    self.stop_event.set()

                    self.message_queue.put({
                        "type": "found",
                        "thread_id": thread_id,
                        "guess": guess,
                        "attempts": attempts_snapshot,
                        "time": elapsed_time
                    })
                    return

    def check_queue(self):
        # run in the Tkinter main thread.
        # update the GUI using messages from the worker thread.
        max_messages_per_check = 20
        messages_processed = 0

        try:
            while messages_processed < max_messages_per_check:
                message = self.message_queue.get_nowait()
                messages_processed += 1

                if message["type"] == "update":
                    thread_id = message["thread_id"]
                    guess = message["guess"]
                    attempts = message["attempts"]
                    elapsed_time = message["time"]

                    self.current_guess_label.config(text=f"Current guess: {guess}")
                    self.attempts_label.config(text=f"Attempts: {attempts}")
                    self.time_label.config(text=f"Time: {elapsed_time:.4f} seconds")

                    # Do not print every guess. This text box is slow.
                    # self.output_box.insert(
                    #     tk.END,
                    #     f"Trying: {guess}\n"
                    # )
                    # self.output_box.see(tk.END)
                    self.output_box.insert(
                        tk.END,
                        f"Thread {thread_id}: Trying {guess}    Attempts: {attempts}\n"
                    )

                    line_count = int(self.output_box.index("end-1c").split(".")[0])
                    if line_count > MAX_OUTPUT_LINES:
                        self.output_box.delete("1.0", "50.0")

                    self.output_box.see(tk.END)

                elif message["type"] == "found":
                    self.running = False
                    self.paused = False

                    guess = message["guess"]
                    attempts = message["attempts"]
                    elapsed_time = message["time"]
                    thread_id = message["thread_id"]

                    self.current_guess_label.config(text=f"Current guess: {guess}")
                    self.attempts_label.config(text=f"Attempts: {attempts}")
                    self.time_label.config(text=f"Time: {elapsed_time:.4f} seconds")

                    self.output_box.insert(tk.END, "\nPassword cracked!\n")
                    self.output_box.insert(tk.END, f"Found by thread: {thread_id}\n")
                    self.output_box.insert(tk.END, f"Correct password: {guess}\n")
                    self.output_box.insert(tk.END, f"Total attempts: {attempts}\n")
                    self.output_box.insert(tk.END, f"Time taken: {elapsed_time:.4f} seconds\n")

                    self.pause_button.config(state=tk.DISABLED)
                    self.resume_button.config(state=tk.DISABLED)
                    self.restart_button.config(state=tk.NORMAL)

                    messagebox.showinfo(
                        "Password Cracked!",
                        f"Correct password: {guess}\n"
                        f"Found by thread: {thread_id}\n"
                        f"Total attempts: {attempts}\n"
                        f"Time taken: {elapsed_time:.4f} seconds"
                    )

                elif message["type"] == "not_found":
                    self.running = False
                    messagebox.showinfo("Done", "Password was not found.")

                    self.pause_button.config(state=tk.DISABLED)
                    self.resume_button.config(state=tk.DISABLED)
                    self.restart_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass

        # check the queue again after 50 ms
        self.root.after(50, self.check_queue)

    def pause_cracking(self):
        if self.running and not self.paused:
            self.paused = True
            self.pause_start = time.time()
            self.pause_event.set()

            self.output_box.insert(tk.END, "\nPaused.\n")
            self.output_box.see(tk.END)

            self.pause_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.NORMAL)

    def resume_cracking(self):
        if self.running and self.paused:
            self.paused = False

            if self.pause_start is not None:
                self.paused_time += time.time() - self.pause_start
                self.pause_start = None

            self.pause_event.clear()

            self.output_box.insert(tk.END, "Resumed.\n")
            self.output_box.see(tk.END)

            self.pause_button.config(state=tk.NORMAL)
            self.resume_button.config(state=tk.DISABLED)

    def restart_cracking(self):
        self.stop_event.set()
        self.pause_event.clear()

        self.running = False
        self.paused = False

        self.target_password = ""
        self.attempts = 0
        self.start_time = None
        self.paused_time = 0
        self.pause_start = None

        # Clear old messages still waiting in the queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except queue.Empty:
                break

        self.current_guess_label.config(text="Current guess: None")
        self.attempts_label.config(text="Attempts: 0")
        self.time_label.config(text="Time: 0.0000 seconds")

        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, "Restarted.\n")
        self.output_box.insert(tk.END, "Set 6-character password (letters and/or numbers)\n")

        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)
        self.password_entry.config(state=tk.NORMAL)
        self.password_entry.delete(0, tk.END)

    def get_elapsed_time(self):
        if self.start_time is None:
            return 0

        if self.paused and self.pause_start is not None:
            return self.pause_start - self.start_time - self.paused_time

        return time.time() - self.start_time - self.paused_time


def main():
    root = tk.Tk()
    app = PasswordCrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()