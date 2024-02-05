"""The main Pulumi deployment script."""
import hashlib
from typing import Any, List

import pulumi_azure_native.dbforpostgresql as postgresql
import pulumi_azure_native.insights as insights
import pulumi_azure_native.resources as resource
import pulumi_azure_native.storage as storage
import pulumi_azure_native.web as web
from pulumi import Config, Output, export

CONFIG = Config()

BACKEND_DOCKER_URL = "turingcropapp/dtbase-backend:main"
FRONTEND_DOCKER_URL = "turingcropapp/dtbase-frontend:main"
FUNCTIONS_DOCKER_URL = "turingcropapp/dtbase-functions:main"
RESOURCE_NAME_PREFIX = CONFIG.get("resource-name-prefix")
SQL_SERVER_USER = "dbadmin"
SQL_DB_NAME = "dtdb"
SQL_SERVER_PASSWORD = CONFIG.require("sql-server-password")
DEFAULT_USER_PASSWORD = CONFIG.require("default-user-password")
POSTGRES_ALLOWED_IPS = CONFIG.get("postgres-allowed-ips")
FRONTEND_SECRET_KEY = CONFIG.require("frontend-secret-key")
JWT_SECRET_KEY = CONFIG.require("jwt-secret-key")
assert RESOURCE_NAME_PREFIX is not None


def get_connection_string(account_name: str, resource_group_name: str) -> Output[str]:
    storage_account_keys = storage.list_storage_account_keys_output(
        account_name=account_name, resource_group_name=resource_group_name
    )
    primary_storage_key = storage_account_keys.keys[0].value
    connection_string = Output.format(
        "DefaultEndpointsProtocol=https;AccountName={0};AccountKey={1}",
        account_name,
        primary_storage_key,
    )
    return connection_string


def create_sql_server(resource_group: resource.ResourceGroup) -> postgresql.Server:
    sql_server_name = f"{RESOURCE_NAME_PREFIX}-postgresql"
    sql_server = postgresql.Server(
        sql_server_name,
        server_name=sql_server_name,
        resource_group_name=resource_group.name,
        administrator_login=SQL_SERVER_USER,
        administrator_login_password=SQL_SERVER_PASSWORD,
        create_mode="Default",
        storage=postgresql.StorageArgs(storage_size_gb=32),
        backup=postgresql.BackupArgs(
            backup_retention_days=14, geo_redundant_backup="Disabled"
        ),
        sku=postgresql.SkuArgs(tier="Burstable", name="Standard_B1ms"),
        availability_zone="1",
        version="16",
    )
    return sql_server


def create_pg_database(
    resource_group: resource.ResourceGroup, sql_server: postgresql.Server
) -> postgresql.Database:
    # TODO This is broken as of 2023-11-30. I'm not sure why, but I've raised an issue
    # on pulumi: https://github.com/pulumi/pulumi-azure-native/issues/2916
    # That this resource fails to get created doesn't interfere with anything else, so
    # one can run `pulumi up`, get all the other stuff going, and then manually go and
    # create a database called ${SQL_DB_NAME} on the PostgreSQL server.
    pg_database = postgresql.Database(
        f"{RESOURCE_NAME_PREFIX}-postgresql-db",
        charset="UTF8",
        collation="English_United States.1252",
        database_name=SQL_DB_NAME,
        resource_group_name=resource_group.name,
        server_name=sql_server.name,
    )
    return pg_database


def create_app_service_plan(
    resource_group: resource.ResourceGroup,
) -> web.AppServicePlan:
    app_service_plan = web.AppServicePlan(
        f"{RESOURCE_NAME_PREFIX}-web-asp",
        resource_group_name=resource_group.name,
        kind="Linux",
        reserved=True,
        sku=web.SkuDescriptionArgs(tier="Premium", name="P1v2"),
    )
    return app_service_plan


def create_app_insights(resource_group: resource.ResourceGroup) -> insights.Component:
    app_insights = insights.Component(
        f"{RESOURCE_NAME_PREFIX}-web-ai",
        application_type=insights.ApplicationType.WEB,
        kind="web",
        resource_group_name=resource_group.name,
        ingestion_mode=insights.IngestionMode.APPLICATION_INSIGHTS,
    )
    return app_insights


def create_storage_account(
    resource_group: resource.ResourceGroup,
) -> storage.StorageAccount:
    # Storage accounts can't have special characters in their names, hence no hyphen for
    # this one after the prefix.
    storage_account = storage.StorageAccount(
        f"{RESOURCE_NAME_PREFIX}sa",
        resource_group_name=resource_group.name,
        sku=storage.SkuArgs(name="Standard_LRS"),
        kind=storage.Kind.STORAGE_V2,
    )
    return storage_account


