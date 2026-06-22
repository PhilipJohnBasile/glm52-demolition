# Elite Code: SFT Gold for Healing Toward True Software Craftsmanship

> Purpose: External gold for supervised fine-tuning. A competent-but-not-elite model cannot
> bootstrap eliteness from its own outputs — it needs ground truth from the masters. This
> document supplies the canon, the criteria, complete gold examples, and an audit gate.

---

## 1. THE ELITE CANON

### The Founding Layer — Systems and Theory

**Brian W. Kernighan** (Bell Labs, Princeton)
Signature principle: *Clarity is the primary virtue of code.* "Write clearly — don't be too
clever." Author (with Plauger) of *The Elements of Programming Style* (1974) and (with Pike)
*The Practice of Programming* (1999). Ninety percent of his 1974 style rules remain valid today.
His test: "If someone could understand your code when read aloud over the telephone, it's clear
enough." Gave us the rule: broader scope → more informative name; local scope → short name.

**Rob Pike** (Bell Labs, Google — Go co-creator)
Signature principle: *Simplicity requires deliberate restraint.* "Fancy algorithms are slow when
n is small, and n is usually small." Co-authored the Unix philosophy and Go. In Go he enforced
`gofmt` so style disputes die at the tool level, not in review. Rules 1 and 2 of his five rules
of performance: don't optimize; don't optimize yet.

**Dennis Ritchie** (Bell Labs — C, Unix)
Signature principle: *The right abstraction dissolves complexity rather than hiding it.* C's
design — transparent cost model, no hidden allocations, what-you-see-is-what-runs — shaped every
systems language since. Unix's design was driven by a single purpose: make computing as simple as
possible.

**Ken Thompson** (Bell Labs, Google — Unix, UTF-8, Go)
Signature principle: *Build the minimal thing that works, then compose.* Wrote pipes in a single
night after nine years of McIlroy pestering. "When in doubt, use brute force." Trusted the
algorithm over the trick.

**Doug McIlroy** (Bell Labs — pipes, Unix tools)
Signature principle: *Composition over monolith.* His 1964 memo proposed programs connect like
garden hoses; Thompson implemented it as `|` in 1973. "Write programs that do one thing and do it
well. Write programs to work together. Write programs to handle text streams, because that is a
universal interface." Invented `diff`, `sort`, `spell`, `tr`.

**Donald E. Knuth** (Stanford — TAOCP, TeX, literate programming)
Signature principle: *Programs are literature written for humans who incidentally run on
machines.* "Let us concentrate rather on explaining to human beings what we want a computer to
do." Full quote on optimization: "We should forget about small efficiencies, say about 97% of
the time: premature optimization is the root of all evil. Yet we should not pass up our
opportunities in that critical 3%." Literate programming: document the *why*, not the *what*.

**Edsger W. Dijkstra** (Eindhoven, UT Austin)
Signature principle: *Simplicity is the prerequisite for reliability.* "Simplicity is a great
virtue but it requires hard work to achieve it and education to appreciate it. And to make matters
worse: complexity sells better." Invented structured programming to eliminate unstructured GOTO;
argued that programs should be so clear that their correctness is obvious by inspection.

**C.A.R. (Tony) Hoare** (Oxford — quicksort, CSP, Hoare logic)
Signature principle: *There are only two kinds of software: simple with obvious correctness, and
complex with non-obvious bugs.* Full quote: "There are two ways of constructing a software
design: One way is to make it so simple that there are obviously no deficiencies, and the other
way is to make it so complicated that there are no obvious deficiencies. The first method is far
more difficult." "The price of reliability is the pursuit of the utmost simplicity."

**David Parnas** (McMaster — information hiding, modular decomposition)
Signature principle: *Hide every design decision that is likely to change.* His 1972 paper "On
the Criteria To Be Used in Decomposing Systems into Modules" shifted the field from flow-based
decomposition to change-based decomposition. High cohesion within modules, loose coupling between
them. Each module's secret is its most volatile design decision.

**Fred Brooks** (IBM, UNC — OS/360, Mythical Man-Month)
Signature principle: *Conceptual integrity is the most important property of a system.* "It is
better to have a system omit certain anomalous features and improvements, but to reflect one set
of design ideas, than to have one that contains many good but independent and uncoordinated
ideas." Essence of software is not the accidents of implementation but the difficult conceptual
structure.

**Barbara Liskov** (MIT — abstract data types, CLU, distributed systems)
Signature principle: *Define types by their behavior, not their representation.* Invented abstract
data types (ADTs): a type is defined by the operations it supports and the promises those
operations keep — the hidden representation is irrelevant to callers. Her substitution principle:
subtypes must be substitutable for their base types without breaking correctness.

### The Craft Layer — Practices and Patterns

**Robert C. Martin ("Uncle Bob")** (various — Clean Code, SOLID)
Signature principle: *Functions do one thing; names tell the truth.* Functions should be small,
do exactly one thing, and be named so the name is the documentation. SOLID: each module has one
reason to change; extend via abstraction, not modification. "The ratio of time spent reading
versus writing is well over 10 to 1."

