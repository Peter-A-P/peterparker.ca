Somewhere in every large organisation, someone spends the first hour of the day reading
the news. They scan twenty sites and a few feeds, decide what the minister or the chief
executive needs to know, and write it up before nine. In a government with dozens of
departments, or a health authority with dozens of divisions, that hour is being spent
dozens of times over, by people who were hired to do something else, on largely the same
articles, with largely the same twenty outlets reporting the same six stories.

The output is rarely good, and the reason is not that the people are careless. It is that
the job is genuinely hard to do well at speed, and nobody can tell whether it was done
well. Nothing is measured. If yesterday's digest missed the one item that mattered, that
absence is invisible.

| What the job actually requires | Why it goes wrong by hand at 8am | What that costs |
|---|---|---|
| Knowing what this particular audience cares about | It lives in one person's head, and changes when they leave | A new person takes months to be useful, and nobody can say what changed |
| Recognising the same story from twenty outlets | Obvious for the front page, tedious for everything else | The digest repeats itself, and looks padded |
| Not missing the item nobody covered loudly | You cannot notice what you did not see | The one real failure, and the one that is never counted |
| Quoting accurately under time pressure | Copy, paste, trim to fit | A quote that was tightened into something the source did not say |
| Knowing whether any of this is working | There is no feedback and no score | The whole activity runs on faith |

This project builds one product that does that job, configured per department in a single
file, and it treats the last row of that table as the deliverable. A digest that feels
relevant is not evidence. The point is to end with two numbers per audience, measured
against a week of items judged by hand: how much of what it showed was worth showing, and
how much of what was worth showing it missed.

## What a department actually configures

One file. Topics, the organisations, people and places that matter, the geography, the
languages, which sources to trust, which to block, how long the digest should be, and what
time it arrives. Adding a department is adding a file. There is no code to change and no
consultant to book.

The file also carries something less usual: a written rubric saying what "relevant" means
for that audience, in plain words, including what does not count. That is not decoration.
It is what a human labeller reads before judging an item, and it gets published next to
the accuracy numbers, so a reader can see what the system was actually being scored
against. A rubric that says "things we care about" is rejected by the software.

## The three things that make it more than a summariser

**It removes the duplicates before it ranks.** The same announcement reaches the system as
a wire story, three outlets' rewrites of that wire story, a government press release and
two posts about it. Those become one story with the sources attached, so a ten-item digest
holds ten things rather than four things and six echoes.

**It keeps the model away from most of the work.** The obvious build sends every article to
a large language model and asks what matters. That is expensive enough to make the whole
idea pointless at scale, and it is not obviously better. Here the day's pool is narrowed
first by methods that cost nothing to run, and only the strongest candidates are put to a
model. That single decision is the difference between a few dollars a month per department
and a few hundred.

**Every quote is checked against its source, mechanically.** The summariser writes each
sentence with the articles it drew on and marks its quotes. Then a separate piece of code,
which is not a language model and does not have opinions, goes and finds each quote in the
source text. If it is not there word for word, the sentence is rewritten once and dropped
if it fails again. The counts before and after are published, so a reader can see how often
the model tried to invent something. A digest that cites is common; a digest whose citations
are verified by something that can say no is not.

## Where the sources come from, and the rule about them

Published feeds and official interfaces only: news and government feeds, a public global
news index, and the official interfaces of two public discussion platforms. No scraping
around paywalls, and no ignoring the rules a site publishes about what machines may read.

Every source's terms are read and recorded with the date before it is used, and a source
that changes its terms is dropped rather than bent. That sentence appears in a lot of
project descriptions and usually means nothing. Here the document holding those records is
wired into the software: the code reads it, and refuses to send a request for any source
whose row does not say the terms were read, with the date. A source added without that is
not a rule broken in a code review. It is a run that fetches nothing and says why.

Article text is kept thirty days and never republished. A digest shows a summary, a link,
and quotes of at most twenty-five words.

The rule earned its keep on the first day it was switched on. Until the terms for a source
were read and dated, the software refused to fetch it, so the first live run made eleven
refusals and sent zero requests. That is not a delay in the project; it is the only version
of that promise worth making.

## Nothing is sent

The system publishes a page and writes a draft file. There is no email path, no chat
integration and no notification of any kind, by design rather than by omission. A test
reads every import in the codebase, the full list of installed libraries and the commands
the tool offers, and fails the build if anything capable of sending appears. The decision
of whether a piece of writing goes to a person stays with a person.

**Where this stands in September 2026: in progress, with nothing measured.** The first
week's work is built and tested: reading the sources, storing them, collapsing the
duplicates and grouping the day's stories, across four example audiences. The ranking, the
cited summaries, the quote verifier and the daily hosted job follow, and then a week of
items is labelled by hand to produce the accuracy numbers. No digest has been produced yet
and no number has been measured, so there is nothing here to check and no results table
pretending otherwise.

