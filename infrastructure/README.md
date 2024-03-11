# DTBase Infrastructure as Code

DTBase has several semi-independent parts that talk to each other, as explained in the main README.md. While you can run all of them locally on a single machine, for a more "production" style deployment you may want to host them on a cloud platform. To deploy DTBase on the cloud, you could make the various resources manually: A PostgreSQL database, a couple of web servers for the frontend and the backend, etc. However, for convenience, maintainability, and reproducibility you should probably rather define the resources you need using an infrastructure-as-code (IaC) tool. That means writing a piece of code that defines the cloud resources that you need, various configuration options for them, and how they are connected, and letting the IaC tool then create these resources for you. If you want to change a configuration option, like increase you database disk allocation or add a firewall rule, you can do this in your configuration file and tell the IaC tool to update the cloud resources correspondingly.

This folder has our IaC configuration using a tool called Pulumi. Pulumi configuration files are written in Python, in this case in a file called `__main__.py`. Global Pulumi configuration is in `Pulumi.yaml`. For every deployed instance of DTBase managed by Pulumi, which Pulumi calls stacks, there is also a file called `Pulumi.name-of-stack-goes-here.yaml`, which holds configuration options for that stack. You may have multiple stacks for instance for a development and production deployment.

We would like to support multiple cloud platforms, but for historical reasons we currently only support Azure. Hopefully converting `__main__.py` to use e.g. AWS or GCloud instead should not be too hard.

## Set-up Steps

To get a Pulumi stack of DTBase up and running, these are the steps to follow.

0. Install Pulumi if you haven't yet. See https://www.pulumi.com/
1. Create an Azure storage account. This storage will only be used to hold Pulumi backend state data. If you have multiple stacks they can all use the same storage account.
2. Set `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_KEY` in `.secrets/dtenv.sh`. `AZURE_STORAGE_ACCOUNT` is the name of the storage account you created, `AZURE_STORAGE_KEY` can be found in the Access Keys of that account.  You also need to add the line `export AZURE_KEYVAULT_AUTH_VIA_CLI="true"` to `dtenv.sh` if its not there already.
3. Create a blob storage container within the storage account.
4. In a terminal run `source .secrets/dtenv.sh` and then `pulumi login azblob://<NAME OF STORAGE CONTAINER>`. Note that this affects your use of Pulumi system-wide, you'll have to login to a different backend to manage different projects.
5. Create an Azure Key Vault. This will hold an encryption key for Pulumi secrets. This, too, can be used by multiple Pulumi stacks.
6. In the key vault, create an RSA key (yes, it has to be RSA rather than ECDSA).
7. Give yourself Encrypt and Decrypt permissions on the key vault.

You are now ready to create a new stack. If you ever need to create a second stack, you will not need to repeat the above steps, only the ones below.

8. Create a new Pulumi stack with `pulumi stack init --secrets-provider="azurekeyvault://<NAME OF KEY VAULT>.vault.azure.net/keys/<NAME OF KEY>"`
9. Make sure you're in a Python virtual environment with Pulumi SDK installed (`pip install .[infrastructure]` should cover your needs).
10. Set all the necessary configurations with `pulumi config set` and `pulumi config set --secret`. You'll find these in `__main__.py`, or you can keep adding them until `pulumi up` stops complaining. Do make sure to use `--secret` for any configuration variables the values of which you are not willing to make public, such as passwords. You can make all of them `--secret` if you want to play safe, there's no harm in that. These values are written to `Pulumi.name-of-our-stack.yaml`, but if `--secret` is used they are encrypted with the key from your vault, and are unreadable gibberish to outsiders.
11. Run `pulumi up` to stand up your new Pulumi stack.
12. As of 2023-11-30, the creation of one resource, the PostgreSQL database, fails. This seems to be an issue with Pulumi, see comments in `__main__.create_pg_database`. Once all the other resources have been created with `pulumi up`, and it's only complaining about the database failing, you can manually login to the PostgreSQL server you've created and create the database yourself. You will then have a functioning deployment of DTBase. Hopefully soon this workaround won't be necessary.
13. Optionally, set up continuous deployment by selecting your WebApp in the Azure Portal, navigating to Deployment Center, and copying the generated Webhook URL; then, head to Docker Hub, select the container sude by the WebApp, create a new webhook using the copied URL. You need to do this for each of the three WebApps: The frontend, the backend, and the function app. This makes it such that every time a new version of the container is pushed to Docker Hub (by e.g. the GitHub Action) the web servers automatically pull and run the new version.
