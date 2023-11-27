#!/bin/bash

# Test database
export DT_SQL_TESTUSER="<REPLACE_ME>"
export DT_SQL_TESTPASS="<REPLACE_ME>"
export DT_SQL_TESTHOST="<REPLACE_ME>"
export DT_SQL_TESTPORT="<REPLACE_ME>"
export DT_SQL_TESTDBNAME="<REPLACE_ME>"

# Dev database
export DT_SQL_USER="<REPLACE_ME>"
export DT_SQL_PASS="<REPLACE_ME>"
export DT_SQL_HOST="<REPLACE_ME>"
export DT_SQL_PORT="<REPLACE_ME>"
export DT_SQL_DBNAME="<REPLACE_ME>"

# Pulumi backend on Azure
export AZURE_STORAGE_KEY="<REPLACE_ME>"
export AZURE_STORAGE_ACCOUNT="<REPLACE_ME>"
export AZURE_KEYVAULT_AUTH_VIA_CLI="true"

# Secrets for the web servers
# DT_DEFAULT_USER_PASS must be set to be able to run the test suite.
export DT_DEFAULT_USER_PASS="<REPLACE_ME>"
export DT_FRONT_SECRET_KEY="<REPLACE_ME>"
export DT_JWT_SECRET_KEY="<REPLACE_ME>"
