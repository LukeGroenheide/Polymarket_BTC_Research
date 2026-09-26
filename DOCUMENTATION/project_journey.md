# Project Journey

This project did not start as the system shown in the architecture page.

It started as a much smaller attempt to collect Polymarket data and see whether prediction markets could tell me anything useful about Bitcoin. As I kept working on it, the problems stopped being only about the research question. I started running into storage limits, broken automation, messy data movement, reproducibility problems, and questions about whether I could actually trust the datasets I was creating.

A lot of the current system exists because something earlier either broke or became too difficult to reason about.

## Early prototype

The first versions were mainly about proving that I could discover markets, collect data, and start experimenting with it.

At that stage I was much more focused on getting something working than on building a system I could maintain for months. This mentality got the project moving quickly, but it also taught me one of the first big lessons of the project:

**A working prototype is not the same thing as a system you can trust long term.**

As the amount of data and code grew, I started needing clearer answers to questions like:

- Where did this file come from?
- Which version of the collector created it?
- Is this raw data or something derived from it?
- Can I rebuild this result later?
- What happens if the machine running the collector fails?

Those questions became more important as the project moved beyond small experiments.

## VPS collector + Mac research setup

The next version of the project split responsibilities between a VPS and my Mac.

The VPS handled continuous collection while the Mac held selected copies of data and was used more heavily for research and analysis.

That separation actually helped at first. It made me think more clearly about the difference between the system collecting live data and the system I was using to experiment with that data.

But it also created a new problem: now the project depended on data moving correctly between two machines.

I had to think about what should be copied, what should stay on the VPS, what counted as the original source, and what would happen if the two machines stopped agreeing about the state of the project.

That setup worked well enough to keep the project moving, but over time it became clear that the split was adding complexity.

## When things started breaking

The project became a lot more educational once it started failing in ways I had not planned for.

One of the biggest early problems was storage. Raw NDJSON collection eventually filled the VPS's 50 GB disk. The Mac had copies of some processed data, but I realized that did not necessarily mean the original raw collection was safe.

I also ran into automation problems on the Mac. One scheduled process ended up using the wrong Python environment. The code itself was not necessarily broken; the unattended job was running under a different environment than I expected.

That taught me to care much more about the runtime around the code:

- which Python executable is actually running
- which paths and environment variables exist
- which user owns the process
- what happens when nobody is sitting there watching it

Those sound like obvious things now, but I learned them by having them actually break.

As more things started to break and my uncertainty about the future state and layout of the project grew, I started to get overwhelmed. This is where the dedicated Linux system came in clutch.

## Moving everything to a dedicated Linux system

By May and June, the VPS/Mac split had become more trouble than it was worth.

The VPS had limited storage, moving data between machines added extra failure points, and I had accumulated enough historical files and generated state that simply copying everything to a new machine would have brought a lot of clutter with it.

Instead, I treated the migration as a chance to decide what parts of the old system were actually worth keeping.

I moved the project onto a dedicated Dell running Linux and kept the useful behavior and data contracts from the earlier system without trying to preserve every old file, service, or experiment exactly as it had existed.

That was another important lesson:

**When moving a system, it is usually better to preserve the rules and important data than to blindly preserve the entire old machine.**

The Dell eventually became the main place where collection, storage, ledger creation, archival, and research infrastructure came together.

## External storage and longer-running collection

Once the project was collecting continuously across **5-minute, 15-minute, 1-hour, 4-hour, and 1-day** markets, storage was at the forefront of my mind.

Large raw captures moved onto external storage. I also started separating the project into clearer types of data:

- raw source data
- processed session ledgers
- data prepared for modeling
- runtime/control files
- archived data

This led me to build a process for archiving old raw captures and keeping a checked copy on a separate drive before older source data can be removed. As much of a pain as this process was to implement, things like this—things I never imagined I would have to build when I first started—have arguably become my favorite part of the project.

## From raw messages to traceable research data

Another major change was the move toward a canonical session ledger.

Early research was much more ad hoc. Over time I wanted a consistent way to turn the raw websocket messages from a market into an ordered session record that I could use again later.

The ledger gave me one place to preserve things like:

- message order
- receipt timing
- source identity
- whether the session was complete
- where the original data came from

This made the data I later used for modeling much easier to trust. If I got a weird result, I wanted to be able to trace it backward through the session ledger to the original messages instead of looking at a final spreadsheet or table and having no idea how it got there.

## Becoming more disciplined about the research

Early on, I had never even heard of overfitting. As the project developed, I started to realize just how important it was to avoid it. It is easy to try an idea, look at the result, change something, and try again. But if you keep doing that on the same data, it also becomes very easy to convince yourself that you found something that is not actually there.

For the final V1 research, I became much stricter.

I fixed the feature definitions, development dates, model comparisons, and final held-back dates ahead of time. The feature code only uses Polymarket messages that had actually reached the machine by the prediction cutoff, and the BTC reference data uses exact one-second Binance bars.

Most importantly, the final out-of-sample block was set aside before the final evaluation. Once that setup was frozen, I did not want to change the experiment based on what the held-back data said.

That made the final question much simpler:

**Given the experiment I committed to ahead of time, does the Polymarket information actually hold up on data I did not use to develop it?**

## What I would do differently

If I started this project again, I would probably build fewer layers early on and make the boundaries between raw data, derived data, and research outputs clearer from the beginning.

I would also consolidate the infrastructure sooner instead of letting the VPS/Mac split grow as far as it did.

At the same time, a lot of what I understand now came directly from dealing with those problems.

The disk filling up taught me more about storage than reading about storage would have. Broken scheduled jobs taught me why runtime identity matters. Recovery work taught me that adding more safety checks is not always the same thing as making a system safer. And the research process taught me how easy it is to accidentally weaken an experiment.

The final system is much more organized than where I started, but the most important part of the project has probably been learning **why** those pieces are organized the way they are.
