# Introduction

### THANK YOU :heart:

First off, thank you for just being _here_. It's people like you who have a heart to serve and desire to create something bigger than themselves that we want to be on our team. So thank you, because by considering t ocontribute to Legesher, we know you're a person we'd love to be with. This is so much more than a product, it's an opportunity that opens doors. Thank you for making all of this possible.

### Read All About It :book:

We all have the same goal: for this community to create a product that empowers individuals. Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

### Be a Part :handshake:

This is a space for you to share your talents, gitfs, and abilities to serve one another. There are many ways to contribute (even if you don't know how to code - _yet_)! From writing tutorials or blog posts, improving the documentation, submitting bug reports and feature requests, translating to another language or writing code, we would love to have you share your God-given abilities with us!

Here are some important and helpful resources:

-   [Tutorials Would Go Here](https://github.com/WithMadi/BetaTeam)
-   [Join Our Slack Conmmunity!](https://join.slack.com/t/codewithmadi/shared_invite/enQtNDM1NDU4NTY4MjA5LTc0ODAyNjM5OTI4ZjJlZjYxNTdhNWQ5OGE4MjNjNzRiMjBmZjczNTkxYTU1ZWFhZDg1NGY2OWRlMzhlOWMyODQ)
    -   Use the `Legesher` channel for questions about Legesher
    -   Use the `tutorials` channel for questions about Legesher, Github, or Programming tutorials
    -   There are many other channels available, check the channel list
-   [Current Project Status](<>) (we're keeping everything on Github for the time being)

# Ground Rules

When contributing it is important to make sure we follow the same guidelines:

-   Be welcoming to newcomers and encourage diverse new contributors from all backgrounds. [(Read More)](https://github.com/madiedgar/Legesher/blob/master/CODE_OF_CONDUCT.md)
-   Ensure cross-platform compatibility for every change that's accepted. (Windows, Mac, Debian & Ubuntu Linux)
-   Ensure that code that goes into core meets all requirements in [this checklist](https://github.com/madiedgar/Legesher/tree/master/.github/ISSUE_TEMPLATE):
-   Create issues for any major changes and enhancements that you wish to make. Discuss things transparently and get community feedback.
-   Don't add any classes to the codebase unless absolutely needed. Err on the side of using functions.
-   Keep feature versions as small as possible, preferably one new feature per version.

# Your First Contribution

If this is your first time contributing to the Legesher project, then we have something special for you. Upon merging of your first contribution, you'll get a free starter pack and a big welcome into the community!

One great way to begin contributing is to look for issues with the `beginner`, `help wanted` or `great first issue` label.

-   `beginner`: issues which should only require a few lines of code, and a test or two.
-   `help wanted`: issues which should be a bit more involved than beginner issues.
-   `great first issue`: issues for individuals new to programming or the github platform.

**If you've never contributed to an open source project before**
Here are a couple of friendly tutorials that may help:

-   [Make A Pull Request](http://makeapullrequest.com/)
-   [First Timers Only](http://www.firsttimersonly.com/)
-   [How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github).

# Getting Started

**TESTS** If you are changing the code base of the project, you will need to perform the provided tests before your changes can be merged. If you add new features to the project, please include tests with your pull request.

To run the tests, run the following command:

```sh
test project
```

**DOCUMENTATION** The more documentation we have the easier it will be for our project to be used. Documentation will change constantly, as we improve the way the product works and we gain better ways of explaining.

**TUTORIALS** If there was anything you do not currently understand or did not while going through the current tutorials, please update them to improve their usefulness. This is for the betterment of our community, we all thank you for it!

**For updates larger than a one or two line fix:**
1\. Create your own fork of the code
2\. Do the changes in your fork
3\. If you like the change and think the project could use it:

-   Be sure you have followed the code style for the project.
-   Note the Legesher Code of Conduct.
-   Add your name to the `CONTRIBUTORS` file.
-   Send a pull request and be open for feedback.

# Style Guide

### Commit Messages Guidelines

A good commit message should describe what changed and why. This project uses semantic commit messages to streamline the release process.

Before a pull request can be merged, it must have a pull request title with a semantic prefix.

Examples of commit messages with semantic prefixes:

-   `fix: don't overwrite prevent_default if default wasn't prevented`
-   `feat: add app.isPackaged() method`
-   `docs: app.isDefaultProtocolClient is now available on Linux`
    Common prefixes:

-   fix: A bug fix
-   feat: A new feature
-   docs: Documentation changes
-   test: Adding missing tests or correcting existing tests
-   build: Changes that affect the build system
-   ci: Changes to our CI configuration files and scripts
-   perf: A code change that improves performance
-   refactor: A code change that neither fixes a bug nor adds a feature
-   style: Changes that do not affect the meaning of the code (linting)
-   vendor: Bumping a dependency like libchromiumcontent or node

Other things to keep in mind when writing a commit message:

1.  The first line should:

-   contain a short description of the change (preferably 50 characters or less, and no more than 72 characters)
-   be entirely in lowercase with the exception of proper nouns, acronyms, and the words that refer to code, like function/variable names

2.  Keep the second line blank.
3.  Wrap all other lines at 72 columns.

**Breaking Changes**
A commit that has the text `BREAKING CHANGE:` at the beginning of its optional body or footer section introduces a breaking API change (correlating with Major in semantic versioning). A breaking change can be part of commits of any type. e.g., a `fix:`, `feat:` & `chore:` types would all be valid, in addition to any other type.

See [conventionalcommits.org](https://conventionalcommits.org/) for more details.

-   Use the present tense ("Add feature" not "Added feature")
-   Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
-   Limit the first line to 72 characters or less
-   Reference issues and pull requests liberally after the first line
-   When only changing documentation, include `[ci skip]` in the commit title
-   Consider starting the commit message with an applicable emoji:
    -   :art: `:art:` when improving the format/structure of the code
    -   :racehorse: `:racehorse:` when improving performance
    -   :non-potable_water: `:non-potable_water:` when plugging memory leaks
    -   :memo: `:memo:` when writing docs
    -   :penguin: `:penguin:` when fixing something on Linux
    -   :apple: `:apple:` when fixing something on macOS
    -   :checkered_flag: `:checkered_flag:` when fixing something on Windows
    -   :bug: `:bug:` when fixing a bug
    -   :fire: `:fire:` when removing code or files
    -   :green_heart: `:green_heart:` when fixing the CI build
    -   :white_check_mark: `:white_check_mark:` when adding tests
    -   :lock: `:lock:` when dealing with security
    -   :arrow_up: `:arrow_up:` when upgrading dependencies
    -   :arrow_down: `:arrow_down:` when downgrading dependencies
    -   :shirt: `:shirt:` when removing linter warnings

# Bug :bug: Reports

### Security

If you find a security vulnerability, do NOT open an issue. Email <mailto:legesher@gmail.com> instead.
In order to determine whether you are dealing with a security issue, ask yourself these two questions:

-   Can I access something that's not mine, or something I shouldn't have access to?
-   Can I disable something for other people?

If the answer to either of those two questions are "yes", then you're probably dealing with a security issue. Note that even if you answer "no" to both questions, you may still be dealing with a security issue, so if you're unsure, just email us at <mailto:legesher@gmail.com>.

### How to Report a Bug

Answer [these questions](https://github.com/madiedgar/Legesher/blob/master/.github/ISSUE_TEMPLATE/bug_report.md) when reporting a bug.

# Feature :rocket: or Enhancement Suggestions

Answer [these questions](https://github.com/madiedgar/Legesher/blob/master/.github/ISSUE_TEMPLATE/feature_request.md) when suggesting a feature or enhancement.

# Code Review Process

### Language Translations

-   The translated file will need to be reviewed by at least 2 different community members to make sure it is appropriate and the best translation that will allow the developer to best understand the foundation of programming.
-   After 2 approved reviews, all 3 contributors will be given credit for the addition of the language when it is merged with the project.

### Code

-   The pull request will need to be reviewed by at least one member of the maintainer community before it can be merged into the project.
