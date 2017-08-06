import pickle


# 1. We define a model
class Model():

    def __init__(self, data):
        self.data = data

    def train(self):
        self.data  # access the data to train the mode

# 2. We create and train a model instance
model = Model(['i', 'am', 'the', 'data'])

# 3. We save the model instance
serialized_model = pickle.dumps(model)


# 4. We update the model, due to a bug and release a patch
class Model():

    def __init__(self, training_data):
        self.training_data = training_data

    def train(self):
        self.trainign_data  # access the data to train the mode

# 5. In production we load in a model from s3
model = pickle.loads(serialized_model)

# 6. And when we access the attribute model_cls
model.train()
