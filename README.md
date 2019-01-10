<img src="https://github.com/madiedgar/legesher/blob/master/styles/images/testOstrich.png" align="left" height="400px"/>

# Welcome to Legesher 👋

>**Legesher** _(leg - ah - share)_: to bridge; to connect

### Because innovation and creativity shouldn't be lost in translation
We are all about building bridges to empower others towards the direction of their lives. With **Legesher**, our bridges allow people to code in their native language. Legesher is designed for individuals where English is a second language and for diverse teams that span across many other barriers already.

**Legesher** is a tool that enables anyone to code in their native language. In order to do that we have several projects within the **Legesher** theme to support such an mission. We built **Legesher** on top of [Atom](atom.io), a hackable text editor, in order to give users as much of a personal invitation to programming as we could.

# Developing with Legesher 💻
👷 Currently, Legesher is a **work in progress** / in the formation phase. We would love your help to get it up and running! Check out our [roadmap](https://github.com/madiedgar/legesher/issues) for the latest updates.

<img src="https://github.com/madiedgar/legesher/blob/master/styles/images/EggPeggy@4xCutWithShadow.png" align="left" height="350px"/>

Designed for beginner developers in mind, we're starting this README.md from the very top! For more in-depth tutorials, head on over to our [wiki](https://github.com/madiedgar/legesher/wiki). If you would like more clarity on a certain topic, _submit a pull request_ or [tweet @ us 🐦](https://twitter.com/legesherio).

### 1️⃣ Download A Text Editor
> **Text Editor** - an interface that allows you to open and edit your code in an user-friendly environment

At this time, we are only actively working on extensions for the following open sourced text editors. If there is another you would like to have included on this list, please _submit a pull request_ and we'll see how all of us can make it happen!
-   [Atom](https://atom.io) <!-- insert Atom logo -->
-   [VS Code](https://code.visualstudio.com/)  <!-- insert VS Code logo -->


### 2️⃣ Install Legesher Packages
Legesher is a collection of packages that enable you to code across language barriers. Use any one or all of them to change the way you work, hopefully allowing your innovation and creativity to flourish.

Navigate to the `Install` section in your editor's settings and search `legesher` to pull up all of our projects. <!-- TODO: Insert Install Screenshot -->

:baggage_claim: **`legesher-LANGUAGE`**
> **`legesher-LANGUAGE`** : this package allows you to code in any spoken language.

This is where our heart ❤️ is. We want this list to expand, so if you know a language (or a specific dialect) that is not listed below please check the `translation` tag in the issues to join the effort. To add another language, follow [this tutorial](https://github.com/madiedgar/legesher/wiki/Add-New-Language) to add it to our project.

The current list of _supported_ dialects:
-   [Spanish (Mexico)](https://github.com/madiedgar/Legesher/tree/master/languages/spanish-mexico)
-   [French (France)](https://github.com/madiedgar/Legesher/tree/master/languages/french-france)

The current list of _work in progress_ dialects:
-   Portuguese
-   Ukrainian
-   Mandarin
-   Korean
-   Arabic

🛄 **`legesher-ui`**
> **`legesher-ui`** : this package theme allows your editor to have the layout to go between languages.

🛄 **`legesher-syntax`**
> **`legesher-syntax`** : this package theme allows your code to be properly vizualized.

### 3️⃣ Start Coding
That's it! You're good to go and start coding. We have [several tutorials](https://github.com/WithMadi/BetaTeam) to get you on your way!

🛄 **`legesher-docs`**
> **`legesher-docs`** : this resource allows you an inside look on the code behind the packages above as well as tutorials to best utilize these tools.

# Contributing to Legesher 🎁
We would love for you to join in our community, because we need you! What are you gifted in? Head on over to the project's [current open issues](https://github.com/madiedgar/Legesher/issues) to see what you can get involved in!  

There are 2 main components and depending on what kind of feature you're writing, you may need to change one or more of these.

## Translator
Legesher allows for the user to code in any desired spoken language available within the `languages/*` folder. The transcompiler `legesherc` is the tool responsible for running the program in the desired spoken language. `legesherc` is written in Python and uses the `pythonparser` module to accomplish parsing.

The `legesherc` script itself lives at `tools/legesherc`.

## Legesher Platform
In order for users to take full advantage of the gift of Legesher, the platform needs to be developed. 🎉 We started developing on the Atom text editor.

When you find something you'd like to help with, please spend some time reading our [Contributing Guide](https://github.com/madiedgar/Legesher/blob/master/CONTRIBUTING.md) for more details in contributing and our [Code of Conduct](https://github.com/madiedgar/Legesher/blob/master/CODE_OF_CONDUCT.md) to maintain the healthy space our community thrives in!

## Source Code Overview
-   `assets`: Contains all of the images and branding of the project
-   `community`: Dedicated to all of the individuals who made this project possible
-   `compiler`: Python package implementing Python in English -> Python trans-compiled language
-   `config`:
-   `docs`: Documentation and style guides for the project
-   `grammars`: Translations for keywords and error messages
-   `spec`:
-   `styles`:
-   `tools`: Transcompilation and utility binaries

### Running  
### Testing  
### Deploying  

### Need Help?
If you can't find the answer there, open an issue in this repository and add the label `question`.

# Our People :handshake:
Out community is full of inspiring people with a heart for others. Although it's rather small in comparison to the impact they've had, we'd like to recognize the people who have made this happen.

### Supporters
This project is maintained by a [passionate community](https://github.com/madiedgar/Legesher/blob/master/community) (and) [With Madi Co.](https://withmadi.co). To give towards the development of this project, please visit our [Patreon page](https://www.patreon.com/madiedgar).

### Contact
Questions? Comments? Drop us a line at [legesher@gmail.com](mailto:legesher@gmail.com) or join our [Slack channel](https://join.slack.com/t/codewithmadi/shared_invite/enQtNDM1NDU4NTY4MjA5LTc0ODAyNjM5OTI4ZjJlZjYxNTdhNWQ5OGE4MjNjNzRiMjBmZjczNTkxYTU1ZWFhZDg1NGY2OWRlMzhlOWMyODQ).

-----------------------------------

Use of this project under the [MIT License](https://github.com/madiedgar/Legesher/blob/master/LICENSE).
