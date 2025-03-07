import os
import shutil
import subprocess

def check_unsaved_changes():
    """Check if there are uncommitted Git changes."""
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.stdout.strip():
        confirm = input(cyan("You have unsaved changes in the repository. Do you want to continue? (y/n): ")).strip().lower()
        return confirm == "y"
    return True

def ask_user_input(prompt, default=None):
    """Ask for user input with a default value."""
    user_input = input(cyan(f"{prompt} [{default}]: ")).strip()
    return user_input if user_input else default

def generate_keys():
    """Run the private key generation script and capture its output."""
    result = subprocess.run(["python", "./scripts/generate_private_key.py"], capture_output=True, text=True)
    output_lines = result.stdout.split("\n")
    
    private_key = None
    public_key = None
    for line in output_lines:
        if line.startswith("AGENT_PRIVATE_KEY ="):
            private_key = line.split(" = ")[1].strip()
        elif line.startswith("Corresponding public key:"):
            public_key = line.split(": ")[1].strip()

    if private_key is None:
        raise ValueError("Failed to extract the private key from generate_private_key.py output")
    
    if public_key is None:
        raise ValueError("Failed to extract the public key from generate_private_key.py output")

    print(green("Key pair generated successfully!"))
    print(bold(cyan(f"Private key: {private_key}")))
    print(bold(cyan(f"Public key: {public_key}")))

    return private_key, public_key

def give_executable_permissions(file_path):
    os.chmod(file_path, 0o755)

def find_project_root():
    """Find the project root by searching for pyproject.toml."""
    current_dir = os.getcwd()
    while not os.path.exists(os.path.join(current_dir, "pyproject.toml")):
        current_dir = os.path.dirname(current_dir)
    return current_dir
def bold(text):
    # ANSI escape code for bold text
    BOLD = '\033[1m'
    RESET = '\033[0m'
    return f"{BOLD}{text}{RESET}"

def green(text):
    # ANSI escape code for green text
    GREEN = '\033[1;32m'  # Green text (you can modify it to non-bold green if needed)
    RESET = '\033[0m'
    return f"{GREEN}{text}{RESET}"

def blue(text):
    # ANSI escape code for blue text
    BLUE = '\033[1;34m'  # Blue text
    RESET = '\033[0m'
    return f"{BLUE}{text}{RESET}"

def red(text):
    # ANSI escape code for red text
    RED = '\033[1;31m'  # Red text
    RESET = '\033[0m'
    return f"{RED}{text}{RESET}"

def dark_grey(text):
    # ANSI escape code for dark grey text
    DARK_GREY = '\033[1;30m'  # Dark grey text
    RESET = '\033[0m'
    return f"{DARK_GREY}{text}{RESET}"

def cyan(text):
    # ANSI escape code for light grey text
    CYAN = '\033[0;36m'  # Light grey text
    RESET = '\033[0m'
    return f"{CYAN}{text}{RESET}"


def run_setup():
    print(bold(blue("Welcome to the Theoriq Agent Setup Script!")))
    print(dark_grey("This script will help you create a new agent project with the Theoriq SDK."))
    print(bold(dark_grey("Let's get started!")))

    print("\n\n\n")
    if not check_unsaved_changes():
        print(bold(red("Aborted due to unsaved changes.")))
        return

    project_name = ask_user_input("Enter project name", "my_agent")
    if not project_name:
        print(bold(red("Project name cannot be empty.")))
        return

    source_dir = "./examples/hello_world_agent"
    target_dir = f"./{project_name}"
    
    try:
        print(dark_grey(f"Copying {source_dir} to {target_dir}..."))
        shutil.copytree(source_dir, target_dir)
    except Exception as e:
        print(bold(red(f"Error copying {source_dir} to {target_dir}: {e}")))
        return

    print(dark_grey("Generating key pair..."))
    private_key, public_key = generate_keys()


    theoriq_uri = ask_user_input("Enter Theoriq URI", "https://theoriq-backend.prod-02.chainml.net")
    # check if the uri is a valid url
    if not theoriq_uri.startswith("https://"):
        print(bold(red("Theoriq URI must be a valid URL.")))
        return
    
    flask_port = ask_user_input("Enter Flask port", "3000")
    # check if the port is a number
    if not flask_port.isdigit():
        print(bold(red("Flask port must be a number.")))
        return
    
    env_path = os.path.join(target_dir, ".env")
    env_example_path = os.path.join(target_dir, ".env.example")
    
    if os.path.exists(env_example_path):
        os.rename(env_example_path, env_path)
    
    with open(env_path, "r") as file:
        env_content = file.read()
    
    env_content = env_content.replace("AGENT_PRIVATE_KEY = CHANGE_ME", f"AGENT_PRIVATE_KEY = {private_key}")
    env_content = env_content.replace("FLASK_PORT = 8000", f"FLASK_PORT = {flask_port}")
    env_content = env_content.replace("THEORIQ_URI = CHANGE_ME", f"THEORIQ_URI = {theoriq_uri}")

    with open(env_path, "w") as file:
        file.write(env_content)
        

    print(bold(green("\nSetup complete! Summary:")))
    print(bold(dark_grey(f"- Project created at: {target_dir}")))
    print(bold(dark_grey(f"- Private key saved in: {env_path}")))
    print(bold(dark_grey(f"- Public key saved in: {public_key}")))
    print(bold(dark_grey(f"- Theoriq URI: {theoriq_uri}")))
    print(bold(dark_grey(f"- Flask Port: {flask_port}")))


    # Give executable permissions to the run.sh script
    run_script_path = os.path.join(target_dir, "scripts", "run.sh")
    give_executable_permissions(run_script_path)
    print(dark_grey(f"Executable permissions granted to {run_script_path}"))

    # Give executable permissions to the install.sh script
    install_script_path = os.path.join(target_dir, "scripts", "install.sh")
    give_executable_permissions(install_script_path)
    print(dark_grey(f"Executable permissions granted to {install_script_path}"))
    
    # Print the command to install the agent
    print(green("\nTo install the agent, use the following commands:"))
    print(f"cd {os.getcwd()}/{target_dir}")
    print(f"./scripts/install.sh")

    # Print the command to run the agent
    print(green("\nTo run your agent, use the following commands:"))
    print(f"cd {os.getcwd()}/{target_dir}")
    print(f"./scripts/run.sh")

    # Going back to the original directory



def main():
        # Find the project root by searching for pyproject.toml
    project_root = find_project_root()
    print(dark_grey(f"Project root: {project_root}"))

    current_dir = os.getcwd()
    # Check if the project root is the current directory
    if project_root != current_dir:
        print(dark_grey("Changing directory to project root..."))
        os.chdir(project_root)

    run_setup()

    # Going back to the original directory
    if current_dir != os.getcwd():
        print(dark_grey("Changing directory back to original directory..."))
        os.chdir(current_dir)

if __name__ == "__main__":
    main()
