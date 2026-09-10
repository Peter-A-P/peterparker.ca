Every team that ships AI has the same argument. Somebody changes a prompt, or the vendor
releases a new model version, and the evaluation score moves from 86 to 83. Is that a
regression, or is it nothing? The meeting goes in circles, because nobody in the room can
answer it and the number has no error bars to settle it with.

It cannot be settled, because three points of movement is roughly what you get from doing
nothing at all.

Ask one model the same question five times and you will not get the same answer five
times. Run the same evaluation twice against an unchanged system and the score moves.
Almost nobody measures that baseline wobble, so every reported number carries an unknown
amount of noise, and no comparison against it can be trusted in either direction. Teams
block changes that were fine and ship changes that were not, and both mistakes look
identical on the dashboard.

| Why an evaluation score moved | A real change? | How you would know |
|---|---|---|
| The model's own randomness, call to call | No | Ask the same model the same question several times in one sitting |
| The serving stack: hardware, provider, routing | No | Run a model whose weights physically cannot change, as a control |
| The vendor quietly changed the model behind a pinned name | Yes | Both floors above, measured first, on a test that never changes |
| The prompt or model your team deliberately changed | Yes, and this is the one you meant to measure | All of the above, then a paired test with a confidence interval |

The last row is what a release gate is for. The first three rows are why most release
gates do not work.

There is a second version of the same problem, one level up from any single team. When you
call a vendor model by a pinned, dated name, the date is a promise that the thing behind it
does not change. Teams keep reporting that behaviour shifts anyway: something that worked
in March stops working in June. Nobody can prove it, because proving it would mean having
run the same fixed test every month since before the shift, and that record does not exist
in public. It also cannot be made after the fact. Either somebody was measuring all along,
or the evidence is gone.

This project builds both halves, in one repository.

The first half is that missing record: a fixed set of about 420 test questions, frozen so
that they can never be edited, sent every month for twelve months to eight model
configurations across the three major vendors plus an open-weights control, five times
each, graded by plain programs rather than by another AI. Every raw response is committed,
so anyone can regenerate every published number offline without spending a cent. Where a
model has moved, the record says by how much and against what noise floor. Where it has
not moved, that is published too.

The second half is the gate itself: the same machinery pointed at a team's own prompt and
model changes and wired into continuous integration, so that a change which has provably
regressed cannot be merged. Not "the score went down", which is noise most of the time,
but a one-sided statistical test against a tolerance the team sets, with an audit trail of
every decision that a regulator could read.

**Where this stands in September 2026: in progress.** The runner, the graders, the
statistics and the monthly job are built and tested. The frozen question set is being
written now, and the first official run is targeted for 27 September 2026. Nothing is
measured yet, and the results table in the repository is empty until it is. The gate itself
is built between December 2026 and January 2027, and the repository becomes public when it
has numbers in it.

<!-- more -->

## Measuring the noise before measuring the change

Every question is sent five times to every model in the same run, shuffled so that the
repeats are spread across the run rather than fired back to back. That produces two
different numbers, where most evaluations have only one:

- **The same-day flip rate.** How often a question's grade changes across those five
  repeats, within a single run, on a model that by definition has not changed. This is
  pure noise, and it is the floor.
- **The month-over-month flip rate.** How often a question's grade changes between last
  month and this month, paired question by question.

Drift is declared only when the second exceeds the upper bound of the first. Both numbers
are printed next to each other in every report, so that a reader can check the call rather
than take it. Without a noise floor every month looks like drift and none of it can be
defended, which is the flaw in most public claims that a model got worse.

There is a second floor. One of the eight arms is an open-weights model with a fixed
checkpoint hash: a file whose contents cannot change. Anything that moves in that arm is
infrastructure, not intelligence. A vendor's model has to clear both floors before the
record says it drifted.

A third check is built into the calendar. The first two full runs are four days apart, at
the end of September and the start of October 2026. Four days is not enough time for a
vendor to change anything, so whatever gap appears between those two runs is a between-run
noise estimate, measured before the record properly begins. It anchors every drift call in
the twelve months that follow.

## Why no AI grades anything in the first half

Using a language model as a judge is the ordinary way to score open-ended output, and it is
excluded here on purpose. A judge drifts too. Its drift would be indistinguishable from the
drift being measured, so the exercise would amount to measuring a moving thing with a
moving ruler and reporting the sum of the two.

So every question in the frozen set is graded by a deterministic program: numeric match
with a tolerance, multiple-choice letter match, JSON schema validation with exact field
values, a constraint checker for instruction following, a visible regular-expression
classifier for refusals. Every grader is tested against deliberately awkward output:
markdown code fences, trailing chatter, unicode digits, empty strings.

The cost of that decision is real, and it is stated in the repository rather than buried.
This half measures capability, instruction following, formatting and refusal behaviour. It
does not measure whether an answer was well written. That needs a judge, and a judge is
only allowed in once it has been calibrated, which is the second half of the project.

