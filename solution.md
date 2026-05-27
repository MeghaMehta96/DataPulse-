# SOLUTION.md — Design Decisions

---

## Paragraph 1 — Why I Used a Generator Instead of a List

The first decision I made was to use a `generator function` (using `yield`) instead of building a list and returning it all at once.

The reason is simple — memory. If I build a list of 1 million records, Python has to store all 1 million dictionaries in RAM at the same time before giving anything back to the caller. That is wasteful and can crash the program on large inputs.

With a generator, only **one record exists in memory at a time**. The function produces a record, hands it over, pauses, and waits. It does not make the next record until the caller asks for it. This means no matter how many records you ask for — 100 or 10 million — the memory usage stays the same.

---

## Paragraph 2 — Why I Used `random.gauss()` for Normal Values (Not `random.uniform()`)

For the 90% of records that are "normal", I chose `random.gauss(mean, std_dev)` instead of `random.uniform(low, high)`.

`random.uniform(0, 100)` gives every number between 0 and 100 an equal chance of appearing. That is not how real servers behave. A real server's CPU does not randomly jump between 2% and 98% with equal probability — it mostly stays around a usual level (say 45%) and only occasionally dips low or goes high.

`random.gauss(45, 15)` means: most readings will be close to 45%, with natural variation above and below. This is called a bell curve and it matches how real-world data actually looks. I also had to clamp the values (using `max` and `min`) because Gaussian can occasionally produce numbers outside the valid range like negatives or over 100.

---

## Paragraph 3 — How I Implemented the 10% Spike Mechanism

To simulate occasional server problems, I needed roughly 1 in 10 records to have dangerously high values.

I used `random.random() < 0.10` to make this decision. `random.random()` gives a random float between 0.0 and 1.0, and there is exactly a 10% chance it falls below 0.10. This is clean, simple, and easy to adjust — if I wanted 20% spikes, I would just change it to `< 0.20`.

When a spike occurs, all four metrics (CPU, memory, disk, latency) go into their danger zones using `random.uniform()` over a high range. This simulates a real incident where a server under heavy load has multiple things go wrong at the same time.

---

## Paragraph 4 — Why `SERVICES` Is Defined Outside the Function

