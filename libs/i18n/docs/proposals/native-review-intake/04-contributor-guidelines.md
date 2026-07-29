# Contributor guidelines: native language-pack review (DRAFT)

Draft of the public-facing guidelines — intended home once ratified:
`libs/i18n/REVIEWING.md` in the monorepo, linked from CONTRIBUTING.md and
the review app's onboarding. Written to be read by linguists and teachers,
not only developers.

---

## 1. What this is

Legesher language packs let people write and read code in their own
language. Every pack starts **experimental** — machine-proposed words that
pass our mechanical checks — and becomes **official** only through review
by people who actually speak the language. That review is what you're here
to do, and it makes you an open-source contributor to Legesher, credited
like any other.

## 2. The mindset: translate the concept, not the word

Ask yourself: **if computer science had been born in your language, how
would this concept be taught?** What would the textbook call it? We are
not looking for the English word dressed in your script — we're looking
for the word your language would have chosen on its own.

In practice:

- **Established terms win.** If your community's classrooms already have a
  word for *division by zero* or *loop*, that word beats anything a model
  proposes. Tell us it's established — that's evidence.
- **Coining is legitimate.** Many concepts (`deprecation`, `generator`)
  have no native term anywhere yet. Proposing one is not cheating; it is
  how every language built its scientific vocabulary (we follow ISO 704's
  spirit: name the concept by its essential characteristics).
- **Genuine loanwords are yours too.** If your language really says
  «كمبيوتر» or "computer", keeping it is a native judgment, not a failure.
  Mark it *cognate/loanword*.
- **Transliteration is labeled, not banned.** A sound-copy of the English
  word (e.g. `الفور` for `for`) is usually a translator's dodge — our
  models are forbidden from proposing them. But if a phonetic borrowing is
  genuinely what your community uses and prefers, you may submit or
  endorse it — tick the **transliteration** tag so the preference is
  visible and honest. If most reviewers of your language prefer
  transliterated terms, that pattern becomes part of your language's
  recorded terminology policy rather than something we pretend isn't
  happening.
- **Phrases get two answers.** For compound tokens (`elif` = "else if"),
  first agree how the *idea* reads in full in your language, then how it
  contracts into a single token. Both matter: the expansion teaches; the
  contraction ships.

## 3. What you can contribute (three tracks)

1. **Reserved words** (the priority): keywords, builtins, exceptions —
   ~183 concepts. Because packs are concept-keyed, your review of `break`
   ships in every programming language that has `break`.
2. **Error messages & common phrases**: the ~50 most-seen messages first
   (short beats long — measured), placeholders preserved, original always
   shown alongside.
3. **Style profile**: ten questions about how code should *read* in your
   language — how compound words join, what replaces UPPERCASE for
   constants where your script has no case, adjective/noun order in
   compounds, digit policy, docstring register. Your answers become your
   language's style guide — which is always a **suggestion** for writers,
   never a law.

Beyond the chosen words, your comments — how you'd explain a concept to a
student, how words should be formed, register notes — are collected (with
credit, moderated for conduct) into the open terminology corpus that
improves `legesher translate` for your language. Nothing you write is
wasted, including words that don't win.

## 4. Who can review, and the reviewer ladder

Anyone may submit. Endorsements are weighted by rung:

| rung | how you get there | weight |
| --- | --- | --- |
| anonymous | no account | recorded, weight 0 |
| contributor | signed-in contributor | low |
| native (claimed) | self-attest native/fluent at sign-up | counts toward review |
| native (verified) | vouched by an existing verified reviewer of that language, **or** a short verification call with a maintainer, **or** institutional affiliation (teacher/linguist) | full native weight; counts toward promotion |
| certified | credentialed engagements (education/accreditation lane — may be paid; see §8) | highest |
| maintainer | Legesher maintainers | equal to certified — on what a word means in your language, a maintainer does not outrank a certified native speaker |

Verification raises the *weight* of your voice, never the welcome: claimed
reviewers do full reviews; verification can come after. One honest detail:
each endorsement carries the rung you held **at the moment you made it** —
that snapshot is permanent evidence and is not silently rewritten when you
level up. Instead, after verification the app offers a one-tap
**re-affirmation**: it re-endorses everything you previously endorsed at
your new rung (the old records stay, retracted, as history). Your earlier
work is never lost — it just asks one tap to carry your new weight.

## 5. The review flow (what to expect)

1. **Your word first.** For each concept you see the definition and a code
   example, and record your own term *before* seeing any candidate — plus
   whether it's established, a coinage, or unsure.
2. **Then the candidates.** Everything we've collected — model proposals,
   terms from other localization projects (Hedy, UniversalPython, UniPy,
   Scratch — shown with credit), the current pack, other contributors'
   words, deduplicated. Sources are hidden until you've ranked, so words
   compete on merit.
