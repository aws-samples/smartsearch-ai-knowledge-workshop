
# RAG with Streaming LLM
This hands-on workshop, aimed at developers and solution builders, introduces how to leverage LLMs for RAG(Retrieval Augmented Generation).

In this solution,
* we bring kNN to search solutions of related problems by AWS Opensearch;
* Use one of LLM models to do analysis for all related content and rendering with streamed response from the LLM model.


## Overview
![Architecture](assets/images/architecture.jpg "Architecture")
This solution illustrate how to do semantic search across AWS AOS and utilize a LLM model to generate analysis with the following steps,
1. Query by keywords from Client for the solutions relating what you ask
2. Generate Embedding for keywords with Embedding Model
3. Search useful knowledge by keyword Embedding across vector DB
4. Return domain-specific knowledge from Vector DB
5. Post selected or all related information to LLM backend
6. Generate problem analysis and solution suggestion by LLM
7. Start to stream out the generated text word by word
8. Render the output word by word

## Cost

You are responsible for the cost of the AWS services used while running this solution. 

## Prerequisites

### Operating System
You need to
* prepare an ec2 instance with x86_64 architecture(t3.xlarge is recommended) for the deployment
  * install cdk in this deployment machine and get your account bootstrapped, please refer to [Install the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)
  * install docker in this deployment machine de and start the docker:: 
    ```shell
    $ sudo yum install docker
    $ sudo systemctl start docker
    ```
* prepare a sagemaker notebook instance(ml.t3.xlarge) to build your own custom model

### Third-party tools

* [Insomnia](https://insomnia.rest/) (Optional): You can post request with AWS IAM V4 Auth to test deployed API

### AWS account requirements

This deployment requires the following available in your AWS account

**Required resources:**
- AWS S3 bucket
- AWS AOS
- AWS SecretsManager
- AWS VPC
- AWS IAM role with specific permissions
- AWS SageMaker

Make sure your account can utility the above resources.

## Deploy the solution
Before you deploy this solution, be sure you have right aws credentials configured.
Now you need to install deployment dependencies.
```shell
  $ cd infrastructure
  $ python3 -m venv .venv
  $ . venv/bin/activate
  $ pip install -r requirements.txt
```

For this example, you can try with 'workshop' profile by the following command::
```
  $ cdk deploy -all --require-approval never
```

When it's done, the command prompt reappears. You can go to the AWS CloudFormation console and see that it now lists `RAGSearchWithLLMInfraStack`, `RAGSearchWithLLMSemanticSearchLambdaStack` and `RAGSearchWithLLMFrontendStack`. 

## Ingest sample data
You need to ingest some data to play with this solution. We provide a simple list of question-answer pairs. You can ingest with SageMaker Notebook and upload whole `data` folder into this notebook instance. Please follow the instructions in `data/data_ingestion.ipynb` to feed data into AWS AOS.

## Test
After deployment and data ingestion, you can get an url of from `RAGSearchWithLLMFrontendStack` stack in output cdk.
```shell
Outputs:
RAGSearchWithLLMFrontendStack.RAGSearchWithLLMFrontendSmartSearchUrl*** = https://***.cloudfront.net

```

### Service limits  (if applicable)

The solution can handle QA pairs for summarization. You can extend it if you have other requirements.

## Cleanup
Please kick `cdk destroy -all` to clean up the whole environment in this path `infrastructure`.

## FAQ, known issues, additional considerations, and limitations
N/A

## Revisions
N/A

## Notices
During the launch of this reference architecture,
you will install software (and dependencies) on the Amazon EC2 instances launched
in your account via stack creation.
The software packages and/or sources you will install
will be from the Amazon Linux distribution and AWS Services, as well as from third party sites.
Here is the list of third party software, the source link,
and the license link for each software.
Please review and decide your comfort with installing these before continuing.

BSD License: https://opensource.org/licenses/bsd-license.php

Historical Permission Notice and Disclaimer (HPND): https://opensource.org/licenses/HPND

MIT License: https://github.com/tsenart/vegeta/blob/master/LICENSE

Apache Software License 2.0: https://www.apache.org/licenses/LICENSE-2.0

Mozilla Public License 2.0 (MPL 2.0): https://www.mozilla.org/en-US/MPL/2.0/

ISC License: https://opensource.org/licenses/ISC
