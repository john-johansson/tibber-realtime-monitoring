# Tibber Real-time Monitoring (running on OKD)
This project aims to give insight on how to create a simple application that visualizes your power consumption (and costs if you have tibber).  To run this application you need a modern electricity meter with a tibber pulse plugged into it.
**Disclaimer:** This project's intention is to showcase OKD features. It's not to be seen as a best practice for developing or deploying cloud-native applications.

## Architecture (orginal single node/docker deployment)
The original application (which can be found in the main branch) is a python script that communicates with the tibber API and writes its data to an influxdb time-series database. In addition to the tibber-realtime-monitor application, thee are two python scripts that run as cron jobs. These cronjobs fetch cost and weather data from the tibber and OpenWeatherMap API. InfluxDB is used as a data source to grafana and the collected data is visualized in a grafana dashboard.
All components run on a single machine. Docker is used for influxdb and grafana. The python scripts are dependent on hard-coded unique values, such as access tokens and location data.

## Task: Refactor to run in Kubernetes with help of OKD
All resources are configured to run in a specific project (namespace)
Create the project (namespace) in OKD:
```
oc new-project openinfra
 ```

If you run OpenStack with cinder and want persistent data, you can create a storage class that uses cinder for persistent storage:
```
oc create -f manifests/sc.yaml
 ```

### influxdb
Influxdb is deployed from the official container image available at dockerhub.io. Variables to initiate the automated setup are provided following the official documentation.
When you use the oc new-app command to create an application, it will also create all necessary Kubernetes resources to make in an application!
```
oc new-app influxdb:latest -e DOCKER_INFLUXDB_INIT_MODE=setup -e DOCKER_INFLUXDB_INIT_USERNAME=tibber -e DOCKER_INFLUXDB_INIT_PASSWORD=$(pwgen -c 16 -n 1) -e DOCKER_INFLUXDB_INIT_ORG=tibber -e DOCKER_INFLUXDB_INIT_BUCKET=tibber
 ```
Optionally, create PVC:s for persisting the influxdb's data:
```
oc create -f manifests/influxdb-pvc.yaml -n openinfra
oc patch deploy influxdb --type merge --patch-file manifests/influxdb-patch.js
 ```

**Note:** Once influxdb is running. You can extract its credentials with the following commands:
influxdb password:
```
oc exec $(oc get pods -o=jsonpath='{.items[0].metadata.name}' | grep influxdb) -- env |  grep DOCKER_INFLUXDB_INIT_PASSWORD| cut -f2 -d =
 ```
inlfuxdb api token:
```
oc exec $(oc get pods -o=jsonpath='{.items[0].metadata.name}' | grep influxdb) -- influx auth list --user tibber --hide-headers  | cut -f 3
 ```

### tibber real-time monitoring application
Create the configmap and secret.
You will need an access token for tibber and OpenWeatherMap:
- You can get your tibber access token [here](https://developer.tibber.com/settings/accesstoken)
- you can get a token for openweathermap [here](https://openweathermap.org/)

You can get the access token from influxdb from the influxdb pod:
```
oc exec $(oc get pods -o name | grep influxdb) -- influx auth list --user tibber --hide-headers | cut -f 3)
```
Replace the `changeme` value in the tibber-secret manifest so it contains your access tokens.
Create the resources:
```
oc apply -f manifests/tibber-configmap.yaml
oc apply -f manifests/tibber-secret.yaml
 ```
Build the container image and deploy the application:
```
oc new-app --name tibber --labels=app=tibber python:3.9-ubi8~https://github.com/garnser/tibber-realtime-monitoring.git#openshift --context-dir python-apps/realtime
```

Update your tibber application with the values from the configmap and secret:
```
oc set env deploy tibber --from secret/tibber-secret
oc set env deploy tibber --from configmap/tibber-config
 ```

### tibber cronjobs
You need to create container images for the python code that should run as a Kubernetes cronjob. This is also done with the tools available to you in OKD:
```
oc new-build python:3.9-ubi8~https://github.com/garnser/tibber-realtime-monitoring.git#openshift --name currentprice --context-dir python-apps/currentprice
oc new-build python:3.9-ubi8~https://github.com/garnser/tibber-realtime-monitoring.git#openshift --name weather --context-dir python-apps/weather
 ```

You can track the process and output from the build by tailing in the build config log. For example, the weather application build can be tracked with the command `oc logs -f bc/weather`
When the build is complete. It pushes the container image to the internal OKD registry. You can see your container images by executing `oc get is`
Update the image: value in the cronjob manifest with the values from the output of `oc get is`
```yaml
  image: changeme
```
to
```yaml
 image: image-registry.openshift-image-registry.svc:5000/openinfra/weather
```
and
```yaml
 image: image-registry.openshift-image-registry.svc:5000/openinfra/currentprice
```
Create the cronjob by applying the manifests:
```
oc apply -f manifests/currentprice-cronjob.yaml
oc apply -f manifests/weather-cronjob.yaml
 ```

### grafana
grafana is installed using the grafana operator. You need to install the operator from the operator hub. In the administrator console, navigate to Operators -> OperatorHub and search for "grafana". Install the operator in the openinfra namespace.
When the operator has finished installing. Create the grafana resources; Grafana, GrafanaDataSource, and Grafana Dashboard, by applying the manifests.
First, verify the successful installation of the operator:
```
oc get csv | grep grafana
```
It should return an output similar to:
`grafana-operator.v4.2.0 Grafana Operator 4.2.0 grafana-operator.v4.1.1 Succeeded`
Once succeded, create the resources:
```
oc create -f manifests/tibber-grafana.yaml
oc create -f manifests/tibber-grafanadatasources.yaml
oc create -f manifests/tibber-grafanadashboard.yaml
 ```
Get the external route for your application
```
oc get route grafana-route -o jsonpath='{.status.ingress[].host}'
```
Use a web browser to access it to view your consumption and cost data.

## Get tibber?
If you want to get tibber yourself, please use my invite [link](https://tibber.com/se/invite/6649f6fc) and we both get some credits in their store, to buy cool stuff. For example, the tibber pulse that was used in this project. Thanks!<br>
https://tibber.com/se/invite/6649f6fc

