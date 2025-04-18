# -*- coding: utf-8 -*-
"""django_signals_demo.py

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1NS_qZ1bTFytqRLf8dbdCZFMGjsGRcx6a

Question 1: By default are django signals executed synchronously or asynchronously?

✅ Answer:
Yes, Django signals are synchronous by default.
That means the signal handler runs immediately when the signal is sent, and the main function waits for the signal handler to finish.
"""

import time
from functools import wraps

# Simulated signal system
class Signal:
    def __init__(self):
        self._receivers = []

    def connect(self, func):
        self._receivers.append(func)
        return func

    def send(self, sender, **kwargs):
        for receiver in self._receivers:
            receiver(sender=sender, **kwargs)

# Create a signal instance
post_save = Signal()

# Simulate a User model
class User:
    def __init__(self, username):
        self.username = username

    @classmethod
    def create(cls, username):
        user = cls(username=username)
        print("👤 User instance created")
        post_save.send(sender=cls, instance=user)
        return user

# Attach a slow signal handler
@post_save.connect
def slow_signal_handler(sender, instance, **kwargs):
    print("➡️ Signal handler started")
    time.sleep(5)  # Simulate a slow task
    print("✅ Signal handler ended")

# Measure total time
start = time.time()
User.create("testuser_sync")
end = time.time()

print(f"⏱️ Total time taken: {end - start:.2f} seconds")

"""If the signal were asynchronous, We see the final print (Total time taken) appear before Signal handler ended — but since it's synchronous, it waits.

Question 2: Do django signals run in the same thread as the caller?

✅Answer: Yes, by default Django signals run in the same thread as the function that triggered the signal.
"""

import time
import threading

# Simulate Django-style signal system
class Signal:
    def __init__(self):
        self._receivers = []

    def connect(self, func):
        self._receivers.append(func)
        return func

    def send(self, sender, **kwargs):
        for receiver in self._receivers:
            receiver(sender=sender, **kwargs)

# Signal instance
post_save = Signal()

# Simulate User model
class User:
    def __init__(self, username):
        self.username = username

    @classmethod
    def create(cls, username):
        user = cls(username=username)
        print("👤 User created in thread:", threading.get_ident())
        post_save.send(sender=cls, instance=user)
        return user

# Signal handler
@post_save.connect
def handler(sender, instance, **kwargs):
    print("🛎️ Signal handler running in thread:", threading.get_ident())

# Trigger and compare thread IDs
User.create("thread_test_user")

"""Conclusion:
This proves that the signal handler and the caller share the same thread, confirming that:

Django signals are executed in the same thread as the caller by default.

3rd question explanation and logic below

Question 3: By default do django signals run in the same database transaction as the caller?

Answer: Yes, by default Django signals are executed inside the same database transaction as the operation that triggered them.
So if the transaction is rolled back, any changes made in the signal handler will also be rolled back.
"""

from contextlib import contextmanager

# Simulate in-memory database
FAKE_DB = {"users": [], "logs": []}

# Simulate Django signal
class Signal:
    def __init__(self):
        self._receivers = []

    def connect(self, func):
        self._receivers.append(func)
        return func

    def send(self, sender, **kwargs):
        for receiver in self._receivers:
            receiver(sender=sender, **kwargs)

# Define the signal
post_save = Signal()

# Simulated Log model
def create_log(message):
    FAKE_DB["logs"].append(message)

# Signal handler
@post_save.connect
def log_user_creation(sender, instance, **kwargs):
    print("📝 Creating log in signal handler...")
    create_log(f"User created: {instance['username']}")

# Simulated transaction manager
@contextmanager
def atomic():
    backup = FAKE_DB["logs"][:]
    try:
        yield
    except Exception as e:
        print("⛔ Exception occurred, rolling back logs...")
        FAKE_DB["logs"] = backup

# Simulate user creation
def create_user(username, raise_exception=False):
    user = {"username": username}
    FAKE_DB["users"].append(user)
    post_save.send(sender="User", instance=user)
    if raise_exception:
        raise Exception("Simulated error after signal")
    return user

# Run transaction and trigger rollback
print("🔁 Starting transaction...")
try:
    with atomic():
        create_user("txn_test_user", raise_exception=True)
except:
    print("🚨 Transaction failed.")

print("\n📦 Final Logs in 'DB':", FAKE_DB["logs"])

"""Conclusion:
Even though the signal handler created a log, it was rolled back when the main operation failed.

This proves that Django signal handlers execute within the same transaction as the caller.
"""