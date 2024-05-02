# regole e note su come creare lo script Create_federation e i generici federationConfig.yaml file 
Dal file di configurazione generale in yaml per tutta la federazione lo script deve essere in grado di creare i seguenti files
- runner.json
- file di configurazione di un federate .json (HELICS)
- file di configurazione di un federate .yaml (INIT)

c'e la possibilita che in caso di esecuzione distribuita e parallela su piu macchine ci sia bisogno di avere pi broker e quindi di creare piu runner files.






# come creare il runner.json
Segui struttura in **federations/example_federation/example_federation_runner.json**

cosa deve contenere il file di configurazioen del runner:
 - la directory dove trovare lo script eseguibile Federate.py (in funzione del tipo di federate)
 - il comando python per eseguire lo script 
   - l'eseguibile di ogni federates deve sempre contenere come argomenti:
     - nome file configurazione json del modello
     - nome file configurazione yaml del modell
     - nome della federation a cui appartiene


# come creare il file di configurazione di un federate .json (HELICS)


# come create il file di configurazione di un federate .yaml (INIT)