3. **Endorse, rank, tag, comment.** Endorse every word you'd genuinely
   teach; rank your endorsements; slot 1 is "ship this". Tag descriptors
   (transliteration/cognate/established/coinage/register). Skipping a word
   is always allowed and means "no opinion."
4. **There are no downvotes.** Disagree by endorsing a better word — or
   proposing one. The **flag** is reserved for real problems (offensive,
   wrong meaning, wrong register, spam) and asks for a sentence of
   explanation.
5. **Submit.** You'll confirm the attestations (§6) and get a verification
   report. Partial reviews submit cleanly — 30 concepts reviewed well beat
   183 rushed.

## 6. Rules and gates

Blocking (mechanical or conduct — the only things that block):

- **Identifier physics**: terms must be valid identifiers — no spaces or
  punctuation, stable under Unicode NFKC normalization, consistent script,
  no invisible characters. The editor checks this live; a failing term is
  kept as evidence but cannot ship.
- **Round-trip**: two different English concepts cannot share one
  translated word within your language (code must translate back
  losslessly). The editor shows you the collision when it happens.
- **Placeholders** (messages track): `{name}`-style placeholders must
  survive, though you may reorder them.
- **Conduct**: submissions pass the Code of Conduct — including its
  language-and-accessibility provisions. Harassment, slurs, or PII in
  comments return or reject a submission.

Explicitly **not** gates:

- Disagreeing with a model. Model output is material, not authority —
  multilingual models underperform in exactly the languages we care most
  about, and your creative judgment is the point of this process.
- Novel coinages. A word nobody proposed before routes to a second native
  reviewer — more human eyes, never machine rejection.
- Transliteration tags, register choices, or any style preference.

## 7. How packs become official

| status | meaning | criteria |
| --- | --- | --- |
| **experimental** | ships now, honestly labeled | mechanical gates pass; no native review required — review is iterative and never blocks availability |
| **reviewed** | native speakers have signed off | full coverage; ≥80% of terms at reviewed status (each = ≥2 native endorsements, no open flags); ≥1 verified native reviewer covered the full surface |
| **official** | the certified tier | ≥95% reviewed; ≥2 distinct verified native reviewers; style profile answered; zero open flags; stable for a release cycle |

(Threshold numbers are ratified by maintainers and may be tuned; the
criteria themselves are public queries — you can always see exactly what
your language still needs, and the app points you at the highest-leverage
gaps first.)

Packs can move down as well as up: a verified defect returns a term to
experimental until re-reviewed. Nothing is deleted; every submitted word
and comment remains part of the record (withdrawable for privacy — see
§9).

## 8. Recognition

- **Credited contribution, your way**: at submission you choose how public
  credit reads — **anonymous** (an opaque contributor id; the default),
  **your username**, or **your name as you choose to write it**. Whatever
  you pick appears (or doesn't) in the language's CONTRIBUTORS section,
  the repo's all-contributors roll, and the public locale dashboard — and
  you can change the choice later. Your endorsements count identically in
  every case.
- **Founding reviewer**: the first verified native reviewer(s) to carry a
  language to *reviewed* are marked as such permanently.
- **Reach**: concept-keyed review means your work ships across programming
  languages — the dashboard shows "your review of `break` ships in N
  packs."
- **Paid lane, named honestly**: reviewing here is volunteer open-source
  contribution. Separately, Legesher's education offerings engage
  fair-wage reviewers for course-edition and accreditation work; verified
  reviewers from this program are the natural candidates when those
  engagements exist. One does not require the other.

## 9. Licensing, attribution, privacy

- Submitted terms and comments are contributed under **Apache-2.0** (the
  pack data license) with sign-off (DCO); you attest the work is yours.
- The published corpus credits you by opaque contributor id (plus your
  chosen credit, where you chose one). Your identity details are never
  part of the published dataset, and you may withdraw your identity at any
  time — counts survive, your personal data does not.
- **We ask for a contact email with every submission.** It's how we reach
  you about your review — a question from another reviewer, a credit
  issue, or verification. It's checked for validity, stored privately
  alongside your identity (never in the public repo, never in the
  dataset), and deleted with the rest of your identity if you withdraw.
- Terms shown from other projects (Hedy, UniversalPython, UniPy, Scratch)
  appear with attribution; endorsing one records *your* independent
  judgment of that word.
- **Your contributions may appear in research.** The open corpus (terms,
  endorsements, tags, expansions, published comments — keyed by your opaque
  id) is research data by design, and we may publish analyses of it. Your
  identity, email, and private session details are never part of that.
- **Published dataset versions are permanent.** Withdrawal removes your
  identity everywhere and stops your words and comments from appearing in
  *future* releases — but dataset versions already published and downloaded
  by others cannot be recalled. We say this plainly because append-only
  honesty cuts both ways.

## 10. Moderation & appeals

Flags and conduct screens are resolved by maintainers (append-only record;
resolution visible on the option). A returned submission tells you exactly
why and how to fix it; a rejected one cites the guideline. Appeals follow
the Code of Conduct's appeal path.