**Martin Fowler** (ThoughtWorks — Refactoring, patterns)
Signature principle: *Working code that cannot be understood is unfinished.* Refactoring
(noun): a change to internal structure that makes it easier to understand and cheaper to modify
without changing observable behavior. Codified code smells — surface symptoms of deeper structural
problems.

**Kent Beck** (various — TDD, XP, JUnit)
Signature principle: *Make it work, make it right, make it fast — in that order.* TDD is not
primarily about testing; it is about design. Writing tests first forces interfaces before
implementations, behavior before structure. "Tests are the Rosetta Stone of code: they tell you
what the code is supposed to do."

### The Domain Masters

**Peter Norvig** (Google — AI, Python, algorithms)
Signature principle: *Choose the perfect data model and the algorithm follows.* His 21-line
spelling corrector solves a real NLP problem with probability theory, Counter, and generator
expressions — nothing more. Emphasizes elegant data representation over clever procedure.

**Rich Hickey** (Cognitect — Clojure)
Signature principle: *Simplicity is not ease; simplicity is the absence of interleaving.*
"Simple Made Easy" (2011): *simple* means one role, one concept, no braiding of concerns.
*Easy* means familiar, nearby — orthogonal to simple. "Decomplect relentlessly."
Values over references; pure functions over stateful objects; data over abstractions.

**Joe Armstrong** (Ericsson — Erlang, OTP)
Signature principle: *Design for failure; let processes crash cleanly.* "Let it crash": do not
over-defend every line. Instead, build supervisor trees that restart failed workers in known-good
state. The system's reliability comes from its *structure*, not from heroic defensive code in
individual functions. Separate the happy path from the error path at the process level.

**John Carmack** (id Software, Meta — Doom, Quake, VR)
Signature principle: *Minimize state; make functions pure where possible; understand every
execution path.* "A large fraction of the flaws in software development are due to programmers
not fully understanding all the possible states their code may execute in." Functional style in
C++: prefer functions that take all inputs as parameters and return results without side effects.
"Sometimes the elegant implementation is just a function. Not a method. Not a class. Not a
framework. Just a function."

**Linus Torvalds** (Linux kernel)
Signature principle: *Good taste means eliminating special cases through better data structures.*
Famous TED demo: a naive linked-list removal has a special case for the head node; the elegant
version uses a pointer-to-pointer and the special case vanishes. "Bad programmers worry about the
code. Good programmers worry about data structures and their relationships."

**Guido van Rossum** (Python)
Signature principle: *Readability counts; there should be one obvious way.* The Zen of Python
(Tim Peters, PEP 20): Beautiful > ugly. Explicit > implicit. Simple > complex. Flat > nested.
Sparse > dense. Readability counts. Errors should never pass silently. In the face of ambiguity,
refuse the temptation to guess. There should be one — and preferably only one — obvious way.

---

## 2. CHECKABLE ELITENESS CRITERIA

These criteria are binary or near-binary — an audit can gate on them.

### C1 — Clarity Over Cleverness
- Code reads like prose from top to bottom.
- No bit-twiddling tricks where a named constant would do.
- No expression packing: `a = b = c++` when three lines would be clearer.
- Kernighan's phone test: readable aloud.

### C2 — Names That Explain Intent
- Functions named as verbs describing what they do, not how: `parse_config`, not `do_stuff`.
- Variables named for what they hold, not for their type: `user_id`, not `int_val`.
- Boolean names start with `is_`, `has_`, `can_`, `should_` or the predicate is self-evident.
- No single-letter names outside of mathematical iteration indices (`i`, `j`, `x`, `y` in small scope).
- No `data`, `info`, `manager`, `helper`, `util` as primary names — these are non-names.

### C3 — Small, Honest Functions Doing One Thing
- A function should fit on one screen (~40 lines is a warning; ~80 is a smell).
- If you can't name a function without using "and", it does two things.
- No hidden side effects: a function named `is_valid` must not write to a database.
- One level of abstraction per function (Brooks: conceptual integrity).

### C4 — Idiomatic for the Language
- Python: generators, comprehensions, context managers, `Counter`/`defaultdict`, unpacking. PEP 8. `with` for resources.
- Rust: `Result`/`Option` propagated with `?`, iterator chains (`.map().filter().collect()`), ownership without cloning unnecessarily, no `unwrap()` in library code.
- Go: error as last return value; `if err != nil` immediately after the call; `defer` for cleanup; table-driven tests; goroutines + channels for concurrency, not shared memory.
- C: `const` correctness; explicit resource ownership; no implicit fall-through in switch; `NULL` checks before dereference.

