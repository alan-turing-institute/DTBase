This folder holds all the code necessary for running various services as Azure
functions. The code here should be minimal in functionality, and should merely implement
the necessary glue bits to have an Azure function e.g. run a model or do ingress. The
actual model or ingress code should be in their respective folders.

To test the functions locally, run
```
func start
```
You'll need the Azure command line tools for that. You can install them with
```
brew tap azure/functions
brew install azure-functions-core-tools@4
```
