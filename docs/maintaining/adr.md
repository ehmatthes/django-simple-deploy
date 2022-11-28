---
title: Architectural Design Record
hide:
    - footer
---

An architectural design record (ADR) keeps track of larger decisions that relate to the overall architecture of the project.

## About ADRs

I've been looking for a good way to record the larger decisions that are being made in the process of reaching a 1.0 release. At DjangoConUS 2022, Juan Saavedra gave a [talk](https://www.youtube.com/watch?v=_-0zHdJGTlw) about using ADRs to record these kinds of decisions, without letting formality hinder the overall development process. This is exactly what I was looking for. 

### Architectural Decisions

An architectural decision (AD) is "a decision on non-functional aspects that is hard to change." For example, "Do we want to use a third-party library to implement the CLI?"

### Architectural Decision Record

An ADR is a short text file, or section of a file, that serves as a message for future developers. It needs to be practical to fill out, it's technical in nature, and is a record of decisions and critical thinking related to those decisions.

- **Context**: Why is this decision necessary? What needed to be considered?
- **Options**: What options were available? What were the pros and cons of each?
- **Consequences**: What will happen as a result of this change? (good and bad)
- **Status/ Outcome/ Conclusion**: Has the decision been implemented? Has it been superseded?

### Format

ADRs are project-specific. The level of formality should be such that maintainers actively use the ADR to help them make progress, rather than seeing it as an obligation or hindrance to progress.

- Some are formal templates; this is not necessary.
- Possible sections: title, context and problem statement, decision drivers, considered options, decision outcomes, pros & cons, validation, extra info (links to issues/ discussions)

### Final thoughts

ADRs should document non-changes as well. If an architectural change was considered seriously but not adopted, recording that decision will probably save some time when the idea comes up again.

ADRs should be a summary of an outcome, not an exploratory tool. All the thinking and external resources that come up in the exploratory phase of making an AD should be tracked in an issue or a discussion. Only the summary of the final decision should be recorded here.

## Making a new ADR entry

Making a new ADR entry should be quick, and should be straightforward if reasonably detailed notes were kept during the exploratory phase.

- Choose the level of detail you want to include, keeping the above points in mind. All records should at least mention the context, the options considered, and the final outcome or decision. They should almost always link to an issue or discussion, if the majority of the thinking or exploratory work was recorded there. There should be some summary of the rationale for the decision that was made.
- Treat this like a changelog. The most recent records should be at the top of this file.

## Evolving ADRs

It may be worth using an issue template to implement ADRs as a specific type of issue, with a dedicated label. But I like the idea of recording ADRs outside of GitHub, in the project's overall documentation.

---

## `simple_deploy` ADRs

### Reassess current CLI architecture

Date: 11/27/22

Context:

At the start of this work, the CLI was defined inside a method in the growing simple_deploy.py file. The goal was to clean up the CLI so it can be used to support new platforms. The main decision was whether to start using Click to implement the CLI, and also to assess whether there were optimizations that could be made at this point.

Options:

- Continue implementing the CLI without Click
- Adopt Click
- Keep everything in simple_deploy.py
- Move some CLI implementation code out of simple_deploy.py

Outcomes:

- Don't adopt Click.
    - It brings added complexity at this point, without a corresponding benefit.
- Move the definition of CLI args to a new file, cli.py.

Extra info:

- Related issue: [#168](https://github.com/ehmatthes/django-simple-deploy/issues/168)
