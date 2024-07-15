import subprocess
import sys
import requests
import re
import os
from getpass import getpass

REPO_URL = "https://github.com/Detectronic-DN/FDV_Converter.git"
REPO_OWNER = "Detectronic-DN"
REPO_NAME = "FDV_Converter"


def validate_version(version):
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise ValueError("Version must be in the format X.Y.Z")


def create_release(version, github_token=None):
    try:
        validate_version(version)

        # Ensure we're on the master branch
        current_branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode()
            .strip()
        )
        if current_branch != "master":
            raise ValueError(f"Not on master branch. Current branch: {current_branch}")

        # Update version.txt
        with open("version.txt", "w") as f:
            f.write(version)

        # Commit version change
        subprocess.run(["git", "add", "version.txt"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Bump version to {version}"], check=True
        )

        # Create and push tag
        subprocess.run(
            ["git", "tag", "-a", f"v{version}", "-m", f"Version {version}"], check=True
        )
        subprocess.run(["git", "push", "origin", "master", "--tags"], check=True)

        print(f"Release v{version} created and pushed to GitHub.")

        if github_token:
            create_github_release(version, github_token)
        else:
            print_manual_release_instructions()

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while creating the release: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


def create_github_release(version, token):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "tag_name": f"v{version}",
        "target_commitish": "master",
        "name": f"Release {version}",
        "body": f"Release notes for version {version}",
        "draft": False,
        "prerelease": False,
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"GitHub release v{version} created successfully.")
    else:
        print(f"Failed to create GitHub release. Status code: {response.status_code}")
        print(f"Response: {response.text}")


def print_manual_release_instructions():
    print("Now, create a release on GitHub with the following steps:")
    print(f"1. Go to {REPO_URL}")
    print("2. Click on 'Releases' in the right sidebar")
    print("3. Click 'Draft a new release'")
    print("4. Choose the tag you just created")
    print("5. Set a title and write release notes")
    print("6. Click 'Publish release'")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_release.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    github_token = (
        os.environ.get("GITHUB_TOKEN")
        or getpass("Enter your GitHub token (or press Enter to skip): ").strip()
        or None
    )
    create_release(version, github_token)