I defined the list of 5 service names as a module-level constant called `SERVICES` (all uppercase, following Python's PEP 8 convention for constants).

If I had defined it inside the function, Python would recreate that list on every single loop iteration — which is unnecessary work. Defining it once at the top of the file means it is created once and reused forever.

It also makes the code easier to maintain. If the team adds a 6th service, I only need to update one line in one place. Nothing else in the file needs to change.

---

## Paragraph 5 — Type Hints and Clean Timestamps

I added full type hints to the function signature: `generate_metrics(num_records: int, interval: float) -> Generator[dict, None, None]`.

Type hints are not required by Python but they make the code much easier to understand. Anyone reading the function knows exactly what to pass in and what they will get back without reading the whole function body. The return type `Generator[dict, None, None]` tells you: this yields dictionaries, you cannot send values into it, and it returns nothing when done.

For timestamps I used `datetime.now().isoformat(timespec="seconds")` which produces a clean format like `"2026-05-27T10:32:01"` — no microseconds, easy to read, and follows the standard ISO 8601 format used in almost all production logging systems.

---

# Task 2 — Anomaly Detector Design Decisions

---

## Paragraph 1 — Why I Used a Class Instead of Just Functions

For the anomaly detector I chose to build a class called `AnomalyDetector` instead of writing standalone functions.

The reason is that the detector needs to **remember things between calls** — like how many alerts have happened so far, and the last 5 readings for each metric. A plain function forgets everything the moment it finishes. A class keeps that state alive inside `self` as long as the object exists.

Think of it like a doctor who keeps a patient's history file on the desk. Every time a new reading comes in, the doctor does not start from zero — they look at the history and make a better decision.

---

## Paragraph 2 — Why I Used `collections.deque` for the Sliding Window

To calculate the moving average, I needed to always keep the last 5 readings and throw away anything older. I used `collections.deque(maxlen=5)` for this.

A regular list does not have a size limit. If I used a list I would have to manually check the length and remove old items every time — extra code, extra bugs. A `deque` with `maxlen` does this automatically. The moment you add a 6th item, it drops the oldest one on its own. No extra code needed.

This is important because moving averages help spot slow trends. One spike could be random. But if the CPU average over the last 5 readings is 88%, that is a real problem developing.

---

## Paragraph 3 — Why `THRESHOLDS` is a Class Variable, Not an Instance Variable

I put `THRESHOLDS` outside `__init__` at the top of the class. This makes it a **class variable** — shared by every single `AnomalyDetector` object.

I did not put it inside `__init__` because the threshold limits are not specific to one detector — they are the rules for the whole system. Every detector should use the same numbers. If you ever need to change the CPU threshold from 90 to 85, you change it in one place and every detector in the whole program automatically gets the update.

---

## Paragraph 4 — How I Built the Decorator to Log Alerts

I wrote a `@staticmethod` called `decorate_log` that wraps the `check_anomaly` method. Whenever `check_anomaly` runs and finds anomalies, the decorator automatically prints an `[ALERT]` line for each one — without me having to put a print statement inside `check_anomaly` itself.

I used `@staticmethod` because the decorator does not need access to `self` or `cls`. It is just a helper that takes a function, wraps it, and returns the wrapped version. I also used `@functools.wraps(func)` inside it so the wrapped function keeps its original name and docstring, which matters when debugging.

The key thing I learned here is that the decorator must be defined **before** `check_anomaly` in the class body. Python reads the class top to bottom, so if you put the decorator below the method it tries to decorate, it does not exist yet and the program crashes.

---

## Paragraph 5 — Why I Added `__len__` and `__repr__`

I added two dunder (magic) methods to make the detector feel like a proper Python object.

`__len__` lets you write `len(detector)` and get back the total number of alerts raised. Without it, you would have to write `detector._total_alerts` every time — which exposes the internal variable and looks messy.

`__repr__` controls what prints when you inspect the object. Instead of something useless like `<__main__.AnomalyDetector object at 0x000001A3>`, it now prints `AnomalyDetector(window_size=5, total_alerts=3)` — instantly useful for debugging. Any time you print the detector or check it in the terminal, you see the real state at a glance.

---

# Task 3 — Alert Router Design Decisions

---

## Paragraph 1 — Why I Used a Closure Instead of a Class

For the alert router I used a closure — a function that returns another function — instead of building a class.

The reason is that the router only needs to do one thing: take an anomaly and figure out which team to send it to. That is a single responsibility, and a closure handles it cleanly without the overhead of a class. The `team_config` dictionary (which maps teams to services and channels) is captured inside the inner function and stays private. Nobody outside can accidentally read or change it.

If I had used a class, I would need an `__init__`, a method, and `self` everywhere — just to do one thing. A closure keeps it short and focused.

---

## Paragraph 2 — Why I Used ABC and `@abstractmethod` for `BaseHandler`

Before writing `SlackHandler`, `PagerDutyHandler`, and `EmailHandler`, I created a `BaseHandler` class that inherits from `ABC` (Abstract Base Class).

The purpose is to create a **contract**. The contract says: every handler that exists in this system MUST have a `send()` method. If someone creates a new handler class in the future and forgets to write `send()`, Python will raise an error the moment they try to create an object from it — not later when the program is running and something mysteriously fails.

Without ABC, a missing `send()` method would only crash the program at the worst possible moment — in production, when a real alert needs to be sent. With ABC it crashes at the earliest safe moment — at startup.

---

## Paragraph 3 — The Strategy Pattern in `AlertDispatcher`

The `AlertDispatcher` class uses what is called the Strategy Pattern. Instead of a long `if/elif` chain to decide which handler to use, I stored all handlers in a dictionary:

```python
self._handlers = {
    "slack":     SlackHandler(),
    "pagerduty": PagerDutyHandler(),
    "email":     EmailHandler(),
}
```

When an anomaly comes in, I just do `self._handlers.get(channel)` to pick the right one. This is clean, easy to extend, and easy to read. If a new channel like `"teams"` is added in the future, I add one line to the dictionary and a new handler class — nothing else changes.

The handler objects are created once in `__init__` and reused every time. I do not create a new `SlackHandler()` on every dispatch call, which would be wasteful.

---

## Paragraph 4 — How the Routing Logic Works

The `route()` function (the closure) loops through the `team_config` dictionary and checks if the anomaly's `service_name` belongs to any team's service list. The moment it finds a match, it dispatches the alert and immediately returns.

The `return` after dispatching is important. Without it, the loop would keep going and might send the same alert to multiple teams if a service accidentally appeared in more than one team config. The early return makes the behaviour predictable — one service, one team, done.

If no team claims the service, a fallback message prints so the problem does not silently disappear. Silent failures are one of the hardest bugs to debug in a real system.

---

## Paragraph 5 — Why Handlers Just Print Instead of Making Real API Calls

All three handlers — Slack, PagerDuty, and Email — just print formatted messages to the terminal instead of making actual HTTP requests or sending real emails.

This is a deliberate decision for a demo and development tool. Real API calls would require API keys, network access, and external service accounts — none of which are appropriate for a local CLI tool being tested. The print output gives exactly the same information you would see in a real alert, so you can verify the routing logic is correct without any external dependencies.

In a real production version, you would replace the `print()` inside each `send()` method with the actual API call. Everything else — the routing, the dispatcher, the closure — stays exactly the same. That is the power of the strategy pattern.

---

# Task 4 — Report Writer Design Decisions

---

## Paragraph 1 — Why I Used a Context Manager Instead of a Regular Function

For writing the final report I built a class called `ReportWriter` that works as a context manager — used with the `with` keyword — instead of a plain function that you call manually at the end.

The reason is reliability. If I wrote a regular function like `save_report()`, the programmer using the code has to remember to call it. If the program crashes halfway through, or if someone forgets to call it, no report gets saved. A context manager removes that responsibility from the caller entirely. Python calls `__exit__` automatically the moment the `with` block ends — whether it ended normally or because of an error. The file is always saved.

---

## Paragraph 2 — Why `__exit__` Calls `_save()` and Returns `False`

Inside `__exit__` I do two things: call `self._save()` and then return `False`.

Calling `_save()` is the actual work — it builds the report dict and writes it to disk. This happens no matter what. Even if an exception crashed the program inside the `with` block, `__exit__` still runs and `_save()` still saves whatever data was collected up to that point. This means you always get a partial report instead of nothing.

Returning `False` tells Python — "I have finished my cleanup, but do not hide the error". If something crashed, the error still propagates normally so the developer knows about it. Returning `True` would swallow the exception silently, which would make bugs very hard to find.

---

## Paragraph 3 — Why I Separated `_save()` Into Its Own Method

I could have put all the file-writing code directly inside `__exit__`, but I chose to put it in a private method called `_save()` instead.

The reason is the same reason you tidy up a messy room by sorting things into boxes — it is easier to find, read, and fix. `__exit__` stays clean and reads like a sentence: "save, then return". The actual details of how saving works live in `_save()`. If the file-writing logic ever needs to change — for example, switching from JSON to YAML — I change one method without touching `__exit__` at all.

The underscore prefix on `_save` signals to other developers that this is an internal helper, not meant to be called from outside the class.

---

# Task 5 — CLI Entry Point Design Decisions

---

## Paragraph 1 — Why I Used `argparse` Instead of `sys.argv`

To let users control how the program runs from the terminal, I used Python's built-in `argparse` module instead of reading `sys.argv` directly.

`sys.argv` gives you a raw list of strings — you have to manually check if the user typed `--records`, convert the value to an integer yourself, and decide what error message to show if they typed something wrong. That is a lot of repetitive work that is easy to get wrong.

`argparse` does all of that automatically. You declare what arguments the program accepts — their names, types, defaults, and help text — and `argparse` handles the parsing, type conversion, and error messages for free. It also generates a `--help` output automatically, so any user can type `python datapulse.py --help` and see exactly what the program does without reading the source code.

---

## Paragraph 2 — Why I Used `--verbose` as a Flag, Not a Value

The `--verbose` argument is defined with `action="store_true"`, which means it does not take a value — it is either present or absent.

When the user types `--verbose`, `args.verbose` becomes `True`. When they do not type it, it defaults to `False`. This is the standard pattern for on/off switches in CLI tools. It is simpler than asking the user to type `--verbose true` or `--verbose 1`, and it matches how most popular command-line tools behave (like `git --verbose` or `pip install --quiet`).

---

## Paragraph 3 — Why I Added `KeyboardInterrupt` Handling

When a user presses `Ctrl+C` to stop the program early, Python normally raises a `KeyboardInterrupt` exception and prints a messy traceback. Instead of letting that happen, I wrapped the main processing loop in a `try/except KeyboardInterrupt` block.

When the user interrupts, the program catches it cleanly, prints a helpful message, and then continues to the report-writing code below. This means the user always gets a partial report with whatever data was collected before they stopped — instead of losing everything. A tool that handles interruptions gracefully feels professional and safe to use.

---

## Paragraph 4 — How `_build_report_data()` Works as a Helper

I put all the report-building logic — counting alerts by severity, by service, by metric, sorting the top 5 critical alerts — into a separate helper function called `_build_report_data()`.

If I had put this logic directly inside `main()`, the function would have been very long and hard to follow. `main()` should read like a story: "parse arguments, create objects, run the loop, build the report, save it". The details of building the report belong in a separate place.

I used `defaultdict(int)` from the `collections` module for the counting. A regular `dict` would crash with a `KeyError` the first time you try to increment a key that does not exist yet. `defaultdict(int)` automatically starts every new key at `0`, so you can do `by_severity["CRITICAL"] += 1` without checking if `"CRITICAL"` is already in the dict.

---

## Paragraph 5 — Why I Used `if __name__ == "__main__"`

At the bottom of the file I have:

```python
if __name__ == "__main__":
    main()
```

This is a Python safety guard. When Python runs a file directly (`python datapulse.py`), the special variable `__name__` is set to `"__main__"`, so `main()` runs. But if another file imports this module — for example, a test file that imports `_build_report_data` — `__name__` is set to the module's name instead, and `main()` does NOT run automatically.

Without this guard, importing anything from `datapulse.py` would immediately start the whole program — including generating metrics and printing output. That would make the code untestable and difficult to reuse. The guard is a small habit that makes a big difference.

---

## Paragraph 4 — How `add_section` Builds the Report Piece by Piece

Instead of passing the entire report structure in one go, I built the `add_section()` method so that sections can be added one at a time inside the `with` block.

Each call to `add_section("title", data)` just does `self._sections["title"] = data` — a simple dictionary assignment. When `_save()` eventually runs, it combines `generated_at` with all the sections using dict unpacking (`**self._sections`) into one final report dict and writes it all at once.

This makes the reporter flexible. You can add as many or as few sections as you want. The reporter does not care what the sections contain — it just stores them and dumps them to JSON at the end.

---

## Paragraph 5 — Why I Used `try/except` Around the File Write

The file writing inside `_save()` is wrapped in a `try/except OSError` block.

Writing files can fail for reasons completely outside the program's control — the disk might be full, the folder might not exist, or the program might not have permission to write to that location. If I let these errors crash the program with an ugly Python traceback, the user would have no idea what went wrong. With `try/except`, they get a clear message like `[ERROR] Failed to write report: [Errno 13] Permission denied`.

I caught `OSError` specifically rather than the broad `Exception` because file-related failures in Python always raise `OSError` or one of its subclasses (`FileNotFoundError`, `PermissionError`). Catching only what you expect is a good habit — it means any other unexpected error still crashes loudly instead of being silently swallowed.