## Three kinds of arm, and none of them tuned

Eight model configurations, of three kinds. A **snapshot** arm calls a dated, pinned
identifier and asks whether frozen means frozen. An **alias** arm calls the vendor's
floating "latest" name for the same model family and asks how far it wanders from its
pinned twin. The **control** arm is the fixed-weights model described above.

The list of identifiers is treated as data, not as configuration. They are chosen on the
first run day from each vendor's own published model list, written down with the date, and
never adjusted afterwards to make a result look better. When a vendor retires an identifier
mid-year, the runner keeps calling it and records the error as the result, because a
retirement is a finding about the vendor rather than a bug in the harness.

Everything else is nailed down, so that only the vendor can be the variable: temperature
zero, fixed token limits, fixed system prompts, no tools, no vendor-side caching, raw HTTP
with pinned API version headers rather than vendor client libraries, and the same runner
image at the same time of day every month. Caching is banned outright on the monthly run.

## The contamination control

Public benchmark questions have a specific failure mode over twelve months. If a score
climbs, is the model better, or did those questions leak into its training data?

Answering that needs a control group, so twenty of the hand-written questions are held out.
Their cryptographic hashes are committed to the public repository on day one; the questions
themselves are kept outside it until month twelve. The runner refuses to start unless what
it is handed matches those committed hashes exactly, in both directions. Their results are
published every month alongside the public ones, but with the model's output replaced by a
hash, so that the grade counts towards the statistics while the question itself stays
secret.

Public accuracy climbing while held-out accuracy stays flat is evidence of contamination
rather than capability, and the monthly report puts the two side by side so that the gap is
visible rather than arguable.

## The record has to survive being checked

The question set is content-hashed, and the hash is printed in every report. Changing a
question is not an edit; it creates a new version of the set, which is run alongside the old
one for a bridging month. When a result looks wrong, the rule is that the question set does
not move: a wrong-looking result is a finding.

The record is append-only. Nothing in it is ever rewritten or deleted, and a bad run is
marked as bad rather than removed. Because every raw response is stored, one command
re-grades a whole month from disk without calling any vendor, which does two jobs at once. A
stranger can verify every published figure for free, and a grader bug discovered in month
eight can be corrected across all eight months instead of invalidating them.

## From a record to a gate

The second half reuses all of that and adds the parts a team needs in order to block a bad
change.

**The test is non-inferiority, not improvement.** A gate is not asking "is this better", it
is asking "did this get worse by more than we tolerate". So the check is one-sided, paired
question by question, and a change fails when the lower bound of the interval falls past the
tolerance. The pairing matters more than it sounds: questions differ from one another far
more than prompt versions do, and an unpaired comparison throws that information away.

**The judge is treated as an instrument and calibrated like one.** Open-ended quality does
need a model judge, so before it is allowed to score anything it is run against several
hundred answers labelled by hand against a written rubric. Its agreement with those labels
is measured, its sensitivity and specificity are measured, it is checked for position bias
and for rewarding length, and the pass rate it reports is corrected for its own measured
error rate and shown next to the uncorrected one. A judge that does not agree with human
labels well enough is refused for that task rather than used anyway.

**The false-block rate is measured, not assumed.** The gate is run with the same prompt and
the same model on both sides, fifty times. Every block is a false block. That number is
published, because a gate that blocks harmless changes gets switched off within a month, and
it is the single figure that decides whether the thing is usable at all.

**Every decision is auditable by construction.** Each run appends one record holding the
content hashes, the model identifiers, the request settings, the grader versions, the raw
responses, the statistics, and the decision with its reasons. Nothing is ever edited; a
mistake is corrected by a later record that references the earlier one. That is what an
audit trail a regulator can read means in practice.

The gate is exercised on a real repository holding a real prompt, over a history of pull
requests where some pass, some are blocked, and one fails on latency alone. That history is
the evidence that it works, rather than a description of it working.

## Publishing what did not work

The portfolio requires every project to publish one approach that was tried and rejected,
with the evidence. Here the candidates are written down in advance, before any data exists,
which is harder than picking one afterwards. Using a model as a judge for drift, where the
judge's own disagreement with itself is expected to be larger than the effect being
measured. Relying on public benchmark questions alone, where contamination is expected to
push scores up without any capability change. And asking each question once instead of five
times, where every single month is expected to look like drift. Whichever of these fails as
predicted is published with its numbers.

## Why one command matters

Eight years of production machine learning inside health and government is real work that an
outsider cannot verify. The portfolio exists to fix that, and the standard is the same in
every project: a stranger clones the repository, runs one command, and gets the same table.
Here that means the frozen question set and its hash, the panel of models with the date they
were chosen, every raw response committed, and every reported score carrying a confidence
interval. In this repository a bare percentage is treated as a defect.