### C5 — Errors Handled, Not Hidden
- No swallowed exceptions: `except: pass` is almost always wrong.
- No `unwrap()` / `.get()` without justification in Rust production paths.
- Error paths are as clean as success paths.
- Errors carry context: "failed to open config" not "error".
- Armstrong's rule: let it crash early and cleanly rather than limp on with corrupted state.

### C6 — No Dead Code, No Speculative Complexity
- No commented-out code in production.
- No `TODO` blocks more than one sprint old without an issue tracker reference.
- No abstractions added "for future flexibility" without a concrete second use case (YAGNI).
- Carmack: "It is not that uncommon for the cost of an abstraction to outweigh the benefit it delivers. Kill one today."

### C7 — Simplicity as Prerequisite for Reliability (Dijkstra)
- If correctness cannot be argued from inspection, the design is too complex.
- Prefer flat over nested: fewer nesting levels = fewer interacting states.
- Hickey: decomplect — separate things that are braided but do not need to be.
- Hoare: if there are no obvious deficiencies, you won. If there are no *non-obvious* deficiencies, you have only hidden them.

### C8 — Composition (Unix / McIlroy)
- Prefer functions that consume and return plain data over objects that hide state.
- Prefer pipelines over monoliths.
- Each component does one thing well; complex behavior emerges from combination.
- Parnas: module boundaries follow *design decisions*, not control flow.

### C9 — Tests That Specify Behavior
- Tests are the specification, not an afterthought.
- Each test exercises one behavior.
- Test names explain the scenario: `test_correction_returns_best_candidate_by_probability`.
- Edge cases (empty input, boundary values, error paths) are covered.
- Go idiom: table-driven tests (Dave Cheney / Go stdlib convention).

### C10 — Performance Is Earned, Not Assumed
- Knuth's full rule: ignore 97% of cases; measure before optimizing the 3%.
- Never sacrifice clarity for speculative performance.
- Pike rule 3: fancy data structures have a higher constant — profile first.
- A benchmark accompanies any non-obvious optimization.

---

## 3. GOLD EXAMPLES

Each example shows: the prompt, the elite implementation, and a brief annotation of which
criteria it satisfies. All code is complete and correct.

---

### Gold 1 — Python: Probabilistic Spelling Correction (Norvig)

**Prompt:**
> Write a Python spelling corrector. Given a word, return the most probable correct spelling
> using a corpus of text. Handle words that are already correct, one edit away, and two edits
> away. Include unit tests.

**Elite Implementation (Peter Norvig, 2007/2016, MIT license):**

```python
"""
Spelling corrector using a unigram language model.
Reference: http://norvig.com/spell-correct.html

Algorithm: return the known word with highest corpus probability that is
within edit distance 0, 1, or 2 of the input.
"""

import re
from collections import Counter


def words(text: str) -> list[str]:
    """Extract all lowercase alphabetic tokens from text."""
    return re.findall(r'\w+', text.lower())


def build_model(corpus_path: str) -> Counter:
    """Return a frequency table of words seen in the corpus."""
    with open(corpus_path) as f:
        return Counter(words(f.read()))


WORDS = build_model('big.txt')
_TOTAL = sum(WORDS.values())


def probability(word: str) -> float:
    """Unigram probability of word in the corpus."""
    return WORDS[word] / _TOTAL


def known(candidates: set[str]) -> set[str]:
    """Return the subset of candidates that appear in the corpus."""
    return {w for w in candidates if w in WORDS}


def edits1(word: str) -> set[str]:
    """All strings one edit (delete, transpose, replace, insert) away."""
    letters = 'abcdefghijklmnopqrstuvwxyz'
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes    = {L + R[1:]               for L, R in splits if R}
    transposes = {L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1}
    replaces   = {L + c + R[1:]           for L, R in splits if R for c in letters}
    inserts    = {L + c + R               for L, R in splits for c in letters}
    return deletes | transposes | replaces | inserts


def edits2(word: str) -> set[str]:
    """All strings two edits away from word."""
    return {e2 for e1 in edits1(word) for e2 in edits1(e1)}


def candidates(word: str) -> set[str]:
    """Generate plausible spelling corrections for word."""
    return (known({word})
            or known(edits1(word))
            or known(edits2(word))
            or {word})


def correction(word: str) -> str:
    """Most probable spelling correction for word."""
    return max(candidates(word), key=probability)


# --- Tests ---

def test_correction() -> None:
    assert correction('speling')      == 'spelling'
    assert correction('korrectud')    == 'corrected'
    assert correction('bycycle')      == 'bicycle'
    assert correction('inconvient')   == 'inconvenient'
    assert correction('word')         == 'word'           # already correct
    assert correction('quintessential') == 'quintessential'


def test_words_tokenizer() -> None:
    assert words('This is a TEST.') == ['this', 'is', 'a', 'test']


if __name__ == '__main__':
    test_correction()
    test_words_tokenizer()
    print('All tests pass.')
```

