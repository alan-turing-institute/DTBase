# DTBase Models

This folder hosts two general purpose timeseries forecasting models, ARIMA and HODMD. They work both as useful additions to many digital twins and as examples for how to implement a model that interfaces with DTBase.

Currently (as of 2024-03-08) this remains work in progress. ARIMA is fully functional, but it has some vestige in its code from a time when it was used for a more particular application, that needs to be cleaned up. HODMD is implemented as a model, but hasn't yet been integrated into DTBase using the `BaseModel` class.

The way to implement your own model is to use the `BaseModel` class as described below. We recommend also reading `dtbase/services/README.md`, since `BaseModel` is just an instance of `BaseService`, described there.

## BaseModel

The `BaseModel` class has all the tools for interacting with the DTBase backend. It inherits from `BaseService`. For a custom model, the user should create their own custom Model Class inheriting from the `BaseModel` class. For example:

```
class CustomModel(BaseModel):
    """
    Custom model inheriting from the BaseModel class.
    """
```

### Method: `get_service_data`

The user then needs to write a `get_service_data` method in `CustomModel`. This method should run the model return the outputs in a particular format, which `BaseModel` will then submit to the the DTBase backend. This might look something like

```
    def get_service_data(some_data):
        model = get_model()
        some_more_data = get_data()
        predictions = model.predict(some_data, some_more_data)
        return predictions
```

The structure of, `predictions`, i.e. the data being returned by `get_service_data`, should be as follows:

```
[(endpoint, payload), (endpoint, payload), etc.]
```
Here `endpoint` is a string that is the name of a DTBase API endpoint, and `payload` is a dictionary or a list that is the payload that that endpoint expects. For models, the endpoints that likely need to be returned are:

- `/model/insert-model`
- `/model/insert-model-scenario`
- `/model/insert-model-measure`
- `/model/insert-model-run`

The model can then be called like this:

```
cm = CustomModel()
cm(
    some_data=my_favourite_data,
    dt_user_email=blahblah@email.com,
    dt_user_password="this is a very bad password",
)
```

The `dt_user_email` and `dt_user_password` arguments are for user credentials that can be used to log into the DTBase backend. Any other keyword arguments, like in this case `some_data`, are passed onto the `get_service_data` function. Note that these have to be passed as keyword arguments, positional ones won't work.

Even though calls to endpoints like `insert-model` and `insert-model-measure` only need to be run once, it is safe to make every run of the model call those endpoints. If the model/measure/scenario already exists in the database the backend will just ignore the attempt to write a duplicate, and return a 409 status code, which `BaseModel` handles for you.