The fourth audience is regional: Newfoundland and Labrador, added because the other three
are national or big-city and the claim being tested is that a small regional team gets the
same system from the same code. It is also the harder ranking problem, with fewer sources,
less duplication to collapse, and a pool where almost everything is local and little of it
matters.

<!-- more -->

## Why measuring the misses is the hard part, and how it is done honestly

Measuring what a digest got right is easy. Show a person the ten items it chose and ask
which of them deserved to be there. That gives you precision, and precision on its own is
the number that flatters every system of this kind. A digest that shows one item, and that
item is good, scores perfectly.

The number that matters is the other one: of everything worth knowing that day, how much
did it miss? Answering that properly means judging every item in the day's pool, which is
hundreds of items per audience per day, thousands across a week. Nobody is going to do
that, and a project that claims it did should be disbelieved.

So it is estimated, and the estimate is labelled as an estimate wherever it appears. Each
day, a labeller sees everything the system ranked in its top thirty, plus thirty items
drawn at random from everything it ranked below that. The first group gives precision
directly. The second group is a sample of the part of the pool the system discarded, and
each item in it stands in for many that were not looked at, in a known proportion, which is
what makes a recall figure calculable rather than guessed. Every published number carries a
confidence interval, because a figure from sixty judgements a day has real uncertainty and
hiding that would be the same dishonesty in a different costume.

One audience is labelled twice, by two different people, and the level of agreement between
them is published too. That figure is uncomfortable and it belongs in public. "Relevant" is
a judgement, not a fact, and a reader is entitled to know how much two reasonable people
disagreed about it before reading how well a machine matched them.

## What happened when the sources were finally switched on

Of the thirteen feeds originally configured, six did not work. Four returned a plain 404.
Two returned a perfectly healthy 200 containing an ordinary web page, which a feed parser
reads as a feed with no entries, and which a daily job counts as a source in good standing
while the digest quietly gets shorter. That second failure is the one worth building
against, so the project grew a command that fetches every configured feed once and refuses
to call a 200 with no entries a success.

The more interesting failure was a public broadcaster whose feeds timed out every time. It
was written off as unreachable. That was wrong. Holding everything else constant and
changing only the line that says who is asking, the feeds returned in a third of a second
for a plain name and version, and the connection was reset whenever the name included a web
address. The `Name/Version (+https://...)` form is the convention crawlers use to say who
they are and how to be contacted, and on that site it is the one thing that gets the request
dropped, while a client that volunteers nothing about itself is served without complaint.

The project now sends its name, version and purpose and no address, which is still true and
still identifies it, and a publisher who wants it to stop still says so in the ordinary way,
in the file where such things are said, and it is obeyed. The episode is recorded because it
is a small, exact example of something general: a rule of thumb aimed at badly behaved
automation, applied bluntly, falls hardest on the automation that was trying to behave.

## Grouping stories is two different problems wearing one coat

An early version of this treated the whole job as one comparison: take each pair of
articles, see how similar they are, group the similar ones. It does not work, and the way
it fails is instructive.

Two outlets running the same wire copy share whole sentences while rewriting the headline
completely. Two genuinely different reports of one event share the subject and almost no
wording. Those are opposite signals. Tuning one comparison to catch both catches neither:
weight the headline and the reprints slip through, ignore it and the independent reports
never join up.

So it is two passes with opposite emphasis. One compares the body text and catches the
reprints. The other compares meaning, with the headline weighted, and joins the reports.
A story is what survives both. The evidence for that is in the project's own test suite,
where the same pair of wire stories scores well above the threshold under the first method
and well below it under the naive combined one.

## What it deliberately does not do

It is not a reader application. No accounts, no bookmarks, no mobile app, no feed to scroll.
The product is the pipeline and the numbers; the delivery is a plain page. Building the
reading experience is where projects like this usually go to die, because it is more fun
than measuring whether the thing works.

It does not score sentiment, or produce "media tone" numbers. Those are the standard
offering in commercial media monitoring, and they cannot be checked against anything true,
which makes them the opposite of what this project is for.

It does not read paywalled articles, and it does not use a large social platform that no
longer offers affordable access on official terms. Both are out on the terms, not on the
budget.

## Why it ends in a table

Eight years of production machine learning inside health and government is real work that
an outsider cannot verify. This portfolio exists to fix that, one project at a time, and
the standard does not move: a stranger clones the repository, runs one command, and gets
the same numbers. For this project that means precision and recall per audience with
intervals, the agreement between two labellers, the deduplication rate, the share of quotes
that survived verification, the lag between publication and inclusion, and the cost per
digest taken from a spending ledger rather than estimated. Whatever those figures turn out
to be, they are the ones that get published.
