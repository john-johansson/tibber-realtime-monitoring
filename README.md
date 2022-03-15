# Tibber Realtime Monitoring (in OKD)

This project give you the tools to create a simple application in OKD that visualize your power consumption and costs if you have tibber and an electricy meter with tibber pulse.

This project intention is to showcase different OKD features. It not to be seen as a best practice for developing or deploying cloud native applications. 

## Architecture 
Look in the main branch for reference.

The main application is a python script that communicates with the tibber api and writes its data influxdb time series database. Additional python scripts run as cron jobs. These cronjobs fetch cost and weather data from the tibber and weathermap API.This data is also written to influxdb. Grafana is used for visualizing.

All components run on a single machine. Docker is used for infouxdb and grafana. The python scripts are dependent on hardcoded uniqe values, such as access tokens and location data.

## Refactoring with OKD

All resources are configured in a specific project (namespace)

Create the project in OKD:

`oc new-project openinfra`

Openstack specific: Create a storage class that use cinder for persistent storage

`oc create -f manifests/sc.yaml`

### influxdb
Influxdb is deployed from the official container image in docker hub with the oc new-app command, which create a deployment. Variables to initiate the automated setup are provided in accordance with the official [documentation](https://hub.docker.com/_/influxdb).

```
oc new-app influxdb:latest -e DOCKER_INFLUXDB_INIT_MODE=setup -e DOCKER_INFLUXDB_INIT_USERNAME=tibber  -e DOCKER_INFLUXDB_INIT_PASSWORD=tibber123 -e DOCKER_INFLUXDB_INIT_ORG=tibber -e DOCKER_INFLUXDB_INIT_BUCKET=tibber -n openinfra
```

Optional: Create pvc:s for persisting the influxdb's data
```
oc create -f manifests/influxdb-pvc.yaml -n openinfra
oc patch deploy influxdb -n openinfra --patch-file manifests/influxdb-patch.js
```
### tibber application
Create the configmap and secret.

You will need an acces token for tibber and openweathremap:

- You can get your token from tibber [here](https://developer.tibber.com/)
- you can get a token for openweathermap [here](https://openweathermap.org/)

You can get the acccess token from influxdb from the influxdb pod:<br>
`oc exec $(oc get pods -o name | grep influxdb) -- influx auth list --user tibber --hide-headers  | cut -f 3)`

Replace the changeme value in the tibber-secret manifest to contain your access tokens.

Create the resources
```
oc apply -f manifests/tibber-configmap.yaml -n openinfra
oc apply -f manifests/tibber-secret.yaml -n openinfra
```

Update your tibber application with the values from the configmap and secret:
```
oc set env deploy tibber --from secret/tibber-secret -n openinfra
oc set env deploy tibber --from configmap/tibber-config -n openinfra
```
### tibber cronjobs
You need to create container images for the python code that should run as a kubernetes cronjob. This is also done with the tools available to you in OKD.

```
oc new-build python:3.9-ubi8~https://github.com/garnser/tibber-realtime-monitoring.git#openshift --name currentprice --context-dir python-apps/currentprice
oc new-build python:3.9-ubi8~https://github.com/garnser/tibber-realtime-monitoring.git#openshift --name weather --context-dir python-apps/weather
```

You can track the process and output from the build by looking in the buildconfig log. For example the weather application build can be tracked with the command òc logs -f bc/weather -n openinfra`

When the build is complete. It pushes the container image to the openshift registry. You should se your container images by executing `oc get is -n openinfra`

Update the image value in the cronjob manifest with the values from the output oc `oc get is -n openinfra`

```yaml
...
            image: changeme
...
```
to
```yaml
            image: image-registry.openshift-image-registry.svc:5000/openinfra/weather
```
and 
```yaml
            image: image-registry.openshift-image-registry.svc:5000/openinfra/currentprice
```

Create the cronjob by applying the manifests

```
oc apply -f manifests/currentprice-cronjob.yaml -n openinfra
oc apply -f manifests/weather-cronjob.yaml -n openinfra
```

### grafana
grafana is installed using the grafana operator. You need to install the operator from the operatorhub. In the administrator console, navigate to Operators -> OperatorHub and search for "grafana". Install the operator to the opeinfra namespace.

When the operator has finished installing. Create the grafana resources, Grafana, GrafanaDataSource and grafana Dashboard by applying the manifests.

First, verify successfull installation of the operator:

`oc get csv -n openinfra | grep grafana`

It should return an output similar to:<br>
`grafana-operator.v4.2.0            Grafana Operator   4.2.0     grafana-operator.v4.1.1            Succeeded`

Once succeded, create the resources
```
oc create -f manifests/tibber-grafanas.yaml -n openinfra
oc create -f manifests/tibber-grafanadatasources.yaml -n openinfra
oc create -f manifests/tibber-grafanadashboard.yaml -n openinfra
```
Get the external route for your application

`oc get route grafana-route -o jsonpath='{.status.ingress[].host}'`

Use a web broser to access it and view your consumption and cost data.
