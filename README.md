# CPU Password Cracker Demo #

## 1. Current Code ##
### Basic ###
``cracker.py``: 6-digit, letter+number

``cracker-number.py``: 8-digit, number only

``cracker-5.py``: 5-digit, letter+number

**Note**: in cracker.py / cracker-number.py, change the variable *PASSWORD_LENGTH* for the password length we want. 

### GUI ###
``gui.py``: (6 digit, letter+number, gui) showing password input box, start/pause/resume/restart buttons, current guess, attempt counts, time spent. In the text box, guesses will be shown (rolling), and the correct password will pop out once it's cracked. 

``gui_noRollingWindow.py``: (6 digit, letter+number, gui) showing everything but rolling guess tries. 

### Thread ###
``thread.py``: (6 digit, letter+number, gui) one main thread + one worker thread, change the variable *UPDATE_EVERY* to test on gui update for every 10/100/1000 guesses.

``time_based.py``: (6 digit, letter+number, gui) same as thread.py, but update based on time passed instead of guess count, change the variable *UPDATE_INTERVAL* oo test on gui update for every 0.05/0.1/1 seconds. 

``4-thread.py``: (6 digit, letter+number, gui) one main thread + four worker thread. 

Thread 1: 0 1 2 3 4 5 6 7 8

Thread 2: 9 a b c d e f g h

Thread 3: i j k l m n o p q

Thread 4: r s t u v w x y z



## 2. How to build a file (.exe)? ##
```
pip install pyinstaller
pyinstaller --onefile filename.py
```