# SOLUTION.md — Design Decisions for Task 1 (Data Generator)

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
