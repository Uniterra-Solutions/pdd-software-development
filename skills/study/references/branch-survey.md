# Surveying branches fast

`references/branch-inventory.md` says what a branch row must contain. This file says how to find the branches
without reading the whole directory from the top, and when to stop.

The failure this prevents: an agent reads files linearly, transcribes every `if` it passes, and produces fifty
rows of which six change anything a caller can see — while the enum that actually selects the behaviour sits
unread in another file.

## 1. The filter, applied in five seconds

A candidate earns a row when the caller can tell which way it went. Ask three questions, and answer them in the
order that fails fastest:

1. **What are the outcomes?** If you cannot name two, it is not a branch.
2. **What does the caller observe differently?** Response, field, side effect, file, metric, failure mode.
3. **If nothing differs, does it decide which of the above happens?** A cache lookup decides latency, not
   output — exclude it, and say so.

No answer within five seconds → excluded, and the condition goes into the excluded list with one clause. The
list is what separates "no branch here" from "nobody looked".

## 2. Survey order, breadth first

Read in this order, and stop each pass when the next file stops adding rows:

| Pass | What you are looking for | Where it usually lives |
| --- | --- | --- |
| 1 | **entry points** — the invocations a caller can make | `main`, route registration, exported handlers, CLI parsers, message consumers |
| 2 | **the selection surface** — the enum, config struct or router table that decides between them | the type definitions, `config`/`settings` module, the router module |
| 3 | **the decision sites** — where that surface is read | the files the entry point reaches, not the whole directory |
| 4 | **the guards** — size, quota, auth, feature gates | middleware, `limits`/`policy` modules, build config |
| 5 | **the failures** — which error class produces which response | the error enum, the response mapper |

Passes 2 and 5 are the ones that get skipped, and they are the ones that make the survey fast: **an enum's
variant list is a branch list**, and **an error enum's variants on the public path are the rejection rows**. Read
those two files first and the grep work in pass 3 becomes verification instead of discovery.

## 3. Grep cheat sheet

The patterns below find the *candidates*; the five-second filter decides which become rows. `rg` is ripgrep
(`rg -n`), which is faster than `grep -rn` on a large tree.

| Ecosystem | Entry points | Decision sites | Configuration |
| --- | --- | --- | --- |
| Rust | `rg -n 'fn main\|#\[tokio::main\]\|pub (async )?fn (new\|run\|handle\|serve)'` | `rg -n '\bmatch\b\|\bif\b\|\belse if\b'`, plus `rg -n '#\[cfg'` for build gates | `rg -n 'env::var\|Config::default\|serde\(default'` |
| TypeScript | `rg -n 'export default\|export (async )?function\|\.(get\|post\|put\|delete)\(.*=>'` | `rg -n '\bswitch\b\|\bcase \|!==\?\?\|&&\|\|\|'` | `rg -n 'process\.env\|import\.meta\.env\|z\.object'` |
| Python | `rg -n '^def (main\|run\|handle)\|@app\.(get\|post)\|@router\.'` | `rg -n '^\s*(if\|elif\|match) '` | `rg -n 'os\.environ\|getenv\|BaseSettings\|load_config'` |
| Go | `rg -n 'func main\|HandleFunc\|http\.Handle\|\.(GET\|POST)\('` | `rg -n '\bswitch\b\|\bcase \|if err != nil'` | `rg -n 'os\.Getenv\|flag\.\|viper\.'` |
| Java/Kotlin | `rg -n '@(Get\|Post)Mapping\|public static void main\|@RestController'` | `rg -n '\bswitch\b\|\bwhen \|if \('` | `rg -n '@Value\|getProperty\|@ConfigurationProperties'` |

Then narrow by the config key, because the default is half the trigger:

```
rg -n 'MAX_BODY|max_body' src/            # where the constant is defined and where it is read
rg -n 'streaming' -g '!target' -g '!node_modules'
```

Two cheap habits that pay for themselves:

- **`rg -c` before reading.** Ten hits is a read; four hundred hits is a filter problem — narrow by file.
- **Read the type definitions, then jump.** `Mode`, `Config`, `*Error`, the router table: four files that
  usually contain most of the branch structure of the directory.

## 4. When the survey is done

"Done" is not "I have read enough". It is a set of counts that either match or are explained:

- [ ] every **route / exported handler / bin target / subscription** has at least one row, including its default;
- [ ] every **variant of the deciding enum** is either a row or in the excluded list with a reason;
- [ ] every **field of the config struct that is read in this directory** appears in some row's trigger, or is
      excluded as non-observable;
- [ ] every **error variant on the public path** maps to a row (that is where the rejection branches come from);
- [ ] every **`match`/`switch` arm on the public path** is accounted for, one way or the other;
- [ ] each pass in §2 was run, and each file you skipped was skipped for a stated reason.

When those six hold, more reading adds prose, not rows. Stop, write, and spend the remaining effort on the
trigger quotes — a table whose predicates are copied verbatim is worth more than one with twice the rows.

## 5. Anti-patterns that cost the most time

- **Linear reading.** From the top of the first file to the bottom of the last: the paths that matter are
  scattered, and the files that define the behaviour (types, config, router) are read last.
- **Counting `if`s.** `rg -c '\bif\b'` produces a number that is neither the branch count nor the work left. The
  filter, not the grep, decides.
- **Documenting the framework.** "Axum routes the request to the handler" is true of every Axum app and tells
  the next agent nothing. Start where the framework stops.
- **Treating tests as the spec.** Tests are evidence of intent; the code is the authority. A test that asserts
  something the code no longer does is a finding, not a row.
- **Chasing every error path.** A `?` that propagates a `DatabaseError` is one row ("dependency failure →
  500"), not one row per call site.
- **Reading the whole dependency tree.** A branch owned by another member is a `cross:` note and a report line;
  the other member's study owns the row.
- **Stopping at the first plausible table.** The §4 counts exist because the first table is always missing the
  default path — the arm reached when nothing matches, which is the branch nobody documents and everybody
  depends on.
