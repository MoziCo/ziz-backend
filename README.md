# Project Template

> A ready-to-go Python package template with Poetry, pre-commit, and Dev Container setup.

## Getting Started

Clone the template repository:

```bash
git clone https://github.com/your-org/python-pypi-template.git my-new-project
cd my-new-project
```

### Update Project Details

Replace placeholders in `pyproject.toml`:

```bash
PROJECT_NAME=my-new-project
DESCRIPTION="Short description of your project"
AUTHOR="Your Name <you@example.com>"

# Replace placeholders in pyproject.toml
sed -i "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" pyproject.toml
sed -i "s/{{DESCRIPTION}}/$DESCRIPTION/g" pyproject.toml
sed -i "s/{{AUTHOR}}/$AUTHOR/g" pyproject.toml
sed -i "s/{{PACKAGE_NAME}}/${PROJECT_NAME//-/_}/g" pyproject.toml

# Rename existing source package directory

Rename the existing folder `python_template` to match the new project name:

```bash
mv src/python_template "src/${PROJECT_NAME//-/_}"
```

### Install Dependencies

Initialize Poetry environment and sync:

```bash
poetry install
poetry sync
```

### Set Up Git and Pre-commit

Initialize Git and install pre-commit hooks:

```bash
git init
git add .
git commit -m "chore: initial commit"
pre-commit install
pre-commit run --all-files
```

### Start Dev Container (Visual Studio Code)

Open in VS Code and reopen in container:

```bash
code .
# then follow the prompt to reopen in container
```

## Usage

Describe how to run your CLI or import your library. For example:

```bash
poetry run my_cli --help
```

## Contributing

Contributions are welcome! Please submit issues and pull requests on GitHub.

## License

Distributed under the MIT License. See `LICENSE` for more information.
