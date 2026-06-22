<!-- Strunk & White / Zinsser / Orwell: omit needless words; plain, specific, active; no slop, no hedging. -->

The parser reads one token at a time. When it meets a token it cannot place, it stops and reports the line.
It does not guess.

This makes errors easy to find. The failure is always where the parser stopped — never three steps later,
never in a place you have to reason backward to reach. You read the line number, you look at the line, you
fix it. The parser's refusal to guess is not a limitation; it is the feature that makes it trustworthy.
