---
title: Review a language pack
description: How to review your language's pack by pull request, and what happens after.
---

Every language pack starts experimental: a machine proposed the words, and only people who speak
the language can make them better. Reviewing a pack is how you shape the words your language codes
in.

Reviews arrive as pull requests in [legesher/language-packs](https://github.com/legesher/language-packs). You need a GitHub account and to
be comfortable editing a file and opening a pull request. You do not need to know Python to review a
Python pack.

## Review in four steps

1. Copy your language's template to your own review file. The tag is your language's code
   (`reference/ml.md` is Malayalam), and the username is your GitHub username.

   ```text
   reference/<tag>.md
   → reviews/<tag>/<tag>-<username>.md
   ```
2. Work through the terms. Put `✓` in Comments to endorse the current word, write `Keep` plus a
   note to endorse it with a limitation, or put another word in Suggested with your reasoning in
   Comments. Leave a row untouched if you have no opinion.
3. Fill in "About you", tick the Required boxes under "Before you submit", and keep one choice on
   the "Credit me as" line.
4. Open a pull request with your file. Sign off each commit:

   ```sh
   git commit -s
   ```

## Good to know

- **A suggestion adds an option.** It never replaces the current word. Other reviewers can endorse
  it, and a pack changes only when the evidence says so.
- **The Required boxes are yours to tick.** The review check fails without them, and nobody can
  tick them for you, because they record your own agreement.
- **Your file is public once merged, comments included.** Never put an email address or private
  contact detail in it.

## What happens next

1. A maintainer runs the review check, reads every line, and replies on your pull request within
   7 days: either it is ready to merge, or the reply names exactly what to fix.
2. Push any fixes to the same branch, with each commit signed off.
3. After the merge, your endorsements and suggestions join the public language corpus. A new word
   you suggest is held until a maintainer clears it.
4. Endorsements add up. When a language crosses a review gate, a new pack version ships, and the
   pack can move from experimental to reviewed and, through a ratification session, to official.

## Read more

- [Start here](https://github.com/legesher/language-packs#start-here) in the language-packs repository
- [The reviewing guide](https://github.com/legesher/language-packs/blob/main/REVIEWING.md): how to choose a word, who can review, and how a pack becomes
  official
- Your language has no pack yet? [Request a new language](https://github.com/legesher/legesher/issues/new?template=add_language.yml).

More ways to contribute are coming.
