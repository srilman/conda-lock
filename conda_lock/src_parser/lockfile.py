import pathlib

from textwrap import dedent

import yaml

from . import Lockfile


def parse_conda_lock_file(
    path: pathlib.Path,
) -> Lockfile:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")

    with path.open() as f:
        content = yaml.safe_load(f)
    version = content.pop("version", None)
    if not (isinstance(version, int) and version <= Lockfile.version):
        raise ValueError(f"{path} has unknown version {version}")

    return Lockfile(**content)


def write_conda_lock_file(
    content: Lockfile, path: pathlib.Path, include_help_text: bool = True
) -> None:
    with path.open("w") as f:
        if include_help_text:
            categories = set(p.category for p in content.package)

            def write_section(text: str) -> None:
                lines = dedent(text).split("\n")
                for idx, line in enumerate(lines):
                    if (idx == 0 or idx == len(lines) - 1) and len(line) == 0:
                        continue
                    print(("# " + line).rstrip(), file=f)

            write_section(
                f"""
                This lock file was generated by conda-lock (https://github.com/conda-incubator/conda-lock). DO NOT EDIT!

                A "lock file" contains a concrete list of package versions (with checksums) to be installed. Unlike
                e.g. `conda env create`, the resulting environment will not change as new package versions become
                available, unless you explicitly update the lock file.

                Install this environment as "YOURENV" with:
                    conda-lock install -n YOURENV --file {path.name}
                """
            )
            if "dev" in categories:
                write_section(
                    f"""
                    This lock contains optional development dependencies. Include them in the installed environment with:
                        conda-lock install --dev-dependencies -n YOURENV --file {path.name}
                    """
                )
            extras = sorted(categories.difference({"main", "dev"}))
            if extras:
                write_section(
                    f"""
                    This lock contains optional dependency categories {', '.join(extras)}. Include them in the installed environment with:
                        conda-lock install {' '.join('-e '+extra for extra in extras)} -n YOURENV --file {path.name}
                    """
                )
            write_section(
                f"""
                To update a single package to the latest version compatible with the version constraints in the source:
                    conda-lock lock --lockfile {path.name} --update PACKAGE
                To re-solve the entire environment, e.g. after changing a version constraint in the source file:
                    conda-lock {' '.join('-f '+path for path in content.metadata.sources)} --lockfile {path.name}
                """
            )

        yaml.dump(
            {
                "version": Lockfile.version,
                **content.dict(by_alias=True, exclude_unset=True),
            },
            f,
        )
