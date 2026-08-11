# Contributor withdrawal runbook

<!-- disposition: MAINTAINER (CORE-1724 audit, 2026-08-11) -->

> **Maintainer-only.** The operator procedure for honouring a withdrawal request. What we promise
> contributors is in [CONTRIBUTOR_PRIVACY.md](../../../CONTRIBUTOR_PRIVACY.md); this is how the
> promise is kept.
>
> It is published openly on purpose. A privacy commitment whose mechanism is secret is a commitment
> nobody can check.

## Two things to understand first

**No published dataset changes when someone withdraws.** The corpus has never carried an identity:
`contributors` holds an opaque id, a rung and a join date, and `contributor_identities` is
structurally excluded from every export. The link between an id and a person exists in exactly one
place, privately. So withdrawal is not a retraction — nothing needs re-pushing, no revision needs
rewriting, and no consumer of the dataset is affected.

**The withdrawal is recorded in the identity map, not in a database.** There is no operational v2
database yet: `migrate_to_v2.py` rebuilds it from scratch every time, and identities come from
the private identity map (`identity/contributor_identity_map.json` in the durable data home,
loaded via `$LEGESHER_DATA_REPO` — moved out of the script's source on CORE-1794). Editing a
built database would be undone by the next rebuild. This surprises people, so it is the first
thing stated here.

## 1. Get their opaque id

You need the id **before** removing the username, because the id is derived from it and the
derivation is one-way.

```bash
cd libs/i18n
read -rs LEGESHER_CONTRIBUTOR_SALT && export LEGESHER_CONTRIBUTOR_SALT
uv run python -c "
import os, sys
from legesher_i18n.db.schema_v2 import contributor_id
print(contributor_id(sys.argv[1], salt=os.environ['LEGESHER_CONTRIBUTOR_SALT']))
" "<github-username>"
```

Cross-check it against the published `contributors` config before continuing. If the id you just
computed is not in the corpus, you have the wrong username and everything below would erase the
wrong person.

## 1b. Confirm the request is theirs

Erasure is not cheaply reversible: reinstatement needs consent from someone whose contact address
you are about to delete. `privacy@legesher.com` is an unauthenticated inbox and the notice says
"Please remove me" is enough, so the *request* stays easy and the *verification* sits here.

Reply from the address in `contributor_identities.contact` or `email` if one is recorded, or ask
them to confirm from the GitHub account named in the request. A mistaken or spoofed message
otherwise erases a third party.

If no contact is on file and the account cannot be confirmed, say so and stop. Do not guess.

## 2. Replace their entry in the identity map

In the data home's `identity/contributor_identity_map.json`, move the label from
`identities` to `withdrawn`:

```json
// before, under "identities"
"<v1-label>": {"github_handle": "<github-username>", "display_name": "<display name>"}

// after, under "withdrawn"
"<v1-label>": {"contributor_id": "c_0123456789abcdef", "withdrawn_at": "2026-08-10"}
```

Then commit and push the data repository — the map there is the durable store,
and an unpushed withdrawal exists only on one workstation.

The placeholders are deliberate. Never write a worked example here using a real
map entry: the v1 label carries a real first name and the opaque id is a
published value, so pairing them in this file would publish exactly the mapping
`contributor_identities` exists to keep private -- in a document whose whole
point is that it can be read openly.

The entry **stays**; only the person leaves. Two failure modes this avoids:

- **Deleting the entry** makes `resolve_identity` refuse the entire build — an unknown v1 label is a
  hard stop by design, so a deletion does not erase them, it just breaks the migration.
- **Keeping the username with a flag** is not erasure. The map is the durable store; a username
  annotated "withdrawn" is a mapping we still hold and have merely promised not to use.

The opaque id is safe to keep in source: it is already published, and with the username gone it
leads nowhere.

## 3. Rebuild and verify

```bash
[ -f build/translations_v2.db ] && mv build/translations_v2.db build/translations_v2.superseded.db
uv run python scripts/migrate_to_v2.py \
    --source legesher_i18n/db/translations.db \
    --target build/translations_v2.db \
    --publish --acknowledge-message-rows-not-migrated
```

Three checks. All three must pass before you reply to the person.

```sql
-- 1. Nothing identifying survives, and the tombstone is set.
SELECT source_key, display_name, github_handle, contact, email, withdrawn_at
  FROM contributor_identities WHERE contributor_id = 'c_...';
-- expect: five NULLs, then the withdrawal date

-- 2. Their username survives nowhere.
SELECT COUNT(*) FROM contributor_identities WHERE source_key = '<github-username>';
-- expect: 0

-- 3. Their evidence is intact. Deleting it would silently move which word a
--    pack ships, for everyone, on the strength of one privacy request.
SELECT COUNT(*) FROM endorsements WHERE contributor_id = 'c_...';
-- expect: the same count as before
```

`test_a_withdrawn_contributor_keeps_their_endorsements_and_loses_their_identity` asserts all three
against a map entry it substitutes in, so it guards the *mechanism*, not this particular withdrawal.
`test_the_shipped_map_only_withdraws_published_ids` is the one that reads the real map. Run the
three checks above anyway: a recorded withdrawal reverted by a bad merge would not fail the suite.

**Do not re-push the corpus.** Running the publish sequence to "apply" a withdrawal would be a
misunderstanding of where the data lives. Nothing published changed.

## 4. Reply

Tell them what was done in the terms the notice uses: the mapping is erased, their endorsements
remain as anonymous data points, and no published dataset had to change because none of them ever
carried their name.

Be straight about the two things withdrawal cannot reach:

- **Public pull requests and issues** they opened themselves remain in the public repository under
  their own account.
- **Repository history.** Step 2 is a commit, and the commit before it still contains the username.
  Removing it from history requires a rewrite; if one is planned before this repository becomes
  public, say so and give the timeframe. Do not imply history is already clean.

## The importer rule

**A design constraint for the review-bundle importer (CORE-1688), which is not yet built.** Writing
it down now is cheaper than retrofitting it.

Review bundles carry the contributor's GitHub username. Because the salt is frozen, an importer can
always recompute the opaque id from that username — which is how it finds the tombstone without us
storing anything identifying.

On meeting a bundle whose contributor id has `withdrawn_at` set:

| bundle predates `withdrawn_at` | bundle postdates `withdrawn_at` |
| --- | --- |
| A replay of old history — a rebuild, not an event. | A person who has come back and submitted again. |
| Write the endorsement, do **not** populate any identity column, and report the count in the import ledger. | **Stop and surface it to a human.** It may be re-consent, or they may have forgotten. Do not decide it in code. |

Without this rule a rebuild silently recreates the identity from the bundle and undoes the
withdrawal. The date comparison is the entire implementation.

## Reinstatement

If a withdrawn contributor asks to return, restoring the entry is a deliberate act that re-captures
consent — never a side effect of an import:

```python
"<v1-label>": Identity("<github-username>", "<display name>"),  # consent re-captured YYYY-MM-DD, v1.0
```

Their historical endorsements reattach automatically, because the opaque id never changed.

## When this procedure changes

Once the review-intake write path lands and the v2 database becomes the operational store rather
than a build artifact, the tombstone moves from the identity map to a row update — the same columns, the
same three checks, without the rebuild. The identity map is a migration-era artifact; this document
should be revisited at that cutover.

## What this procedure does not cover

- **Removing contributions rather than identity.** A request to withdraw the *words* has a real cost
  to other contributors. It is a conversation, not a runbook.
- **Changing credit preference.** Moving between anonymous, handle and name is not a withdrawal and
  does not need any of this.
