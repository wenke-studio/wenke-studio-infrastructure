# Wenke Studio Infrastructure

## Requirements

- Python
    - [uv](https://github.com/astral-sh/uv)
- Pulumi CLI
    - [download and install](https://www.pulumi.com/docs/iac/download-install/)

## Quick Start

```bash
# install dependencies
$ pip install -r requirements.txt

# Pulumi login uses the `default` profile in `~/.aws/credentials`
$ pulumi login s3://wenke-studio-infrastructure

# change director to any entrypoint, for example:
$ cd wenke_studio

# list stacks
$ pulumi stack ls
NAME   LAST UPDATE   RESOURCE COUNT
root*  8 months ago  8
```

## Development

```bash
# update requirements.txt
$ uv pip freeze > requirements.txt
```
