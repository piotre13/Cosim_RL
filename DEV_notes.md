# TODO
- definire varie tipologie di simulator workflow (proposta:
  - **simple** : inputs one round of step and output
  - **iterative**: inputs step outputs repeated until convergence
  - **iterative dynamic inp/out**: inputs step outputs --> different inputs step diff outputs until end (must have a wokflow order) )       
- fare test esempio di iterative dynamic base con reverse I/O (esempio enevelope xuyuan vedi quaderno) per esempio qui foprse conviene unpack communication_management
- should rething the structure of same mod_inst multiple inp/sub/pub avoinding the key and using the the key value as key.
- inserire gestione reset nel Federate simple
- helics connector permettono di creare tramite semplice config le varie connessioni






# FMU integration
definire il federated o un model?
non posso fare get se non sugli output prima di entrare in execution mode!!



# RICORDA
remember to kill brokers helics comes with some command line commands
Publication/Subscritpions/Inputs possono solo essere valori numerici (doubles)

# nomenclature standard




# Connections config

How to write connections point in the config files of each federate.

## Subscription
empty subscriptions (always required for now)
``` yaml
fed_connections:
  sub: {}
  ```
simple subscription **TO BE  DONE**

``` yaml
fed_connections:
  sub: 
  ```
## Inputs
input dict  keys:
- key: name of the mod number and var name that will be received _mod_num/var_name_
- type: type of variable value (int/float/double etc..) see helics options
- units: measurement unit of the value
- global: if global or not change the automatic naming format in helics (does not include the fed name because is already included in key)
- targets : list of topic from which this input will be received
- multi_input_handling_method: string specifying the aggregation method see helics options

empty inputs (always required for now)
```yaml
  inp: {}
```


single model instance single input
```yaml
  inp:
    0: [ {
      "key": "voltage",
      "type": "double",
      "units": "V",
      "targets": [
        "Charger/0/voltage",
      ]
    }]
```

multiple model instance multiple inputs

```yaml
  inp:
    0: [ {
      "key": "voltage",
      "type": "double",
      "units": "V",
      "targets": [
        "Charger/0/voltage",
      ]
    },
    {
      "key": "test_val",
      "type": "double",
      "units": "V",
      "targets": [
        "Charger/0/test_val",
      ]
    }]
    1: [ {
      "key": "voltage",
      "type": "double",
      "units": "V",
      "targets": [
        "Charger/1/voltage",
      ]
    },
    {
      "key": "test_val",
      "type": "double",
      "units": "V",
      "targets": [
        "Charger/1/test_val",
      ]
    }]

```
#### special multi-input with aggregation
this when you want to receive as a single input value the aggregation of multiple pubblications
```yaml
  inp:
    0: [ {
      "key": "power",
      "type": "double",
      "units": "W",
      "multi_input_handling_method": "sum",  # aggregation method ref to helics
      "targets": [     # topic opf the publication from which receiving the values
        "PV/0/pv",
        "Building/0/plug",
      ]
    }]
```

#### NB. of course is also valid single model multiple inputs, multiple models single inputs

## Publications
publication dict  keys:
- key: name of the topic must follow _Fed_name/mod_num/var_name_
- type: type of variable value (int/float/double etc..) see helics options
- units: measurement unit of the value
- global: if global or not change the automatic naming format in helics (does not include the fed name because is already included in key)

empty publications (always required for now)
```yaml
  pub: {}
```


single model instance single output (pub)
```yaml
  pub:
    0: [{
      "key": "voltage",
      "type": "double",
    }]
```

multiple model instance multiple outputs (pub)
```yaml
   pub:
    0: [{
      "key": "voltage",
      "type": "double",
      "units": "V",
    },
         {
      "key": "test_val",
      "type": "double",
      "units": "V",
    }]
    1: [{
      "key": "voltage",
      "type": "double",
      "units": "V",
    },
    {
      "key": "test_val",
      "type": "double",
      "units": "V",
    }]

```
#### NB. of course is also valid single model multiple pubs, multiple models single pubs


## Endpoints
**TODO** 


# Connection points registration inside Simple Federate (combo federate):

publications are registered and stored in a dict with key: pub topic and value :Helics_pub object

```python

self.pubs =
{
    '0':
        {
            'power': < helics.HelicsPublication >,
            'other_var_name': < helics.HelicsPublication >
        },

    '1':
        {
            'power': < helics.HelicsPublication >,
            'other_var_name': < helics.HelicsPublication >
        }
}
 ```

self.subs
```python

```
inputs are registered and stored in a dict with key: mod_receiver (_Fed_name/mod_num/var_name_) and value :Helics_input object
```python
self.inps = 
{
    '0':
        {
            'power': <helics.HelicsInput>,
            'other_var_name': <helics.HelicsInput>
        },
    
    '1':
        {
            'power': <helics.HelicsInput>,
            'other_var_name': <helics.HelicsInput>
        }
} 
```

#### TODO this for endpoints should be changed
endpoints are registered and stored in a dict with key: endpoint name (_Fed_name/mod_num/var_name_) and value :Helics_Endpoint object
```python
self.ends  = 
{
    '0': (<helics.HelicsEndpoint>, [test_msg, power], [[test_msg, power], [test_msg]]), 
    '1': (<helics.HelicsEndpoint>,[],[])                
}
```
# Data workflow and methods inside Federate

## Simple Federate (combo federate)
### Receive inputs:
                   

