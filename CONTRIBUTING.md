# Introduction

### THANK YOU :heart:

First off, thank you for just being _here_. It's people like you who have a heart to serve and desire to create something bigger than themselves that we want to be on our team. So thank you, because by considering t ocontribute to Barak, we know you're a person we'd love to be with. This is so much more than a product, it's an opportunity that opens doors. Thank you for making all of this possible. 

### Read All About It :book:

We all have the same goal: for this community to create a product that empowers individuals. Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

### Be a Part :handshake:

This is a space for you to share your talents, gitfs, and abilities to serve one another. There are many ways to contribute (even if you don't know how to code - _yet_)! From writing tutorials or blog posts, improving the documentation, submitting bug reports and feature requests, translating to another language or writing code, we would love to have you share your God-given abilities with us! 

Here are some important and helpful resources:
- [Tutorials Would Go Here]()
- [Join Our Slack Conmmunity!]()
    - Use the `barak` channel for questions about Barak
    - Use the `tutorials` channel for questions about Barak, Github, or Programming tutorials
    - There are many other channels available, check the channel list 
- [Current Project Status]() (we're keeping everything on Github for the time being)

# Ground Rules
When contributing it is important to make sure we follow the same guidelines: 
* Be welcoming to newcomers and encourage diverse new contributors from all backgrounds. [(Read More)](https://github.com/madipfaff/barak/blob/master/CODE_OF_CONDUCT.md)
* Ensure cross-platform compatibility for every change that's accepted. (Windows, Mac, Debian & Ubuntu Linux)
* Ensure that code that goes into core meets all requirements in this checklist: https://github.com/madipfaff/barak/tree/master/.github/ISSUE_TEMPLATE
* Create issues for any major changes and enhancements that you wish to make. Discuss things transparently and get community feedback.
* Don't add any classes to the codebase unless absolutely needed. Err on the side of using functions.
* Keep feature versions as small as possible, preferably one new feature per version.

# Your First Contribution
If this is your first time contributing to the Barak project, then we have something special for you. Upon merging of your first contribution, you'll get a free starter pack and a big welcome into the community!

One great way to begin contributing is to look for issues with the `beginner`, `help wanted` or `great first issue` label.
- `beginner`: issues which should only require a few lines of code, and a test or two.
- `help wanted`: issues which should be a bit more involved than beginner issues.
- `great first issue`: issues for individuals new to programming or the github platform. 

**If you've never contributed to an open source project before**
Here are a couple of friendly tutorials that may help: 
- [Make A Pull Request](http://makeapullrequest.com/)
- [First Timers Only](http://www.firsttimersonly.com/)
- [How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github).

# Getting Started

**TESTS** If you are changing the code base of the project, you will need to perform the provided tests before your changes can be merged. If you add new features to the project, please include tests with your pull request. 

To run the tests, run the following command:
```sh
test project
```

**DOCUMENTATION** The more documentation we have the easier it will be for our project to be used. Documentation will change constantly, as we improve the way the product works and we gain better ways of explaining.

**TUTORIALS** If there was anything you do not currently understand or did not while going through the current tutorials, please update them to improve their usefulness. This is for the betterment of our community, we all thank you for it!

**For updates larger than a one or two line fix:**
1. Create your own fork of the code
2. Do the changes in your fork
3. If you like the change and think the project could use it:
    * Be sure you have followed the code style for the project.
    * Note the Barak Code of Conduct.
    * Add your name to the `CONTRIBUTORS` file.
    * Send a pull request and be open for feedback.
    
# Style Guide
### Git Commit Messages
* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* When only changing documentation, include `[ci skip]` in the commit title
* Consider starting the commit message with an applicable emoji:
    * :art: `:art:` when improving the format/structure of the code
    * :racehorse: `:racehorse:` when improving performance
    * :non-potable_water: `:non-potable_water:` when plugging memory leaks
    * :memo: `:memo:` when writing docs
    * :penguin: `:penguin:` when fixing something on Linux
    * :apple: `:apple:` when fixing something on macOS
    * :checkered_flag: `:checkered_flag:` when fixing something on Windows
    * :bug: `:bug:` when fixing a bug
    * :fire: `:fire:` when removing code or files
    * :green_heart: `:green_heart:` when fixing the CI build
    * :white_check_mark: `:white_check_mark:` when adding tests
    * :lock: `:lock:` when dealing with security
    * :arrow_up: `:arrow_up:` when upgrading dependencies
    * :arrow_down: `:arrow_down:` when downgrading dependencies
    * :shirt: `:shirt:` when removing linter warnings

# Report a Bug :bug:
### Security 
If you find a security vulnerability, do NOT open an issue. Email mailto:withmadico@gmail.com instead.
In order to determine whether you are dealing with a security issue, ask yourself these two questions:
* Can I access something that's not mine, or something I shouldn't have access to?
* Can I disable something for other people?

If the answer to either of those two questions are "yes", then you're probably dealing with a security issue. Note that even if you answer "no" to both questions, you may still be dealing with a security issue, so if you're unsure, just email us at mailto:withmadico@gmail.com.

### Tell your contributors how to file a bug report.
You can even include a template so people can just copy-paste (again, less work for you).

> When filing an issue, make sure to answer these five questions:
>
> 1. What version of Go are you using (go version)?
> 2. What operating system and processor architecture are you using?
> 3. What did you do?
> 4. What did you expect to see?
> 5. What did you see instead?
> General questions should go to the golang-nuts mailing list instead of the issue tracker. The gophers there will answer or ask you to file an issue if you've tripped over a bug.

[source: [Go](https://github.com/golang/go/blob/master/CONTRIBUTING.md#filing-issues)] **Need more inspiration?** [1] [Celery](https://github.com/celery/celery/blob/master/CONTRIBUTING.rst#other-bugs ) [2] [Atom](https://github.com/atom/atom/blob/master/CONTRIBUTING.md#reporting-bugs) (includes template)

# How to suggest a feature or enhancement
### If you have a particular roadmap, goals, or philosophy for development, share it here.
This information will give contributors context before they make suggestions that may not align with the project’s needs.

> The Express philosophy is to provide small, robust tooling for HTTP servers, making it a great solution for single page applications, web sites, hybrids, or public HTTP APIs.
>
> Express does not force you to use any specific ORM or template engine. With support for over 14 template engines via Consolidate.js, you can quickly craft your perfect framework.

[source: [Express](https://github.com/expressjs/express#philosophy)] **Need more inspiration?** [Active Admin](https://github.com/activeadmin/activeadmin#goals)

### Explain your desired process for suggesting a feature.
If there is back-and-forth or signoff required, say so. Ask them to scope the feature, thinking through why it’s needed and how it might work.

> If you find yourself wishing for a feature that doesn't exist in Elasticsearch, you are probably not alone. There are bound to be others out there with similar needs. Many of the features that Elasticsearch has today have been added because our users saw the need. Open an issue on our issues list on GitHub which describes the feature you would like to see, why you need it, and how it should work.

[source: [Elasticsearch](https://github.com/elastic/elasticsearch/blob/master/CONTRIBUTING.md#feature-requests)] **Need more inspiration?** [1] [Hoodie](https://github.com/hoodiehq/hoodie/blob/master/CONTRIBUTING.md#feature-requests) [2] [Ember.js](https://github.com/emberjs/ember.js/blob/master/CONTRIBUTING.md#requesting-a-feature)

# Code review process
### Explain how a contribution gets accepted after it’s been submitted.
Who reviews it? Who needs to sign off before it’s accepted? When should a contributor expect to hear from you? How can contributors get commit access, if at all?

> The core team looks at Pull Requests on a regular basis in a weekly triage meeting that we hold in a public Google Hangout. The hangout is announced in the weekly status updates that are sent to the puppet-dev list. Notes are posted to the Puppet Community community-triage repo and include a link to a YouTube recording of the hangout.
> After feedback has been given we expect responses within two weeks. After two weeks we may close the pull request if it isn't showing any activity.

[source: [Puppet](https://github.com/puppetlabs/puppet/blob/master/CONTRIBUTING.md#submitting-changes)] **Need more inspiration?** [1] [Meteor](https://meteor.hackpad.com/Responding-to-GitHub-Issues-SKE2u3tkSiH ) [2] [Express.js](https://github.com/expressjs/express/blob/master/Contributing.md#becoming-a-committer)

# Community
If there are other channels you use besides GitHub to discuss contributions, mention them here. You can also list the author, maintainers, and/or contributors here, or set expectations for response time.

> You can chat with the core team on https://gitter.im/cucumber/cucumber. We try to have office hours on Fridays.

[source: [cucumber-ruby](https://github.com/cucumber/cucumber-ruby/blob/master/CONTRIBUTING.md#talking-with-other-devs)] **Need more inspiration?**
 [1] [Chef](https://github.com/chef/chef/blob/master/CONTRIBUTING.md#-developer-office-hours) [2] [Cookiecutter](https://github.com/audreyr/cookiecutter#community)

# BONUS: Code, commit message and labeling conventions
These sections are not necessary, but can help streamline the contributions you receive.

### Explain your preferred style for code, if you have any.

**Need inspiration?** [1] [Requirejs](http://requirejs.org/docs/contributing.html#codestyle) [2] [Elasticsearch](https://github.com/elastic/elasticsearch/blob/master/CONTRIBUTING.md#contributing-to-the-elasticsearch-codebase)

### Explain if you use any commit message conventions.

**Need inspiration?** [1] [Angular](https://github.com/angular/material/blob/master/.github/CONTRIBUTING.md#submit) [2] [Node.js](https://github.com/nodejs/node/blob/master/CONTRIBUTING.md#step-3-commit)

### Explain if you use any labeling conventions for issues.

**Need inspiration?** [1] [StandardIssueLabels](https://github.com/wagenet/StandardIssueLabels#standardissuelabels) [2] [Atom](https://github.com/atom/atom/blob/master/CONTRIBUTING.md#issue-and-pull-request-labels)
