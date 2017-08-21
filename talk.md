name: inverse
layout: true
class: center, middle, inverse

---
# Predictive services
## From data to production
<br>

Jonas Brunsgaard & Helge Munk Jakobsen   
.small[jonas.brunsgaard@visma.com]   
.small[helge.munk.jacobsen@visma.com]

September 4th, 2017 — PUDD   

.small[https://github.com/brunsgaard/berlin-talk-2017]   

---

layout: false

# Agenda

* Our team and our mission

* PART1: From **DATA** to **PREDICTION**

* PART2: From **PREDICTION** to **PRODUCTION**


---

# About us

* The Visma Machine Learning Team
* Located in Copenhagen (e-conomic office)
* Team headcount: 4
* Main focus: AutoSuggest

#### Helge Munk Jakobsen

* Interested in data and predictive modelling

#### Jonas Brunsgaard

* Interested in software arhitecture, elegant code and best practices
* Designing and building an upcomming end-to-end data science platform

---

template: inverse

# From **DATA** to **PREDICTION**

a gentle introduction to building predictive models aimed at developers

---

# Intro

Data -> Magic -> Prediction

---

# Intro

Data -> ~~Magic~~ Math + Code -> Prediction

---

# Hands on exercise

* **Goal:** Build account suggestion service

* **Example:** For "Taxi to conference" -> Travel expense account (maybe)

* No hardcoded rules

<br>.center[![:scale 65%](img/hands-on-exercise.png)]

---

# The big picture

* Supervised learning (predictions)

* Classification

* One single type of model

<br>.center[![:scale 65%](img/the-big-picture.png)]


---

layout: false

template: inverse

# Let's code!

---

layout: false

template: inverse

# From **PREDICTION**
# to **PRODUCTION**

---

# Let's get started
We could write a simple API endpoint that loads in data and trains the model.
There after we should be ready to serve requests
<br><br>.center[![:scale 50%](img/the-naive-approach-1.svg)]<br>

```python
import api

app = api.create(name='Berlin')

@app.route('/predict', method=['POST'])
def predict(request):
    model = Model()
    training_data = db.get_all_observed_events()
    model.train(training_data)
    return model.predict(request.json)

app.run()
```

---

# What could possible to wrong


```python
import api

app = api.create(name='Berlin')

@app.route('/predict', method=['POST'])
def predict(request):
    model = Model()  # Naive Bayes is O(n)
    training_data = db.get_all_observed_events()
    model.train(training_data)
    return model.predict(request.json)

app.run()
```

 * Data availability - .small[we assume the data is available]
 * Data selection and preprocessing - .small[we select all the data and assume it is preprocessed]
 * Model training - .small[might take long time depending on the model and the data]
 * Resouce contraints - .small[CPU time and Memory]

All in all this is just not a great solution!

---

# So, what is needed?

To build a __continuously updated prediction api__ we need:

--

* Data integration
  * _Extract_ data from the original data sources.
  * _Transform_ data into a _prepared dataset_
  * _Load_ the _prepared dataset_ into our data warehouse

.credit[See more https://en.wikipedia.org/wiki/Extract,_transform,_load]
 <!---
 Function consumer data to prepared data
 pr aggrement
--->

--

* Continuous model building
  * _Re-train_ models triggered on events
  * _Testing_ if the new model is sane
  * _Resource consumption_ should be monitored 
  * _Serialization_ and dezerialization ('environments must be identical')

---

# So, what is needed?

--

* Api package
  * Authentication
  * Schema validation
  * Model loading ('Environment mismatch')
  * Logging
  * Metrics
  * Packaging


--

* Operations platform
  * Codified provisioning
  * High availability
  * Zero downtime releases
  * Scalability
  * ...

---

# Continuous is the keyword

So what we need is a pipeline, that lets us train new models at will and
redeploy to production multiple times a day.

To sum it up we need three components

* Datastore - will make _prepared datasets_ available
* CI/Scheduler - will train models continously
* Api - will map REST call to the models

<br>.center[![:scale 70%](img/components.svg)]

Also we need an operations solution to make sure the whole service is available

---

layout: false

template: inverse

# Getting data into the system

---

# The process of ETL

Extract, transform, load...

<br>.center[![:scale 70%](img/ETL.png)]


---

# Prepared datasets

We create a _prepared dataset_ per client/model/agreement, e.g.

.small[`e-conomic/smartscan/agreement552343`]

The datasets might at this point hold certain properties if needed

 * Entries are sorted by time stamp
 * Duplicates are removed
 * Text have been normalized
 * Maximum number of entries

Importing a dataset is now easy and can look like this.

```python
import datastore

# Fetching a dataset that are already prepared for the model
data = datastore.get('e-conomic/smartscan/agreement552343')
```

Prepared datasets are updated as frequently as the client needs.

 <!---
What does the properties give us
 - Resource limits
 - Transfer speed assertions
 - Model training time assertions
--->

---

layout: false

template: inverse

# Training models

---

# Training Models

Depending on the model type, training might happen before or during call time.

* _User_ - small models are trained on _call time_ with a _prepared dataset_
* _Domain_ - bigger models are _pre-trained_ with a collection of _prepared datasets_
* _Mix_ - some domain models are modified with a _prepared dataset_ on _call time_


--
<br>
__We will only look at _Domain_ models__

--

<br>

We use containers to ensure that the environment is fixed.

---

# Training Models

<br>.center[![:scale 70%](img/containers-to-the-rescue.png)]


---

# Training Models

* The container image holds the api code, the trained\_models and all the
dependencies. 
* We build on container images on the CI and store the images on
azure container registry


<br>.center[![:scale 65%](img/a-container-based-approach-1.svg)]<br>


---

# Dockerfile

A `Dockerfile` is used to describe how an image is build

.small[
```Dockerfile
FROM visma/machinelearning:1.0.4                       # base image with c/c++ deps

RUN pip install vml-model-smartscan        # install deps
RUN pip install vml-model-api              # install deps

RUN python train_models.py                 # train and serialize models 
RUN py.test --pyargs .                     # test the model and sanity

ENTRYPOINT ["python -m vml-api"]           # run the application
```
]

Then save it to the registry

.small[
```bash
~ docker push vml.azurecr.io/model-smartscan:v2-1499177682
```
]


---

layout: false

template: inverse

# Container orchestration
In kubernetes we trust

---

# What is kubernetes

.center[![:scale 100%](img/what-is-kubernetes-1.png)]

--

.center[![:scale 100%](img/what-is-kubernetes-2.png)]


---


# Kubernetes

An example of a kuberentes configuration

.small[
```yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: smartscan-model
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: smartscan-model
      - image: vml.azurecr.io/model-smartscan:v2-1499177682
        resources:
          requests:
            memory: "512Mi"
          limits:
            memory: "1024Mi"
        env:
        - name: AWS_CREDENTIALS
          valueFrom:
            secretKeyRef:
              name: smartscan-model-secrets
              key: aws_credentials
        ports:
        - containerPort: 80
```
]

---

# Putting it all together

We have a datastore with _prepared datasets_ and a CI is building new images over time
<br>.center[![:scale 35%](img/a-container-based-approach-2.svg)]<br>
The CI will tell Kubernetes to replace the containers, as soon as new images
are available

.center[![:scale 90%](img/a-container-based-approach-3.svg)]

---

## Docker and Kubernetes gave me

* Agile application creation and deployment
* Environmental consistency
* Dependency isolation
* Rolling updates
* Scaling thought in
* State configuration of services
* Dev and Ops separation of concerns
---

##Deploying to Kubernetes from notebook

Gazelle is a small tool we are working on that will let data scientists spin up
prediction endpoints from a jupyter notebook.

It works by serializing the model and sending it to a server that puts it into
a conatiner uploads the image and notifies kubernets about the the new endpoint

Lets us try it to get Helges models up and running.

---

template: inverse

# Thanks!
