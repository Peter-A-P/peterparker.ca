Every running platform tells you what you did. Strava, Garmin and TrainingPeaks are very
good at that. None of them tell you what to do next, and the ones that try hand you a plan
that was generated at sign-up, from a template, before any of your running had happened.

A coach does three things a platform does not. It reads what you said, not only what your
watch recorded. It remembers what you said last week. And it is allowed to tell you no.

| What a runner actually asks | What the platforms answer | What that answer is missing |
|---|---|---|
| Am I fit enough to run the time I want? | A race prediction from your best recent effort | It reads a hot, windy or hilly run as a bad one, and it never says how sure it is |
| Was that run good, given the day it was run on? | A pace and an average heart rate | The same pace means different things at 22 degrees into a headwind and at 8 degrees on the flat, and nothing corrects for the difference |
| Should I run tomorrow? | A readiness score out of 100 | It does not know your Achilles has been mentioned three weeks running, because you typed that into a comment box rather than into a sensor |
| What should next week look like? | A plan written before this week happened | Nothing in it responds to the week you actually had |
| Who decides? | The app does | There is no point at which it stops and waits for you to disagree |

Overload is an attempt at the other thing: a coaching staff rather than a dashboard. Three
AI specialists read the week. One watches for injury, scanning what the runner wrote for
pain and tracking whether a niggle is new, recurring or fading. One watches fitness, asking
whether the load is being absorbed and what would advance it. One watches the calendar,
weighing the race being trained for against the build that is actually happening. They
report to a head coach, which weighs the three reports, writes next week's plan, and then
stops and talks it through. Nothing is committed until a person says yes.

The part that matters is what the AI is not allowed to do. It does no arithmetic. Training
load, weekly volume, fitness trends, the pace each run was really worth once the hills, the
heat and the wind are taken out: all of that is computed in plain, tested Python, and the
models only ever see the results. The safety limits work the same way. How much the week may
grow, when a recovery week stops being optional, what the day after a long run may contain,
how much of a week's running two consecutive days may carry: these are computed, handed to
the head coach as hard limits, and then checked again in Python after the plan comes back.
A plan that breaks one is sent back once with the breach spelled out.

That division is the whole design, and it is there because the alternative was tried first
and failed in a way worth reading about. The rules used to live in the prompt. One of them
turned out to be arithmetically impossible to obey, and in the single week it actually
bound, the coach broke it and then wrote in its own notes that it had not.

There is also a limitation that belongs near the top rather than in a footnote, because it
cuts against the design's own central claim. Pain reaches the system only as free text in a
comment box. There is a deterministic injury gate in the code, it is tested, and in normal
use nothing ever triggers it, because nothing writes the table it reads. So whether a sore
tendon changes the training is a judgement a model makes, not a limit the code enforces.
Three things compensate and none of them is a guarantee.

**Where this stands in September 2026: running, and in private use since 2025.** It ingests
real Strava and Garmin data, runs a real weekly cycle, and has been corrected by its own
history more than once. It has no published result. The portfolio's standard is that a
stranger clones the repository, runs one command and gets the same table, and this project
cannot meet that yet, for a reason that is not laziness: every number in it is calibrated
against one person's own training data, and that data is the one thing that cannot be handed
to a stranger. The repository is private, and it opens when there is a number in it that
somebody else can check.

<!-- more -->

## The rule that could not be obeyed

The original spacing rule was one line of prompt text: no back-to-back running days during
the base build. It sounded conservative, which is how it survived review.

It is unsatisfiable. On a repeating weekly template, forbidding adjacent running days caps a
runner at three days a week, because Sunday and the following Monday are adjacent too. The
athlete profile asked for four days, and the stated goal of the training phase in force was,
in as many words, to add the fourth day. The guardrail forbade the objective of the phase it
was guarding. Worse, at the volume the plan was building toward, the only way to satisfy
both was to push every session over 20 km: a rule written to protect a tendon could comply
only by maximising the distance of every single run.

Then it bound, once. The plan could not fit the week's kilometres into three and a half
non-adjacent days, so it broke the rule, put the unavoidable pair in the only place left,
which was a 9 km run directly into a 22 km long run the next morning, and wrote "no
back-to-back run days anywhere" in its own briefing. The runner's own untutored habit, two
days early in the week with four clear days before the long run, was both safer and banned.

The replacement is a different kind of rule: any two consecutive running days may total at
most 40% of that week's running. Consecutive days are otherwise fine. It is computed, stated
to the coach as a number, and re-checked against the finished plan in Python, because
prompt-only enforcement is exactly how the first version failed.

## Where 40% came from, and what it is not

Not from a textbook. It was measured, by taking the largest consecutive-day pair as a share
of the week across every week in the database. Four uneventful weeks came in at 37.8, 36.2,
37.3 and 38.1. The week that prompted the whole exercise came in at 58.6. The threshold sits
in the eight-point gap between the highest passing week and the lowest failing one, and over
all thirty judgeable weeks it flags three and clears twenty-seven. Nobody designed that
cluster; it is where this runner settles when left alone.

