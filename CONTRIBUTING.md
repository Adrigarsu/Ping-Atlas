# Contributing to Ping-Atlas

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to Ping-Atlas. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Code of Conduct

This project and everyone participating in it is governed by the [Ping-Atlas Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [adrigarsu@example.com].

## I Have a Question

> **Note:** If you want to ask a question, we assume that you have read the available [Documentation](https://github.com/Adrigarsu/Ping-Atlas/wiki).

Before you ask a question, it is best to search for existing [Issues](https://github.com/Adrigarsu/Ping-Atlas/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/Adrigarsu/Ping-Atlas/issues/new).
- Provide as much context as you can about what you're running into.
- Provide project and platform versions (Python, Node, Docker, etc.), depending on what seems relevant.

We will then take care of the issue as soon as possible.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for Ping-Atlas. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as many details as possible.
- **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples.
- **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
- **Explain which behavior you expected to see instead and why.**
- **Include screenshots and animated GIFs** which show you following the described steps and clearly demonstrate the problem.
- **If the problem wasn't triggered by a specific action**, describe what you were doing before the problem happened and share more information using the guidelines below.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for Ping-Atlas, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title** for the issue to identify the suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
- **Provide specific examples to demonstrate the steps**.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
- **Explain why this enhancement would be useful** to most Ping-Atlas users.
- **List some other applications where this enhancement exists.**
- **Specify the name and version of the OS you're using.**

### Pull Requests

- Fill in [the required template](PULL_REQUEST_TEMPLATE.md)
- Do not include issue numbers in the PR title
- Follow the [Python](#python-styleguide) and [JavaScript](#javascript-styleguide) styleguides
- Include thoughtfully-worded, well-structured tests for any new functionality
- Document new code based on the [Documentation Styleguide](#documentation-styleguide)
- End all files with a newline

## Development Setup

You'll need Docker and Docker Compose to get Ping-Atlas up and running. For development, you'll also need Python 3.11+ and Node.js 20+.

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/Adrigarsu/Ping-Atlas.git
   cd Ping-Atlas
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file to configure your desired settings (e.g., probe targets, intervals).

3. **Run with Docker Compose for development**

   ```bash
   docker compose up --build
   ```

   This will start the backend, frontend, and database services.

## Coding Standards

### Python Styleguide

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Use [Black](https://black.readthedocs.io/) to format your Python code.
- Use [isort](https://pycqa.github.io/isort/) to sort imports.
- We use [mypy](https://mypy-lang.org/) for static type checking. Ensure your code passes mypy checks.
- **Run tests:** Before submitting a pull request, ensure all tests pass.

  ```bash
  docker compose run --rm backend pytest
  ```

- **Add tests:** Please add tests for any new features or bug fixes.

### JavaScript/React Styleguide

- Use [ESLint](https://eslint.org/) and [Prettier](https://prettier.io/) to maintain a consistent code style.
- Use functional components and hooks for React development.
- Use meaningful variable and function names.

## Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Additional Notes

### Issue and Pull Request Labels

This section lists the labels we use to help us track and manage issues and pull requests.

| Label | Description |
|---|---|
| `api` | FastAPI endpoints |
| `bug` | Something is broken |
| `db` | Database models and migrations |
| `docs` | Documentation |
| `feat` | New feature or enhancement |
| `frontend` | React components and hooks |
| `infra` | Docker, CI/CD, deployment |
| `probe` | Scapy probe engine |
| `security` | Authentication, rate limiting, hardening |
| `test` | Unit, integration, or E2E tests |


### Recognition

Contributors will be recognized in the project's README and release notes.

### Where to Ask for Help?

If you have any questions or need help, please open an issue on GitHub or contact the maintainers directly.

---

Thank you for your interest in making Ping-Atlas better! 🚀