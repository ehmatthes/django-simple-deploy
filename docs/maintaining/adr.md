---
title: Architectural Design Record
hide:
    - footer
---

An architectural design record (ADR) keeps track of larger decisions that relate to the overall architecture of the project.

## About ADRs

I've been looking for a good way to record the larger decisions that are being made in the process of reaching a 1.0 release. At DjangoConUS 2022, Juan Saavedra gave a [talk](https://www.youtube.com/watch?v=_-0zHdJGTlw) about using ADRs to record these kinds of decisions, without letting formality hinder the overall development process. This is exactly what I was looking for. 

Briefly:

- An architectural decision (AD) is "a decision on non-functional aspects that is hard to change."
    - An example is, "Do we want to use a third-party library to implement the CLI?"
- An ADR is a short text file, or section of a file, that serves as a message for future developers. It needs to be practical to fill out, it's technical in nature, and is a record of decisions and critical thinking related to those decisions.
- An ADR should contain:
    - Context: Why is this decision necessary? What needed to be considered?
    - Options: What options were available? What were the pros and cons of each?
    - Consequences: What will happen as a result of this change? (good and bad)
    - Status/ Outcome/ Conclusion: Has the decision been implemented? Has it been superseded?
- Format:
    - ADRs are project-specific. The level of formality should be such that maintainers actively use the ADR to help them make progress, rather than seeing it as an obligation or hindrance to progress.
    - Some are formal templates; this is not necessary.
    - Possible sections: title, context and problem statement, decision drivers, considered options, decision outcomes, pros & cons, validation, extra info (links to issues/ discussions)
- My thoughts
  - ADRs should document non-changes as well. If an architectural change was considered seriously but not adopted, recording that decision will probably save some time when the idea comes up again.
  - ADRs should be a summary of an outcome, not an exploratory tool. All the thinking and external resources that come up in the exploratory phase of making an AD should be tracked in an issue or a discussion. Only the summary of the final decision should be recorded here.

## Making a new ADR entry

- Choose the level of detail you want to include, keeping the above points in mind. All records should at least mention the context, the options considered, and the final outcome or decision. They should almost always link to an issue or discussion, if the majority of the thinking or exploratory work was recorded there.
- Treat this like a changelog. The most recent records should be at the top of this file.

## `simple_deploy` ADRs