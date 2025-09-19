# CLAI - Your AI-powered CLI

![CLAI](images/command-mode.png)

With modern large language models nowadays, it is very easy to just ask what command
would do a specific task it is spits it out.  
This small project reproduces that using whatever techniques are currently known.

**Our goal will be to predict Nushell commands given a user's instruction,**

A far more concrete goal is to learn and explore how to use LLMs from a programer's perspective:
- How far can one go using language models with a "small" number of parameters.
- Which techniques would get us close to high accuracy without requiring spending money (or very little of it).
- What other techniques/tools would provide value to end users?

The project is not meant to be of production quality -- existing tools do this very well already.  
The project is written in a manner that it is easy to understand and extend so that if others wish to use
it to learn don't need to start from scratch.

## Motivation
I was reading the book "LLM Engineer's Handbook: Master the Art of Engineering Large Language Models from Concept to Production"
and I liked it. So I set out to apply what is taught in it via my this small project.

I settled on a CLI tool for a few of reasons:
1. I don't need to worry about creating a complicated UI and the associated backend machinery.
2. The responses (commands) are usually very short so generating them should not be taxing on the language model.
3. Commands have structure so it is quite easy to evaluate how well we are doing.

A major part I liked about the book is that it emphasizes devops/mlops.
In practice (i.e. on the job) this is quite a useful thing to know.
So having a project were one can play with different devops and mlops tools in very important.

## Getting setup and running
I'm writing this on a Linux machine so I can't say much about Windows or Mac at the moment.

### Nushell
Since the goal is to predict Nushell commands,
the reader should install Nu: https://www.nushell.sh/book/installation.html.

### Ollama
We use Ollama to run language models locally.
So first install Ollama from: https://ollama.com/download

We will use the `llama3.1` model so pull it into Ollama:
```
ollama pull llama3.1:latest
```

### Docker
We run a lot of ML ops in docker containers so the reader should install docker as well:
https://docs.docker.com/get-started/get-docker/

### UV
Last, we use `uv` as the package manager: https://docs.astral.sh/uv/getting-started/installation/


With those 4 tools installed, the reader is almost ready.
It is assumed that the reader has already cloned the current repository:
```
git clone git@github.com:ntwalibas/clai.git
```

To run the project, a `.env` file with environment variables must be provided.
Mine looks like this:
```
# MongoDB database
MONGO_DATABASE_HOST     =   "mongodb://clai:clai@127.0.0.1:27017"
MONGO_DATABASE_NAME     =   "clai"

# Qdrant vector database
QDRANT_CLIENT_URL       =   "http://127.0.0.1:6333"
QDRANT_COLLECTION_NAME  =   "clai"
QDRANT_EMBEDDING_MODEL  =   "all-MiniLM-L6-v2"

# PostgreSQL database
POSTGRES_USER           =   "clai"
POSTGRES_PASSWORD       =   "p@ssw0rd"
POSTGRES_DATABASE       =   "postgres"
MLFLOW_DATABASE         =   "clai_mlflow"
MLFLOW_USERNAME         =   "admin"
MLFLOW_PASSWORD         =   "password1234"
MLFLOW_TRACKING_URI     =   "file:///home/ntwalib/.config/mlflow"

# DSPy
LLM_NAME                = "ollama_chat/llama3.1:latest"
LLM_ENDPOINT            = "http://localhost:11434"
```

Please note that the `MLFLOW_TRACKING_URI` environment variable must be replaced
with a valid path on your system.

The project comes with a small "management" script to take care of regular tasks
that happen during developement:
```
Clai engineering management script.
Manage local infrastructure, settings, pipelines, and more.

Usage:
  manage.sh [options] <command> [command options]

Options:
  -h, --help              Show this help message
  -v, --version           Show script version

Commands:
  infra                   Manage the infrastructure
    --up                  Start the services
    --down                Stop the services
    --status              Status of services

  settings                Manage ZenML settings
    --export              Export local settings to ZenML secrets
    --drop                Delete settings from ZenML secrets

  pipeline                Run the given pipeline
    --no-cache            Disable cache (optional)
    --etl                 Run the ETL pipeline only
    --rag                 Run the RAG pipeline only
    --all                 Run all the pipelines
    -c, --config FILE     Path to pipeline configuration file (required)
```

Right now, we only deal with 3 commands to get us up and running.
### Setting up secrets
Assuming you have already created your `.env` file and duly filled,
you place the contents of ZenML inside its "secrets" vault so they can be accessed inside the program:
```
./manage.sh secrets --export
```

