# DTBase Functions

DTBase supports services as any callable API endpoints that send data to the backend when called. These services do not need to be hosted as part of the same deployment as the database, backend, and frontend of DTBase. However, when implementing your own services, it is often handy to be able to host them as part of the same deployment. For that, we use Azure Functions, Azure's concept for serverless compute that runs on demand and releases resources once it's done running. We recommend reading a bit about Azure Functions before trying to understand this code in detail.

This folder holds all the code necessary for running various services as Azure functions. The code here should be minimal in functionality, and should merely implement the necessary glue bits to have an Azure function e.g. run a model or do ingress. The actual model or ingress code should be in their respective folders.

To test the functions locally, run
```
func start
```

You'll need the Azure command line tools for that. You can install them with
```
brew tap azure/functions
brew install azure-functions-core-tools@4
```

## Examples

Currently there are two example functions in this folder: Arima and weather ingress. You can see how their `__init__.py` files handle interfacing with Azure and base your code on their examples. Any folder under `dtbase/functions` with a `function.json` file will be recognised as an Azure function and included in the Docker container built by the GitHub Action.