def create_backend_webapp(
    name: str | Output[str],
    resource_group: resource.ResourceGroup,
    app_service_plan: Any,
    sql_server: postgresql.Server,
    app_insights: insights.Component,
) -> web.WebApp:
    _sql_host = Output.format("{0}.postgres.database.azure.com", sql_server.name)
    webapp_settings = [
        web.NameValuePairArgs(name=name, value=value)
        for name, value in (
            ("APPINSIGHTS_INSTRUMENTATIONKEY", app_insights.instrumentation_key),
            (
                "APPLICATIONINSIGHTS_CONNECTION_STRING",
                app_insights.instrumentation_key.apply(
                    lambda key: "InstrumentationKey=" + key
                ),
            ),
            ("ApplicationInsightsAgent_EXTENSION_VERSION", "~2"),
            ("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false"),
            ("DOCKER_REGISTRY_SERVER_URL", "https://index.docker.io/v1"),
            ("DOCKER_ENABLE_CI", "true"),
            ("DT_SQL_HOST", _sql_host),
            ("DT_SQL_PASS", SQL_SERVER_PASSWORD),
            ("DT_SQL_PORT", "5432"),
            ("DT_SQL_USER", SQL_SERVER_USER),
            ("DT_SQL_DBNAME", SQL_DB_NAME),
            ("DT_DEFAULT_USER_PASS", f"{DEFAULT_USER_PASSWORD}"),
            ("DT_JWT_SECRET_KEY", JWT_SECRET_KEY),
            ("WEBSITES_PORT", "5000"),
        )
    ]
    webapp = web.WebApp(
        f"{RESOURCE_NAME_PREFIX}-{name}",
        resource_group_name=resource_group.name,
        server_farm_id=app_service_plan.id,
        site_config=web.SiteConfigArgs(
            app_settings=webapp_settings,
            always_on=True,
            linux_fx_version=f"DOCKER|{BACKEND_DOCKER_URL}",
        ),
        https_only=True,
        name=f"{RESOURCE_NAME_PREFIX}-{name}",
    )
    return webapp


def create_frontend_webapp(
    name: str | Output[str],
    resource_group: resource.ResourceGroup,
    app_service_plan: Any,
    app_insights: insights.Component,
    backend_url: str | Output[str],
) -> web.WebApp:
    webapp_settings = [
        web.NameValuePairArgs(name=name, value=value)
        for name, value in (
            ("APPINSIGHTS_INSTRUMENTATIONKEY", app_insights.instrumentation_key),
            (
                "APPLICATIONINSIGHTS_CONNECTION_STRING",
                app_insights.instrumentation_key.apply(
                    lambda key: "InstrumentationKey=" + key
                ),
            ),
            ("ApplicationInsightsAgent_EXTENSION_VERSION", "~2"),
            ("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false"),
            ("DOCKER_REGISTRY_SERVER_URL", "https://index.docker.io/v1"),
            ("DOCKER_ENABLE_CI", "true"),
            ("DT_BACKEND_URL", backend_url),
            ("DT_FRONT_SECRET_KEY", FRONTEND_SECRET_KEY),
            ("WEBSITES_PORT", "8000"),
        )
    ]
    webapp = web.WebApp(
        f"{RESOURCE_NAME_PREFIX}-{name}",
        resource_group_name=resource_group.name,
        server_farm_id=app_service_plan.id,
        site_config=web.SiteConfigArgs(
            app_settings=webapp_settings,
            always_on=True,
            linux_fx_version=f"DOCKER|{FRONTEND_DOCKER_URL}",
        ),
        https_only=True,
        name=f"{RESOURCE_NAME_PREFIX}-{name}",
    )
    return webapp