It is documented as a descriptive bound and not a physiological threshold, and the
documentation says so in the same breath as the number. It is a between-week comparison,
which is the class of evidence this project distrusts on principle, over one person's
history, with no within-week control available, because spacing is a property of a week and
cannot be varied inside one.

It is also documented with what it made unnecessary and what was rejected. The long run is
34 to 48% of the week in every week on file, so it isolates itself: anything beside it
breaches the cap on its own, and a separate "nothing the day before the long run" rule would
only make the cap look like it needed propping up. A ban on three consecutive days looked
free, since it had never happened in 111 running days, and was rejected because it quietly
re-imposes the four-day ceiling the cap exists to remove.

## The wind model was wrong by a factor of four, and that was measurable

Running in St. John's means wind, so the pace correction carries a wind term derived from
published aerodynamics. Comparing runs against each other says windier runs are faster, at a
correlation of +0.30, and applying the raw correction makes the spread of per-run fitness
scores worse rather than better, from 2.93 to 3.23. That is the signature of a correction
amplifying noise, and taken at face value it would have killed the feature.

The comparison was the problem. Wind is confounded with season, route, session type and
fourteen months of fitness drift. So it was measured within runs instead, where fitness,
weather, fuelling and route are constant by construction: each kilometre split carries a
grade-adjusted speed, an average heart rate and, from the recorded route, its own head
component.

That exposed the confounder. This runner goes out into the wind and comes home with it, so
position in the run and headwind correlate at -0.397, while efficiency falls about 7% from
the start of a run to the end as heart rate lags early and drifts late. The position effect
is an order of magnitude larger and swallows the wind effect whole. Fit both together and
the wind term is real, correctly signed, and roughly a quarter of what the published model
predicts. The calibration constant is 0.26, taken from the windiest subset rather than
averaged across three, because near-still runs dominate the all-runs fit, and because taking
the lowest of three overlapping estimates errs toward under-correcting.

Then the comfortable explanations were checked, and all of them failed. Shelter: the usual
route is coastal and exposed for more than half its length. Route recording error: a median
97% of recorded distance at 29 points per kilometre. Wind direction error from valley
channelling: it would have to be about 95 degrees off, which is to say random. What is left
is that the published chain overstates this runner's real cost, which is the less tidy
answer and the honest one.

The payoff is deliberately unglamorous. On the windiest run in the history the raw model
claims nearly 3 VDOT points and the calibrated one claims 0.75. The median across
correctable runs is 0.23 points. The headline fitness figure did not move at all, and the
marathon projection moved five seconds. The constant is a module constant rather than a
setting, specifically so that nobody can tune it until the chart looks right.

## Fitness measured on every run, and the guards that make it refuse

VDOT is Daniels' scale, and it is defined off race performances. Feeding a training run into
the race formula reads an easy run as a ceiling, which was a real bug: easy runs were scoring
around 47 for a runner whose actual figure is around 62.

The correction comes from the same source as the tables. The spreadsheet's own
percentage-of-VO2max and percentage-of-maximum-heart-rate rows are one straight line,
reproducing to five decimals across all nine distance columns, so it can be inverted: the
effort a run was run at is recoverable from its average heart rate, and the run's
grade-adjusted pace is divided by it. The test that makes this a correction rather than a
fudge is that at race pace and race heart rate the two paths return exactly the same number.

Most of the work is in the refusals. No heart rate, no answer. Below the line's lowest
anchor, no answer, because that is extrapolation. Under ten minutes, no answer, because the
average is mostly the warm-up climb. Treadmill and virtual runs are excluded entirely: the
belt speed is whatever the machine claims, there is no gradient so the grade adjustment does
nothing, and heart rate sits lower indoors, which is precisely the signature this model
mistakes for elite fitness. One virtual run scored 68.2 against about 61 either side of it,
and it was setting the headline.

The headline itself is the best qualifying run of the last seven days, not an average.
Per-run error is one-sided: drift, heat, a slipping strap and heart-rate lag all read low,
and nothing reads systematically high, so the best of a few recent runs is the least
corrupted reading rather than the most flattering one. A week with no qualifying run returns
nothing rather than carrying the last value forward, which fires on about 2% of days and is
the deliberate cost of not presenting a stale number as current fitness.

## Three corrections that were built, measured and thrown away

Long runs score consistently lower than short runs at matched heart rate, by three to four
points on six of seven pairs. The obvious explanation is cardiac drift inflating the average,
and the obvious fix is to score a fixed window instead, which is roughly what Garmin does.
Three versions were built and backtested. A duration constant was the worst: back-solving
what each long run would have needed gives implied drift rates from 0.4 to 8.7% per hour, a
twentyfold spread within one runner in one distance band, and the best single constant still
left a large residual while inflating the clean long runs into fantasy. Nine scoring windows
were tried; the best moved the gap from 3.30 to 2.81 points and cost about 1.8 points of
uniform downward shift on every run, which would have broken the independent agreement with
Garmin's own VO2max that the rest of the system leans on as a sanity check.

