## Set-up steps

0. Install Pulumi if you haven't yet. See https://www.pulumi.com/
1. Create an Azure storage account. This storage will only be used to hold Pulumi backend state data.
2. Set `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_KEY` in `.secrets/dtenv.sh`. `AZURE_STORAGE_ACCOUNT` is the name of the storage account you created, `AZURE_STORAGE_KEY` can be found in the Access Keys of that account.  You also need to add the line
`export AZURE_KEYVAULT_AUTH_VIA_CLI="true"`.
3. Create a blob storage container within the storage account.
4. In a terminal run `source .secrets/dtenv.sh` and then `pulumi login azblob://<NAME OF STORAGE CONTAINER>`. Note that this affects your use of pulumi system-wide, you'll have to login to a different backend to manage different projects.
5. Create an Azure Key Vault. This will hold an encryption key for Pulumi secrets.
6. In the key vault, create an RSA key (yes, needs to be RSA rather than ECDSA).
7. Give yourself Encrypt and Decrypt permissions on the key vault.
9. Create a new Pulumi stack with `pulumi stack init --secrets-provider="azurekeyvault://<NAME OF KEY VAULT>.vault.azure.net/keys/<NAME OF KEY>"`
10. Make sure you're in a Python virtual environment with Pulumi SDK installed (`pip install .[infrastructure]` should cover your needs).
11. Set all the necessary configurations with `pulumi config set` and `pulumi config set --secret`. You'll find these in `__main__.py`, or you can keep adding them until `pulumi up` stops complaining.
12. Run `pulumi up` to stand up your new Pulumi stack.
13. As of 2023-11-30, the creation of one resource, the PostgreSQL database, fails. This
    seems to be an issue with Pulumi, see comments in `__main__.create_pg_database`.
    Once all the other resources have been created with `pulumi up`, and it's only
    complaining about the database failing, you can manually login to the PostgreSQL
    server you've created and create the database yourself. You will then have a
    functioning deployment of DTBase. Hopefully soon this workaround won't be necessary.
14. Set up continuous deployment by selecting your WebApp in the Azure Portal, navigating to Deployment Center, enabling continuous deployment under Container Registry, adding the image name, and copying the generated Webhook URL; then, head to DockerHub, select the linked container, create a new webhook using the copied URL, and repeat for each WebApp.
