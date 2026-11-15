# Plain-Language Lexicon

§2 of this file is the banlist, so a new term enters the ban the moment its row lands here, and adding a
row is the whole fix. §3 and §4 guide the rewrite and are read by the writer, not by any tool. Backticked
strings and appendix A stay exempt, because a quoted original is text the reader will meet verbatim.

## 1. The test

A word is jargon if an intelligent reader from outside software would have to ask about it — not if a
dictionary contains it. "Table" is fine; "schema" is not. "Copy" is fine; "cache" is not.

## 2. Banned terms and their replacements

| Technical term | Plain language |
| --- | --- |
| API / endpoint / route | the window opened to the outside: who can send what in from where, and get what back |
| schema / model / DTO | which columns this table has, what goes in each column, which columns cannot be empty |
| database / table / row | ledger / one account book / one line of record |
| migration | moving house: old data turned into the new format, and nothing may drop on the way |
| cache | a copy left lying around; once it is out of date you have to fetch it again |
| index | table of contents |
| queue / worker / job | the slips that queue up / who goes and handles them / one thing done on a timer or on demand |
| idempotent | do the same thing twice, the result is the same as doing it once |
| race condition / lock / mutex | when two things happen at once they step on each other; only one may come in at a time |
| transaction / atomic | either the whole entry succeeds, or the whole entry does not count |
| timeout / retry / backoff | wait too long and it counts as not received / send it again / wait longer and longer before sending again |
| token / session / auth | pass / the credential for coming in this time / verify identity |
| permission / role / RBAC | who is allowed to do what / position / give permissions by position |
| hash / signature / encrypt | fingerprint / signature / put a lock on it |
| regex / parse / serialize | a pattern for comparing strings / read a piece of text / turn it into a storable form |
| refactor | the outside stays the same, the inside is swapped |
| deploy / rollback / release | go live / go back to the previous version / publish |
| CI / pipeline / test runner | the whole set of checks that re-runs automatically on every change |
| unit test / mock / fixture / stub | a small drill / a stand-in opponent / a stage set up in advance |
| coverage | how many kinds of situation the drill covers |
| DAG / dependency / wave | the order chart of who must finish first / what comes before and after / batches that can be done at the same time |
| invariant | a rule that never changes at any time |
| requirement / spec / contract | requirement / standard / what the two sides agreed |
| latency / p99 / throughput | how long the slowest batch has to wait / how much can be handled within a given time |
| flag / config key / env var | switch / setting item |
| log / metric / alert | record / numeric indicator / notification |
| error variant / exception | which kind of error the system reports when something goes wrong |
| feature branch / PR / merge | open another road and try it out / send it for review / merge |
| feature flag / canary | a switch given only to some people first |
| cron / scheduler | do it automatically on a timer |
| dry run | one empty run, without actually changing anything |
| sandbox / staging | practice ground / trial venue |
| landing / empowerment / unblock / alignment / closed loop | delete it, replace with "who does one more or one fewer thing, and where" |

## 3. Boundary cases in plain words

The plan's boundary taxonomy is precise and unreadable. Translate, do not drop:

| Original | Plain language |
| --- | --- |
| empty / absent | not a single one / the thing is not there |
| min / single | only one entry |
| max / at limit | filled to the limit; one more cannot get in |
| duplicate | the same thing sent twice |
| out-of-order | the order is reversed; the one sent later arrives first |
| malformed | the data is incomplete, the format is wrong |
| partial failure | it breaks off halfway; the front part got done, the back part did not |
| concurrent | two people doing the same thing at the same time |
| stale / version skew | what he is holding is an old version of the data |
| unauthorized | someone without a pass comes knocking |

## 4. Banned sentence shapes

| Don't write | Because | Rewrite |
| --- | --- | --- |
| the system will handle it automatically | nobody knows what a refusal looks like | who is refused under what condition, and what he sees |
| under normal circumstances | sweeping the boundary under the carpet | state that abnormal condition |
| in theory / should / basically | the reader cannot verify it | give a number or one observable event |
| specifically (followed by empty talk) | pretending to be concrete | replace with a scene |
| greatly improved / more stable | no counterpart | how long the wait is, how often it breaks, what happens with twice as many people |
| leaving room for later expansion | trading the future for approval now | how much more is paid now, under what condition it would even be used |

## 5. What may stay in the original

Only strings the reader will personally meet: a file name, a command he will type, an error line on
screen, a field label on a form. Each appears once, in backticks, followed immediately by its plain
meaning. Ids (`REQ-…`, `D1`, `P1`, `T1`) are labels, not jargon, and stay unglossed.