### Set up the infrastructure
We need to have docker containers running with our services available not only for development
but also to run the main application:
```
./manage.sh infra --up
```

Pay attention to the output of the above command, ZenML might ask you to open a link in order to log you in.

You can check if the infrastructure is running by running:
```
./manage.sh infra --status
```

Once all services are running, I generally keep ZenML, Qdrant, and MLFlow dashboards open
so I can double-check if things I'm doing are really working:
- ZenML: http://127.0.0.1:8237/
- Qdrant: http://127.0.0.1:6333/
- MLFlow: http://127.0.0.1:5000/

Since we use MongoDB as our data warehouse, I also keep MongoDB Compass open
to see if the data pulled from the online documentation is being loaded correctly.

### Run pipelines to load some data
We have almost eveything ready, we now need to run the ETL pipeline to in order
to fetch some command documentations and save them in MongoDB.

After the ETL has run, the RAG pipeline needs to run in order to load data into
Qdrant.
> Right now the RAG pipeline also does evaluation to tell you how accurate RAG will be.
> In a short time, I will add optimization step(s) so RAG can perform better.

You can run both pipeline in one go with:
```
./manage.sh pipeline --all --config ./data/commands.yml
```

Or you can run them individually, check `./manage.sh` documentation.

## Test drive CLAI
At this point, you have everything you need to try CLAI.
First make sure to have `nu` running:
```
nu
```

Then run CLAI:
```
./clai.sh
```

ENJOY!

The commands available are decided by the contents of `data/commands.yml`.
If you wish to add an additional command, just drop it in there.

In the shell, you can switch between free text mode (where you type instructions in natural language) to command mode (where Nushell commands are expected) using <kbd>CTRL</kbd>+<kbd>T</kbd>.
> Heck, I wish a CLI like this but much better than this project exists. Sometimes I forget commands, and it would be quicker to ask right there in the terminal what to do.

To exit the program, you have a couple of options:
1. Press <kbd>CTRL</kbd>+<kbd>C</kbd>.
2. Type `exit` or `quit`.

## Constraints
To make this project useful to myself and others, I imposed a few constraints on what tools and techniques can be used:
1. We will limit ourselves to language models that can run on commodity hardware, ideally with no GPU.
2. Each technique that is and will be explored should not require costly resources: so no large-scale finetuning.
3. All the tools we use should run locally, but can scale to a production environment.
4. The language model should not have been trained on the our task.

Here is how those constrains are fulfilled:
### Language model
I settled on `llama3.1` running under Ollama. I chose this model for two reasons:
- It is reasonably small: not too small, not too big.
- The project is about predicting Nushell commands which `llama3.1` doesn't know about but it was trained on predicting regular commands.

### Cost
All the tools used to help facilitate our work are open source:
- ZenML is the orchestrator and it has both free and paid versions.
- MLFlow is the experiment tracker and it is entirely free.
- Qdrant is the vector database, and has both free and paid versions.
- Ollama is the language model runner and it is free.

### Scalability
Except Ollama, all the other tools are dockerized so they can run, in say, Kubernetes for self-hosted solutions.
Some of them offer paid plans for those who want to use them as services.

### Freshness
As already said, our goal is to predict a Nushell command given the user's instructions.
The `llama3.1` was trained on regular POSIX commands but not on Nushell commands.
This makes it perfect since it knows more than free text (text without structure such as commands)
but doesn't know about the commands we care about.

## Implementation approach
Right now, the focus is on retrieval-augmented generation (RAG).
I rely heavily on [DSPy](https://github.com/stanfordnlp/dspy) to reduce a lot of boilerplace,
especially dealing with prompt engineering and context engineering.

I would even say that this project is as much about experimenting with LLM engineering
as it is about experimenting with DSPy.

The book cited above doesn't use DSPy but after experimenting with,
if just for prompt engineering, I am convinced I would not want to use anything else for this project.

I experimented with it for prompt optimization, context optimization, and in general program optimization;
and other things it provides, and I can say that while not everything worked well locally
(I had an optimization with GEPA run for 8 hours with not much of an improvement),
I can say I'm happy I settled on DSPy. I hope you will give it a try as well.

The code itself is structured according to domain-driven design, just as in the book,
and it is easy to follow if I say so myself.

## Next steps
So I have simple RAG running at the moment.
I intend to add program optimization offered by DSPy to increase the prediction accuracy (I have played with this in a Jupyter notebook and it did work).  
After that, I want to add one RAG technique talked about in the book namely query expansion.

With that, I have no other clear direction that to just add whatever I like and/or found useful over time.
