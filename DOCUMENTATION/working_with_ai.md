# Working with AI

I used ChatGPT and Codex throughout this project for research, debugging, planning, code review, documentation, and implementation.

When I first started using Codex, I was going into an area I had almost zero experience in. I hardly knew how to code, I didn't know much about prediction markets, and I didn't really know where to start. For lack of a better word, the project was slop. My Codex and ChatGPT sessions were overloaded with context, they were hallucinating left and right, and I had no good way to even visualize what work was being done. It was a mess. Regardless, I kept working on it.

As time went on and the project became larger, I began to understand how to manage session context, token usage, the type of model and reasoning I was using, and how to leverage ChatGPT when prompting Codex.

## Giving AI smaller, clearer jobs

One of the biggest changes was learning not to give AI vague tasks like "fix this part of the project."

I got much better results by breaking work into stages:

- inspect the current state
- explain what is wrong
- propose a plan
- implement only the approved scope
- run specific checks
- stop and report what changed

Sometimes telling AI what **not** to touch became just as important as explaining what I wanted changed.

That mattered especially near the end of the research. Once the final experiment was frozen, Codex could execute the evaluation, inspect outputs, and validate the results, but it was not allowed to change the models, feature definitions, dates, or evaluation rules based on what it found.

## Managing context

This project also taught me how important context is when working with AI over a long period of time.

The work eventually spanned many ChatGPT and Codex sessions. If a new session did not know which decisions were current, it could confidently recommend work that had already been completed or bring back an older design I had intentionally replaced.

I started keeping source-of-truth and handoff documentation so new sessions could quickly understand the current state of the project.

I also became more deliberate about session context and token usage. Instead of trying to carry the entire history of the project into every task, I started using ChatGPT to help create focused prompts for Codex. My workflow became: have an idea, use ChatGPT to audit it, create a Codex prompt with only the context needed for that specific task, and choose the model and reasoning level based on the complexity and risk of the task.

## Learning not to trust plausible answers automatically

AI was useful partly because it forced me to get better at recognizing when something sounded reasonable but was not actually correct.

One example came from comparing different Polymarket horizons. An early version of the logic reused timing from the 5-minute market too literally. I eventually realized that the meaningful comparison was not using the same number of seconds after market start, but using the same **40%-through-the-market** point across horizons.

I also learned that AI often responded to reliability problems by suggesting more checks, more safeguards, and more machinery. Sometimes those protections were useful. Other times they made the system harder to understand without protecting against a real failure mode.

Over time I got much more comfortable pushing back and asking whether a new layer was actually necessary.

## What I kept in my hands

I used AI heavily in this project, including for implementation. I do not think pretending otherwise would make the project more impressive.

The important part for me was understanding the system well enough to decide what should be built, recognize when an assumption was wrong, and verify the result before relying on it.

Some decisions stayed explicitly under my control:

- freezing the final research design
- approving destructive or production-facing changes
- deciding what counted as authoritative project state
- deciding whether an unexpected result justified changing anything
- interpreting the final out-of-sample result
- deciding what claims were appropriate to make publicly

AI helped me move much faster, but I did not want it quietly changing the question I was trying to answer.

## What I learned

One of the biggest things I learned was the importance of giving AI the same things that make normal engineering work better: clear scope, good context, explicit constraints, review points, evidence, and tests.

I now use AI less like an answer generator and more like a collaborator.

Learning how to use AI effectively has ended up becoming one of the most useful skills I learned from the project.