**Annotations:**
- C1: reads as a declarative description of the algorithm at each line.
- C2: `probability`, `known`, `edits1`, `candidates`, `correction` — each name is its contract.
- C3: every function is 1–6 lines; `correction` is one line.
- C4: `Counter`, `re.findall`, set comprehensions, `max(..., key=...)` — purely Pythonic.
- C5: resource opened with `with`; `open` failure propagates naturally.
- C7: correctness argument fits in one paragraph: try distance 0, then 1, then 2; pick max P.
- C8: `edits1 → edits2 → candidates → correction` is a pipeline.

---

### Gold 2 — Go: Word Frequency Counter (idiomatic)

**Prompt:**
> Write a Go program that reads text from stdin, counts word frequencies (case-insensitive),
> and prints each word with its count sorted most-frequent first. Handle errors explicitly.
> Include a table-driven test.

**Elite Implementation:**

```go
// wordfreq counts word frequencies from stdin and prints them most-frequent first.
package main

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strings"
)

// wordCount returns a map of lowercase word -> frequency for all words in r.
func wordCount(r *bufio.Scanner) map[string]int {
	counts := make(map[string]int)
	r.Split(bufio.ScanWords)
	for r.Scan() {
		counts[strings.ToLower(r.Text())]++
	}
	return counts
}

// ranked returns words sorted by descending frequency, then lexicographically.
type wordFreq struct {
	word  string
	count int
}

func ranked(counts map[string]int) []wordFreq {
	result := make([]wordFreq, 0, len(counts))
	for w, c := range counts {
		result = append(result, wordFreq{w, c})
	}
	sort.Slice(result, func(i, j int) bool {
		if result[i].count != result[j].count {
			return result[i].count > result[j].count
		}
		return result[i].word < result[j].word
	})
	return result
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	counts := wordCount(scanner)
	if err := scanner.Err(); err != nil {
		fmt.Fprintf(os.Stderr, "read error: %v\n", err)
		os.Exit(1)
	}
	for _, wf := range ranked(counts) {
		fmt.Printf("%s %d\n", wf.word, wf.count)
	}
}
```

```go
// wordfreq_test.go
package main

import (
	"bufio"
	"strings"
	"testing"
)

func TestWordCount(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  map[string]int
	}{
		{
			name:  "empty input",
			input: "",
			want:  map[string]int{},
		},
		{
			name:  "single word",
			input: "hello",
			want:  map[string]int{"hello": 1},
		},
		{
			name:  "case insensitive",
			input: "Hello hello HELLO",
			want:  map[string]int{"hello": 3},
		},
		{
			name:  "multiple words",
			input: "the cat sat on the mat",
			want:  map[string]int{"the": 2, "cat": 1, "sat": 1, "on": 1, "mat": 1},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			scanner := bufio.NewScanner(strings.NewReader(tt.input))
			got := wordCount(scanner)
			if len(got) != len(tt.want) {
				t.Errorf("got %d words, want %d", len(got), len(tt.want))
			}
			for word, count := range tt.want {
				if got[word] != count {
					t.Errorf("word %q: got %d, want %d", word, got[word], count)
				}
			}
		})
	}
}
```

**Annotations:**
- C1: `wordCount`, `ranked`, `main` each have one job, clearly named.
- C4: `bufio.Scanner.Split`, `strings.ToLower`, `sort.Slice`, error as last return, `if err != nil` — idiomatic Go throughout. Table-driven tests per Go convention (Dave Cheney / Go stdlib).
- C5: `scanner.Err()` checked; stderr + `os.Exit(1)` on failure.
- C8: scanning and ranking are separate functions, composable and independently testable.
- C3: no function exceeds 20 lines.

---

### Gold 3 — Rust: Line-counting with Proper Error Propagation

**Prompt:**
> Write a Rust command-line tool that takes a list of file paths as arguments, counts the lines
> in each file, and prints a summary. If a file cannot be opened, report the error and continue
> with the remaining files. Exit with a non-zero status if any file failed. Use idiomatic Rust
> error handling throughout.

**Elite Implementation:**

```rust
//! linecount — count lines in each file, report errors without aborting early.
//!
//! Usage: linecount <file>...

use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::Path;
use std::process;

/// Count the lines in `path`, returning the count or an IO error.
fn count_lines(path: &Path) -> io::Result<usize> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    Ok(reader.lines().count())
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();

    if args.is_empty() {
        eprintln!("usage: linecount <file>...");
        process::exit(2);
    }

    let mut had_error = false;

    for arg in &args {
        let path = Path::new(arg);
        match count_lines(path) {
            Ok(n) => println!("{:>8}  {}", n, path.display()),
            Err(e) => {
                eprintln!("linecount: {}: {}", path.display(), e);
                had_error = true;
            }
        }
    }

    if had_error {
        process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn counts_lines_correctly() {
        let mut f = NamedTempFile::new().unwrap();
        writeln!(f, "one\ntwo\nthree").unwrap();
        // writeln adds a trailing newline, so "one\ntwo\nthree\n" = 3 lines
        let n = count_lines(f.path()).unwrap();
        assert_eq!(n, 3);
    }

    #[test]
    fn empty_file_is_zero_lines() {
        let f = NamedTempFile::new().unwrap();
        assert_eq!(count_lines(f.path()).unwrap(), 0);
    }

    #[test]
    fn missing_file_returns_error() {
        let result = count_lines(Path::new("/nonexistent/path/file.txt"));
        assert!(result.is_err());
    }
}
```