They failed because the premise was wrong. Once decoupling was actually measured, runs over
an hour came in at a median of about 1%, several of them negative, and the correlation
between a run's measured decoupling and its scoring penalty is only -0.40. The two runs
either side of the headline settle it: near-identical decoupling, four points apart, and
reading the splits shows the deficit is fully present by minute ten and flat from kilometre
three to kilometre twenty-one. There is nothing in the tail to trim. So the deficit is
treated as real and left alone, because inventing a correction for it would be the confident
wrong number this project exists to avoid.

Humidity went the same way. Dew point on its own looks convincing, and it is entirely
temperature: warm air holds more water, so the two are collinear by construction, and putting
temperature into the model collapses dew point to nothing and flips its sign. Relative
humidity is the clean test, being essentially independent of temperature here, and it comes
out in the physiologically wrong direction. The reason is climate rather than statistics.
Humidity binds when evaporation is the limiting route for shedding heat, and this runner's
runs have a median of 12.8 degrees and a maximum of 21.1. There is no effect here to find,
and a term fitted to this data would be fitting noise. The conclusion is flagged as local: it
does not travel to a hot race, and because the underlying temperature table is linear and
unbounded above, the right fix there is a guard that refuses rather than a term that
extrapolates.

Gusts were asked about and answered no, for the same structural reason humidity fails: a
per-run constant is annihilated by the within-run centring that made the wind measurement
work in the first place.

## Every model call is counted, and the ledger does not rewrite its own history

There are six places this project calls Claude, and four of them go through structured
output, which consumes the response object carrying the token counts. Reading usage at each
call site would have meant rewriting the coach's control flow to suit the accounting. Instead
one callback sits on the client and sees the raw response before the parser does, so all six
sites are covered and none of them changed shape. The property worth having is that a call
site added later is measured by default; the failure mode of the alternative is a new model
call that is silently free. A call made outside a labelled block is recorded as unattributed
rather than dropped, so it appears on the page asking to be labelled.

The ledger stores tokens, never dollars. Cost is derived on read from the model and the day
the call was made, because list prices move: an introductory rate on the model the three
advisors run on lapsed on 2026-08-31, and a single flat rate per model would have meant every
advisor call ever made silently got 50% more expensive overnight. Each row is priced and then
summed, never the reverse, because a month spanning that date has no single rate. An unknown
model yields nothing rather than a guess, and the page says how many calls it could not
price, so the total reads as a floor.

The currency is handled the same way. The ledger is in US dollars because that is what is
invoiced, and Canadian dollars are derived on read at the rate for each call's own day rather
than today's. The rate moved 2.2% over one summer, and applying a current rate to the whole
history would restate what every past week cost every time the currency moved. Reference
rates publish on business days only and the weekly run fires on a Sunday, so the page records
which day a carried-forward rate is really from and names it, rather than interpolating a
number the market never quoted into a money column.

## What this deliberately does not do

The injury gate is the large one, and it sits at the top of this page rather than down here.
The decision not to build per-body-part severity logging was made deliberately: it is more
bookkeeping than it is worth, and a plain comment on a run carries the same information to a
coach. The consequence is that the deterministic backstop for "the athlete said their
Achilles hurt" does not exist. What compensates is a prompt that names the channel
explicitly, a comment box that asks for pain rather than for a training diary, and an entire
specialist whose only job is to read for it, so that the judgement cannot be crowded out by
planning. That is three mitigations and no guarantee, and the documentation says so in those
terms.

Fitness is seeded from zero at the start of the record, so the first six weeks of any history
understate it. A session prescribed by duration rather than distance drops out of the spacing
arithmetic, because converting minutes to kilometres needs an assumed pace and a wrong guess
would either invent a violation or hide one; the checker therefore never reports a plan as
clean, only that it found nothing. Garmin has no official consumer interface, so that half of
the ingestion is unofficial and can need re-authentication. And it is a personal training aid
and not medical advice, which is a boundary the models are instructed to hold.

## The number that is missing, and why

Every project in this portfolio is meant to end in a table a stranger can regenerate. The
pieces here are closer to that than they look: the wind constant, the spacing threshold and
the metric validation are each produced by a script in the repository rather than typed, and
each is re-derivable by running it. The validation pass over the real history is what found
five genuine bugs in the load model in the first place.

What is missing is that all of it rests on one runner's own training data, and that data is
personal. A stranger can clone the code and cannot clone the history, so the numbers are
reproducible by exactly one person. There is also no control group and no second athlete, so
nothing here can separate good coaching from a good year. Naming a checkable result that
survives those two facts is the open problem, and until it is solved this is a working system
rather than a finished one. That is why the repository is still closed, and it is a better
reason than not being ready.
