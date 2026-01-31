# Respond to PR Comments: $ARGUMENTS

**Goal**: Fetch, review, and respond to all review comments on the current PR (or specified PR number).

## Instructions

### 1. Identify the PR

- If `$ARGUMENTS` contains a PR number, use that
- Otherwise, detect from the current branch: `gh pr view --json number`

### 2. Fetch All Review Comments

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments
```

### 3. For Each Comment, Respond

**If the issue was already fixed in a subsequent commit:**

- Reply with the commit SHA and a brief explanation of what was changed
- Example: "Fixed in commit `abc1234` — [description of fix]."

**If the issue is being intentionally not addressed:**

- Reply with a clear rationale for why
- Example: "These dates are intentionally different because [reason]. No change needed."

**If the issue needs to be fixed now:**

- Make the code change first
- Commit the fix
- Then reply with the commit SHA referencing the fix

**If the comment is informational/minor (e.g., style nits from auto-formatters):**

- Acknowledge briefly
- Example: "This was an auto-formatter side effect. Not reverting as it's harmless in docs."

### 4. Response Format

Keep replies concise and direct:

- Lead with the action taken (or not taken)
- Reference commit SHAs when changes were made
- Explain rationale when not implementing a suggestion
- No filler or excessive politeness — be professional and factual

### 5. Post Responses

Use the GitHub API to reply in-thread to each comment:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments \
  -f body="Response text" \
  -F in_reply_to={comment_id}
```

### 6. Update Linear

After responding to all comments, add a summary comment to the associated Linear ticket documenting:

- How many comments were addressed
- Which were implemented vs. declined with rationale
- Any remaining action items

## Checklist

- [ ] All review comments have replies
- [ ] Code fixes committed where needed
- [ ] Linear ticket updated with summary
