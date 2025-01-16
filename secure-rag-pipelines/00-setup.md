## Setup and Prerequisites

Lets start with the setup for this workshop.

- Access to a [SpiceDB](https://authzed.com/spicedb) instance.  You can find instructions for installing SpiceDB [here](https://authzed.com/docs/spicedb/getting-started/install/macos)
- A [Pinecone account](https://www.pinecone.io/) and API key
- An [OpenAI Platform account](https://platform.openai.com/docs/overview) and API key
- [Jupyter Notebook](https://jupyter.org/) running locally

#### Running SpiceDB

Once you've installed SpiceDB, run a local instance with this command in your terminal: 

`spicedb serve --grpc-preshared-key rag-rebac-walkthrough`

and you should see something like this that indicates an instance of SpiceDB is running locally:

```
8:28PM INF configured logging async=false format=auto log_level=inf
o provider=zerolog
8:28PM INF GOMEMLIMIT is updated GOMEMLIMIT=25769803776 package=git
hub.com/KimMachineGun/automemlimit/memlimit
8:28PM INF configured opentelemetry tracing endpoint= insecure=fals
e provider=none sampleRatio=0.01 service=spicedb v=0
8:28PM WRN this version of SpiceDB is out of date. See: https://git
hub.com/authzed/spicedb/releases/tag/v1.39.1 latest-released-versio
n=v1.39.1 this-version=v1.37.2
8:28PM INF configuration ClusterDispatchCacheConfig.CacheKindForTes
ting=(empty) ClusterDispatchCacheConfig.Enabled=true ClusterDispatc
8:28PM INF using memory datastore engine
8:28PM WRN in-memory datastore is not persistent and not feasible t
8:28PM INF configured namespace cache defaultTTL=0 maxCost="32 MiB"
8:28PM INF schema watch explicitly disabled
8:28PM INF configured dispatch cache defaultTTL=20600 maxCost="164
8:28PM INF configured dispatcher balancerconfig={"loadBalancingConfig":[{"consistent-hashring":{"replicationFactor":100,"spread":1}}]} concurrency-limit-check-permission=50 concurrency-limit-lookup-resources=50 concurrency-limit-lookup-subjects=50 concurrency-limit-reachable-resources=50
8:28PM INF grpc server started serving addr=:50051 insecure=true network=tcp service=grpc workers=0
8:28PM INF running server datastore=*schemacaching.definitionCachingProxy
8:28PM INF http server started serving addr=:9090 insecure=true service=metrics
8:28PM INF telemetry reporter scheduled endpoint=https://telemetry.authzed.com interval=1h0m0s next=5m14s
```

## Learning Summary

- [x] In this module you installed and launched an instance of SpiceDB locally

## Navigation

Proceed to this Jupyter Notebook.

### Troubleshooting