**Annotations:**
- C4: `?` propagates `io::Result`; `BufReader` + `.lines().count()` is the idiomatic iterator pipeline; `match` on `Result` at the call site; no `unwrap()` in non-test code.
- C5: errors are never swallowed — each file failure is reported and tallied; exit code reflects reality.
- C3: `count_lines` is 4 lines; it does exactly one thing.
- C7: the correctness argument is trivial — open, wrap, count, done.
- C8: `count_lines` is a pure I/O function; the loop in `main` is the imperative shell (Bernhardt's functional core / imperative shell pattern).

---

### Gold 4 — C: Safe String Tokenizer (Kernighan/Ritchie style)

**Prompt:**
> Write a C function that splits a string into tokens on a given delimiter character, storing
> pointers into the original buffer (no allocation). The caller supplies a fixed-size array of
> token pointers and the array capacity. Return the number of tokens found, or -1 if the array
> is too small. Document the ownership contract.

**Elite Implementation:**

```c
/*
 * split_tokens — in-place string tokenizer, no heap allocation.
 *
 * Splits `str` by `delim`, writing pointers to each token into `tokens[0..n-1]`
 * and NUL-terminating each token in place. The caller owns `str` and must ensure
 * it remains live for the lifetime of the returned token pointers.
 *
 * Parameters:
 *   str      — input string, modified in place (delimiters replaced with '\0').
 *   delim    — delimiter character.
 *   tokens   — caller-supplied array to receive token pointers.
 *   capacity — number of slots in tokens[].
 *
 * Returns:
 *   Number of tokens found, or -1 if tokens[] overflows.
 *
 * Ownership: tokens[i] points into str; do not free tokens[i] separately.
 */
int split_tokens(char *str, char delim, const char **tokens, int capacity)
{
    int n = 0;

    while (*str != '\0') {
        /* skip leading delimiters */
        while (*str == delim)
            str++;

        if (*str == '\0')
            break;

        /* record start of token */
        if (n >= capacity)
            return -1;
        tokens[n++] = str;

        /* advance to end of token */
        while (*str != '\0' && *str != delim)
            str++;

        /* terminate token and step past delimiter */
        if (*str == delim) {
            *str = '\0';
            str++;
        }
    }

    return n;
}


/* ---- Tests (compile with -DRUN_TESTS) ---- */
#ifdef RUN_TESTS
#include <assert.h>
#include <string.h>
#include <stdio.h>

static void test_basic_split(void)
{
    char input[] = "one,two,three";
    const char *tokens[8];
    int n = split_tokens(input, ',', tokens, 8);
    assert(n == 3);
    assert(strcmp(tokens[0], "one")   == 0);
    assert(strcmp(tokens[1], "two")   == 0);
    assert(strcmp(tokens[2], "three") == 0);
}

static void test_leading_and_trailing_delimiters(void)
{
    char input[] = ",,,hello,world,,";
    const char *tokens[8];
    int n = split_tokens(input, ',', tokens, 8);
    assert(n == 2);
    assert(strcmp(tokens[0], "hello") == 0);
    assert(strcmp(tokens[1], "world") == 0);
}

static void test_capacity_overflow(void)
{
    char input[] = "a,b,c,d";
    const char *tokens[2];
    int n = split_tokens(input, ',', tokens, 2);
    assert(n == -1);
}

static void test_empty_string(void)
{
    char input[] = "";
    const char *tokens[8];
    int n = split_tokens(input, ',', tokens, 8);
    assert(n == 0);
}

int main(void)
{
    test_basic_split();
    test_leading_and_trailing_delimiters();
    test_capacity_overflow();
    test_empty_string();
    puts("All tests pass.");
    return 0;
}
#endif /* RUN_TESTS */
```

**Annotations:**
- C1: two-level loop with comments explaining each phase; reads like a description of the algorithm.
- C2: `split_tokens`, `capacity`, `delim` — every name explains intent.
- C4: C idioms — pointer walk, in-place NUL termination, no malloc. `const char **` signals that tokens are read-only to the caller. Ownership contract documented in the header comment (Parnas: document the interface contract explicitly).
- C5: overflow returns -1 immediately; no silent truncation.
- C6: no speculative abstraction — one function, no object, no vtable.
- C7: correctness argument: skip delimiters → record start → advance past token → terminate. Each phase does exactly one thing.

---

### Gold 5 — Python: Retry Decorator with Exponential Backoff

**Prompt:**
> Write a Python decorator `retry` that retries a function call up to `max_attempts` times,
> with exponential backoff starting at `base_delay` seconds. Accept a tuple of exception types
> to retry on. On final failure, re-raise the last exception. Log each retry. Include tests that
> do not require sleeping.

**Elite Implementation:**

```python
"""
retry — a decorator for fault-tolerant function calls with exponential backoff.

Usage:
    @retry(max_attempts=3, base_delay=1.0, exceptions=(RequestException,))
    def fetch(url: str) -> Response: ...
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

log = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0,
) -> Callable[[F], F]:
    """
    Retry `func` up to `max_attempts` times on the given exception types.

    Delay between attempts follows: base_delay * (backoff_factor ** attempt_index).
    On final failure, the last exception is re-raised unchanged.

    Args:
        max_attempts:   Maximum number of total calls (including the first).
        base_delay:     Initial wait time in seconds.
        exceptions:     Exception types that trigger a retry.
        backoff_factor: Multiplier applied to delay after each failure.
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be >= 1, got {max_attempts}")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = base_delay
            last_exc: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts - 1:
                        log.warning(
                            "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                            func.__qualname__, attempt + 1, max_attempts, exc, delay,
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        log.error(
                            "%s failed after %d attempts: %s",
                            func.__qualname__, max_attempts, exc,
                        )

            raise last_exc  # type: ignore[misc]  # always set; loop ran >= 1 time

        return wrapper  # type: ignore[return-value]

    return decorator


# ---- Tests ----

import pytest
from unittest.mock import patch, call


def test_succeeds_on_first_attempt():
    calls = []

    @retry(max_attempts=3)
    def ok():
        calls.append(1)
        return 42

    assert ok() == 42
    assert len(calls) == 1


def test_retries_then_succeeds():
    attempt = [0]

    @retry(max_attempts=3, base_delay=0)
    def flaky():
        attempt[0] += 1
        if attempt[0] < 3:
            raise ValueError("not yet")
        return "done"

    with patch('time.sleep'):
        result = flaky()

    assert result == "done"
    assert attempt[0] == 3


def test_raises_after_max_attempts():
    @retry(max_attempts=2, base_delay=0)
    def always_fails():
        raise RuntimeError("boom")

    with patch('time.sleep'), pytest.raises(RuntimeError, match="boom"):
        always_fails()


def test_only_retries_specified_exceptions():
    @retry(max_attempts=3, base_delay=0, exceptions=(ValueError,))
    def wrong_exc():
        raise TypeError("wrong type")

    with pytest.raises(TypeError):
        wrong_exc()


def test_invalid_max_attempts():
    with pytest.raises(ValueError):
        @retry(max_attempts=0)
        def f(): pass


def test_backoff_delays():
    delays_slept = []

    @retry(max_attempts=3, base_delay=1.0, backoff_factor=2.0)
    def always_fails():
        raise ValueError("x")

    with patch('time.sleep', side_effect=lambda d: delays_slept.append(d)):
        with pytest.raises(ValueError):
            always_fails()

    assert delays_slept == [1.0, 2.0]  # attempt 0→1 sleep 1.0, attempt 1→2 sleep 2.0
```

**Annotations:**
- C1: the wrapper's for-loop reads: try → if exception and not last attempt → log + sleep + double delay → else log final failure → raise.
- C2: `max_attempts`, `base_delay`, `backoff_factor`, `last_exc`, `wrapper` — no ambiguity.
- C3: each function does one thing; decorator/wrapper are separated; config validation is at decoration time.
- C4: `functools.wraps`, `TypeVar`, `tuple[type[Exception], ...]`, `logging.getLogger(__name__)`, `pytest.raises` — idiomatic Python throughout.
- C5: the last exception is re-raised unchanged — callers see the original traceback, not a wrapped one.
- C9: tests exercise success, retry-then-success, total failure, wrong exception type, invalid config, and backoff delays — behavior specification, not coverage.
- C10: no time.sleep in tests (`patch`); tests run instantly.

---

## 4. ELITENESS AUDIT (Python pseudocode)

This audit gates a code candidate before it is accepted as SFT gold. It returns a score
and a list of failures for rejection reasons. Candidates below the threshold are rejected
and optionally queued for a repair pass.

```python
"""
elite_audit.py — gate for SFT gold code samples.

Usage:
    result = audit(prompt, code, language)
    if result.score < ACCEPT_THRESHOLD:
        reject(result.failures)
"""

from __future__ import annotations
import ast
import re
import difflib
from dataclasses import dataclass, field


ACCEPT_THRESHOLD = 0.75   # fraction of criteria that must pass
DEGENERATION_WINDOW = 120 # characters; repeated substring detection window


@dataclass
class AuditResult:
    score: float                        # 0.0 – 1.0
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return self.score >= ACCEPT_THRESHOLD


def audit(prompt: str, code: str, language: str) -> AuditResult:
    """Run all criteria checks and return an AuditResult."""
    checks = [
        _check_not_empty(code),
        _check_no_dead_code(code, language),
        _check_no_swallowed_errors(code, language),
        _check_function_size(code, language),
        _check_name_quality(code, language),
        _check_idiomatic_patterns(code, language),
        _check_has_test_or_example(code, language),
        _check_no_degeneration(code),
        _check_answers_prompt(prompt, code),
        _check_no_nonname_names(code),
    ]

    passed = [name for name, ok in checks if ok]
    failed = [name for name, ok in checks if not ok]
    score = len(passed) / len(checks) if checks else 0.0

    return AuditResult(score=score, passed=passed, failed=failed)


# ---- Individual checks ----

def _check_not_empty(code: str) -> tuple[str, bool]:
    name = "C0_not_empty"
    return name, len(code.strip()) > 50


def _check_no_dead_code(code: str, language: str) -> tuple[str, bool]:
    """Fail if there are commented-out code blocks."""
    name = "C6_no_dead_code"
    # Heuristic: multiple consecutive comment lines containing code syntax
    if language == 'python':
        dead = re.search(r'(#[^\n]*\n){3,}', code)
        return name, dead is None
    if language in ('rust', 'go', 'c'):
        dead = re.search(r'(/[^\n]*\n){3,}', code)
        return name, dead is None
    return name, True


def _check_no_swallowed_errors(code: str, language: str) -> tuple[str, bool]:
    """Fail on except:pass, unwrap() without comment, or empty catch blocks."""
    name = "C5_errors_not_hidden"
    if language == 'python':
        # bare except or except Exception with pass
        bad = re.search(r'except\s*(Exception)?\s*:\s*\n\s*pass', code)
        return name, bad is None
    if language == 'rust':
        # unwrap() in non-test code (allow in #[cfg(test)] or #[test])
        # Simple heuristic: count unwrap() calls outside test blocks
        non_test = re.sub(r'#\[cfg\(test\)\][^}]*}', '', code, flags=re.DOTALL)
        non_test = re.sub(r'#\[test\][^}]*}', '', non_test, flags=re.DOTALL)
        bad = re.search(r'\.unwrap\(\)', non_test)
        return name, bad is None
    if language == 'go':
        # check for ignored error: assign to blank without comment
        bad = re.search(r',\s*_\s*:?=\s*\w+\(', code)
        return name, bad is None
    return name, True


def _check_function_size(code: str, language: str) -> tuple[str, bool]:
    """Warn if any function body exceeds 50 lines (hard fail at 80)."""
    name = "C3_small_functions"
    if language == 'python':
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return name, False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or 0) - node.lineno
                if length > 80:
                    return name, False
        return name, True
    # For other languages: rough line count per function
    if language in ('rust', 'go', 'c'):
        blocks = re.findall(r'\{([^{}]*)\}', code, re.DOTALL)
        for block in blocks:
            if block.count('\n') > 80:
                return name, False
    return name, True


def _check_name_quality(code: str, language: str) -> tuple[str, bool]:
    """Fail on single-character names outside math loops, or 'data'/'info' as primary names."""
    name = "C2_good_names"
    bad_names = {'data', 'info', 'temp', 'tmp', 'val', 'ret', 'res', 'obj', 'mgr', 'util'}
    if language == 'python':
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return name, False
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in bad_names:
                return name, False
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in bad_names:
                    return name, False
    return name, True


def _check_idiomatic_patterns(code: str, language: str) -> tuple[str, bool]:
    """Spot-check for language-idiomatic patterns being used."""
    name = "C4_idiomatic"
    if language == 'python':
        # Good: context managers, comprehensions, or stdlib collections
        has_with   = 'with ' in code
        has_comp   = ('[' in code and ' for ' in code) or ('{' in code and ' for ' in code)
        has_stdlib = any(m in code for m in ('collections', 'itertools', 'functools',
                                              'pathlib', 'dataclass', 'typing'))
        return name, has_with or has_comp or has_stdlib
    if language == 'rust':
        # Good: Result/Option, iterator chains, ? operator
        has_result = 'Result<' in code or 'Option<' in code
        has_iter   = any(p in code for p in ('.map(', '.filter(', '.collect(', '.fold('))
        has_q      = '?' in code
        return name, has_result or has_iter or has_q
    if language == 'go':
        # Good: error return, defer, goroutines or channels
        has_err    = 'error' in code and 'err != nil' in code
        has_defer  = 'defer ' in code
        return name, has_err or has_defer
    return name, True


def _check_has_test_or_example(code: str, language: str) -> tuple[str, bool]:
    """Require at least one test or assertion in the submission."""
    name = "C9_has_tests"
    if language == 'python':
        has_test = 'def test_' in code or 'assert ' in code or 'doctest' in code
        return name, has_test
    if language == 'rust':
        has_test = '#[test]' in code or 'assert!' in code or 'assert_eq!' in code
        return name, has_test
    if language == 'go':
        has_test = 'func Test' in code or 't.Error' in code or 't.Fatal' in code
        return name, has_test
    if language == 'c':
        has_test = 'assert(' in code or 'RUN_TESTS' in code
        return name, has_test
    return name, True


def _check_no_degeneration(code: str) -> tuple[str, bool]:
    """
    Repetition / degeneration guard.

    Fail if any substring of length >= DEGENERATION_WINDOW appears
    more than twice (suggests a stuck generation loop).
    Also fail if the code is >90% whitespace or comment lines.
    """
    name = "DEGEN_no_repetition"

    # Check repeated substrings
    window = DEGENERATION_WINDOW
    seen: dict[str, int] = {}
    for i in range(0, len(code) - window, window // 2):
        chunk = code[i:i + window]
        seen[chunk] = seen.get(chunk, 0) + 1
        if seen[chunk] > 2:
            return name, False

    # Check comment/whitespace ratio
    lines = code.splitlines()
    if not lines:
        return name, False
    comment_or_blank = sum(
        1 for ln in lines
        if not ln.strip() or ln.strip().startswith(('#', '//', '/*', '*'))
    )
    if comment_or_blank / len(lines) > 0.9:
        return name, False

    return name, True


def _check_answers_prompt(prompt: str, code: str) -> tuple[str, bool]:
    """
    Semantic relevance: extract key nouns/verbs from prompt and check they
    appear (or close synonyms) in code or comments.

    This is a lightweight heuristic, not a full semantic check.
    Replace with embedding cosine similarity for production use.
    """
    name = "C0_answers_prompt"
    # Extract lowercase alpha tokens from prompt (>3 chars)
    prompt_tokens = {t.lower() for t in re.findall(r'[a-zA-Z]{4,}', prompt)}
    code_lower = code.lower()
    # At least 30% of prompt tokens should appear somewhere in the code
    matches = sum(1 for t in prompt_tokens if t in code_lower)
    ratio = matches / len(prompt_tokens) if prompt_tokens else 1.0
    return name, ratio >= 0.30


def _check_no_nonname_names(code: str) -> tuple[str, bool]:
    """Fail if common anti-names appear as identifiers."""
    name = "C2_no_nonnames"
    anti_patterns = [
        r'\bdo_stuff\b', r'\bdo_thing\b', r'\bprocess_it\b',
        r'\bhandle_it\b', r'\bmy_function\b', r'\bfoo\b', r'\bbar\b',
        r'\bbaz\b',
    ]
    for pat in anti_patterns:
        if re.search(pat, code):
            return name, False
    return name, True


# ---- Batch usage example ----

def filter_gold(samples: list[dict]) -> list[dict]:
    """
    Given a list of {'prompt': str, 'code': str, 'language': str} dicts,
    return only those that pass the audit.
    """
    accepted = []
    for sample in samples:
        result = audit(sample['prompt'], sample['code'], sample['language'])
        if result.accepted:
            accepted.append({**sample, 'audit_score': result.score})
        else:
            print(f"REJECTED (score={result.score:.2f}): {result.failed}")
    return accepted
```

---

## 5. REFERENCES

Primary sources this document draws from directly:

- Kernighan & Plauger, *The Elements of Programming Style* (1974)
- Kernighan & Pike, *The Practice of Programming* (1999)
- Knuth, "Structured Programming with Go To Statements," *ACM Computing Surveys* (1974)
- Knuth, "Literate Programming," *The Computer Journal* (1984)
- Dijkstra, "The Humble Programmer," ACM Turing Award Lecture (1972)
- Hoare, "The Emperor's Old Clothes," ACM Turing Award Lecture (1980)
- Parnas, "On the Criteria To Be Used in Decomposing Systems into Modules," *CACM* (1972)
- Brooks, *The Mythical Man-Month* (1975, 1995)
- McIlroy, "Unix Time-Sharing System: Foreword," *Bell System Technical Journal* (1978)
- Norvig, "How to Write a Spelling Corrector," norvig.com (2007, updated 2016)
- Hickey, "Simple Made Easy," Strange Loop (2011); QCon London (2012)
- Armstrong, "Making Reliable Distributed Systems in the Presence of Software Errors," PhD thesis, KTH (2003)
- Carmack, "Functional Programming in C++" (2012), archived at sevangelatos.com
- Torvalds, TED interview on "good taste" in code (2016)
- Go team, *Effective Go*, go.dev/doc/effective_go
- Cheney, "Prefer Table Driven Tests," dave.cheney.net (2019)
- Cheney, "The Zen of Go," dave.cheney.net (2020)
- Bernhardt, "Functional Core, Imperative Shell," destroyallsoftware.com (2012)
- Ben Hoyt, "Performance Comparison: Counting Words in Python, Go, C++, C, AWK, Forth, and Rust," benhoyt.com (2021)
- Tim Peters, *The Zen of Python*, PEP 20 (1999/2004)
