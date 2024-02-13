# Guide to models in DTBase

This readme details how to write your own models in DTBase.

## BaseModel

The `BaseModel` class has all the general purpose tools for interacting with the backend (and TODO: Azure Functions). It inherits from `BaseService`.
For a custom models, the user should create their own custom DataModelClass inheriting from the `BaseModel` class.
For example:

```
class CustomDataModel(BaseModel):
    """
    Custom class inheriting from the BaseModel class for interacting with the OpenWeatherData API.
    """

    def __init__(self) -> None:
        super().__init__()
```

### Method: get_service_data

The user then needs to write a `get_service_data` method in the `CustomDataModel`. This method should create the model, predict on some data and return some predicted values.

```
def get_service_data():
    model = get_model()
    data = get_data()
    predictions = model.predict(data)
    return predictions
```

The structure of the data being returned by the function should be as follows:

```
[(endpoint, payload), (endpoint, payload), etc.]
```
For models, the endpoints that likely need to be returned are:

- /model/insert-model
- insert-model-scenario
- insert-model-measure
- /model/insert-model-run

TODO Provide a simple example
