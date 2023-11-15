#!/usr/bin/env python3

import os

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    App, CfnOutput, Stack
)

from lib.smart_search_infra_stack import SmartSearchInfraStack
from lib.semantic_search_api_stack import SemanticSearchLambdaStack
from lib.smart_search_frontend_stack import SmartSearchFrontendStack
from lib.utils import get_value


app = App()
project_name = app.node.try_get_context("project_name")
instance_type_em = app.node.try_get_context("instance_type_em")

AWS_ENV = cdk.Environment(account=os.environ['CDK_DEFAULT_ACCOUNT'],
                          region=os.environ['CDK_DEFAULT_REGION'])

infra_stack = SmartSearchInfraStack(app,
                                    f"{project_name}InfraStack",
                                    project_name=project_name,
                                    instance_type_em=instance_type_em,
                                    env=AWS_ENV,
                                    description="Smart search infrastructure including embedding endpont, vector db, llm docker and llm application",
                                    )

semantic_search_stack = SemanticSearchLambdaStack(app,
                                    f"{project_name}SemanticSearchLambdaStack",
                                    search_engine=infra_stack.opensearch_domain_endpoint,
                                    em_endpoint_name=infra_stack.em_endpoint_name,
                                    env=AWS_ENV,
                                    description="Semantic search in Smart search as a moddler layer to handle search across vector db and keywords embedding",
                                    )
semantic_search_stack.add_dependency(infra_stack)

summarize_api = get_value("SummarizeApi")
semantic_search_api = get_value("SemanticSearchApi")

frontend_stack = SmartSearchFrontendStack(app,
                               f"{project_name}FrontendStack",
                               project_name=project_name,
                               semantic_search_api=summarize_api,
                               summarize_api = summarize_api,
                               env=AWS_ENV,
                               description="Front end for Smart search",
                              )                         
frontend_stack.add_dependency(semantic_search_stack)

# # add tags
cdk.Tags.of(infra_stack).add('CNRP/PRJ', project_name)
cdk.Tags.of(semantic_search_stack).add('CNRP/PRJ', project_name)
cdk.Tags.of(frontend_stack).add('CNRP/PRJ', project_name)
app.synth()
