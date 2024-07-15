import PyInstaller.__main__
import os


def build_exe():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to your main script
    main_script = os.path.join(script_dir, "src", "UI", "main.py")

    # Path to your version file
    version_file = os.path.join(script_dir, "version.txt")

    # Read the version
    with open(version_file, "r") as f:
        version = f.read().strip()

    PyInstaller.__main__.run(
        [
            main_script,
            "--name=FDV_Converter",
            "--onefile",
            "--windowed",
            f"--add-data={version_file};.",
            f"--version-file={version_file}",
            "--clean",
            "--noconfirm",
        ]
    )

    print(f"Executable built successfully. Version: {version}")


if __name__ == "__main__":
    build_exe()