def create_function_app(
    name: str | Output[str],
    resource_group: resource.ResourceGroup,
    app_service_plan: Any,
    app_insights: insights.Component,
    sa_connection_string: str | Output[str],
    storage_account: storage.StorageAccount,
    backend_url: str | Output[str],
) -> web.WebApp:
    webapp_settings = [
        web.NameValuePairArgs(name=name, value=value)
        for name, value in (
            ("AzureWebJobsStorage", sa_connection_string),
            ("FUNCTIONS_EXTENSION_VERSION", "~4"),
            ("APPINSIGHTS_INSTRUMENTATIONKEY", app_insights.instrumentation_key),
            (
                "APPLICATIONINSIGHTS_CONNECTION_STRING",
                app_insights.instrumentation_key.apply(
                    lambda key: "InstrumentationKey=" + key
                ),
            ),
            ("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false"),
            ("DOCKER_REGISTRY_SERVER_URL", "https://index.docker.io/v1"),
            ("DOCKER_ENABLE_CI", "true"),
            ("DT_BACKEND_URL", backend_url),
            # TODO We should probably use a different user for the functions app.
            ("DT_DEFAULT_USER_PASS", f"{DEFAULT_USER_PASSWORD}"),
        )
    ]
    models_app = web.WebApp(
        f"{RESOURCE_NAME_PREFIX}-{name}",
        resource_group_name=resource_group.name,
        kind="functionapp",
        server_farm_id=app_service_plan.id,
        site_config=web.SiteConfigArgs(
            app_settings=webapp_settings,
            linux_fx_version=f"DOCKER|{FUNCTIONS_DOCKER_URL}",
            azure_storage_accounts=web.AzureStorageInfoValueArgs(
                account_name=storage_account.name,
                type=web.AzureStorageType.AZURE_FILES,
            ),
            # TODO This should be updated to only include the backend URL.
            cors={"allowed_origins": ["*"]},
        ),
        https_only=True,
    )
    return models_app


def create_postgres_firewall_rules(
    resource_group: resource.ResourceGroup,
    sql_server: postgresql.Server,
    ips_string: str,
    already_created: Any,
    num_hash_chars: int = 4,
) -> List[postgresql.FirewallRule]:
    """Given a list of comma separated IP addresses, create a firewall rule for the
    Postgres server to allow each one of them.

    We append a part of the IPs hash to the name, to create a unique name for the role.
    We use the hash rather than the actual IP to not reveal actual IPs in the resource
    names.
    """
    rules = []
    for ip in ips_string.split(","):
        if ip in already_created:
            # Don't try to create another rule for this same IP, if it comes up again.
            continue
        h = hashlib.sha256(bytes(ip, encoding="utf8")).hexdigest()[:num_hash_chars]
        rules.append(
            postgresql.FirewallRule(
                f"{RESOURCE_NAME_PREFIX}-fwr{h}",
                resource_group_name=resource_group.name,
                start_ip_address=ip,
                end_ip_address=ip,
                server_name=sql_server.name,
            )
        )
        already_created.append(ip)
    return rules


def main() -> None:
    resource_group = resource.ResourceGroup(f"{RESOURCE_NAME_PREFIX}-rg")
    sql_server = create_sql_server(resource_group)
    create_pg_database(resource_group, sql_server)
    app_service_plan = create_app_service_plan(resource_group)
    app_insights = create_app_insights(resource_group)
    storage_account = create_storage_account(resource_group)
    sa_connection_string = get_connection_string(
        storage_account.name, resource_group.name
    )
    backend = create_backend_webapp(
        "backend", resource_group, app_service_plan, sql_server, app_insights
    )

    # Create firewall rules for allowing traffic for the PostgreSQL server. Using apply
    # in this way explicitly breaks the Pulumi docs' warning that one shouldn't create
    # new resources within apply. However, this is also how some officially Pulumi
    # examples do it, and I don't know of another way. This means that `pulumi preview`
    # doesn't work correctly though, it might not show the firewall rules, but the
    # deployment does work out fine.
    firewall_ips = []
    backend.outbound_ip_addresses.apply(
        lambda x: create_postgres_firewall_rules(
            resource_group, sql_server, x, firewall_ips
        )
    )
    if POSTGRES_ALLOWED_IPS is not None:
        create_postgres_firewall_rules(
            resource_group, sql_server, POSTGRES_ALLOWED_IPS, firewall_ips
        )
    backend_url = backend.default_host_name.apply(
        lambda endpoint: "https://" + endpoint
    )
    export(
        "backend_endpoint",
        backend_url,
    )

    create_function_app(
        "functionapp",
        resource_group,
        app_service_plan,
        app_insights,
        sa_connection_string,
        storage_account,
        backend_url,
    )

    frontend = create_frontend_webapp(
        "frontend",
        resource_group,
        app_service_plan,
        app_insights,
        backend_url,
    )
    frontend_url = frontend.default_host_name.apply(
        lambda endpoint: "https://" + endpoint
    )
    export(
        "frontend_endpoint",
        frontend_url,
    )


if __name__ == "__main__":
    main()
