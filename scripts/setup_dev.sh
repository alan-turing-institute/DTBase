ENV_NAME="dt_env"

# Function to check and activate Conda environment
check_activate_conda() {
    if conda env list | grep "${ENV_NAME}" > /dev/null 2>&1; then
        echo "Activating Conda environment: ${ENV_NAME}"
        source activate "${ENV_NAME}"
        return 0
    else
        return 1
    fi
}

# Function to check for Poetry environment
check_activate_poetry() {
    if poetry env list | grep "${ENV_NAME}" > /dev/null 2>&1; then
        echo "Activating Poetry environment: ${ENV_NAME}"
        poetry shell
        return 0
    else
        return 1
    fi
}

# Function to check and activate PyEnv environment
check_activate_pyenv() {
    if pyenv versions | grep "${ENV_NAME}" > /dev/null 2>&1; then
        echo "Activating PyEnv environment: ${ENV_NAME}"
        pyenv activate "${ENV_NAME}"
        return 0
    else
        return 1
    fi
}

# Check for environment management systems in the order of preference
if ! { conda --version &>/dev/null && check_activate_conda; } &&
   ! { type poetry &>/dev/null && check_activate_poetry; } &&
   ! { type pyenv &>/dev/null && check_activate_pyenv; } &&
   [[ -z "$VIRTUAL_ENV" ]]; then
    echo "No suitable Python environment management system is installed or the ${ENV_NAME} environment does not exist."
fi

# The following commands run regardless of the DT_ENV variable's value, assuming that
# necessary services and dependencies are already set up when DT_ENV="development"

# Run tests
python -m pytest

# Start the backend API
(cd backend && DT_CONFIG_MODE=Debug ./run_localdb.sh) &

# Start the frontend
(cd webapp && npm install && FLASK_DEBUG=true DT_CONFIG_MODE=Auto-login ./run.sh) &

echo "DTBase setup complete. Backend running on http://localhost:5000, frontend on http://localhost:8000."
