
## Description
This hands-on workshop, aimed at developers and solution builders, introduces how to leverage LLMs for RAG(Retrieval Augmented Generation).

In this case,
* we bring kNN to search solutions of related problems by AWS Opensearch;
* Use one of LLM models to do analysis for all related content and rendering with streamed response from the LLM model.

Deployment
please go to infrasturcture folder. 
You need to setup python env,
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Then you can kick off infrastructure deployment via
```
cdk deploy
```
If you don't have cdk booted in your account, you may need to setup by,
```
cdk bootstrap aws://ACCOUNT-NUMBER-1/REGION-1
```
Please find more details on cdk guide via [cdk boostrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)

If you don't have cdk installed, please refer to https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html