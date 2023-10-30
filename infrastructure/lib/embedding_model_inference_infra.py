import os
from constructs import Construct

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudwatch as cloudwatch,
    aws_sagemaker as sagemaker,
    aws_applicationautoscaling as asg,
)

from .config import PYTORCH_VERSION, TRANSFORMERS_VERSION, PY_VERSION, REGION_DICT


class EmbeddingModelInferenceInfra(Construct):
    # @property
    # def bucket_name(self):
    #     return self._bucket_name

    @property
    def endpoint_name(self):
        return self._endpoint_name

    @property
    def endpoint_ref(self):
        return self._endpoint_ref

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id)

        self._deploy_partition = "aws"
        self._region = os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
        self._instance_type = kwargs['instance_type']
        self._project_name = kwargs['project_name']
        if self._region.startswith("cn"):
            self._deploy_partition = "aws-cn"

        # self._local_model_path = self._get_local_model_path()

        # self._data_bucket = self._create_data_bucket()
        self._sagemaker_role = self._create_sagemaker_role()

        # self._model_deployment, s3_model_file_url = self._create_model_deployment()

        endpoint = self._create_endpoint(None, self._sagemaker_role)

        # self._bucket_name = self._data_bucket.bucket_name
        self._endpoint_name = endpoint.attr_endpoint_name
        self._endpoint_ref = endpoint.ref

        cdk.CfnOutput(
            self, f"SageMakerEndpoint", value=self._endpoint_name)

    def _get_local_model_path(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), os.pardir, 'models')

    def _create_endpoint(self, s3_model_file_url, sagemaker_role):
        prefix = f"{self._project_name}"
        instance_type = self._instance_type

        image_uri = self._get_sagemaker_image_uri()

        # HF_TASK          = "feature-extraction"
        # HF_MODEL_ID      = "sentence-transformers/msmarco-distilbert-base-v3"
        # SAGEMAKER_REGION = "us-east-1"
        # SAGEMAKER_CONTAINER_LOG_LEVEL = 20

        # ===========================
        # ===== SAGEMAKER MODEL =====
        # ===========================
        model = sagemaker.CfnModel(
            self,
            f"{prefix}Model",
            execution_role_arn=sagemaker_role.role_arn,
            # the properties below are optional
            enable_network_isolation=False,
            containers=[
                sagemaker.CfnModel.ContainerDefinitionProperty(
                    container_hostname=f"{prefix}ContainerHostname",
                    image=image_uri,
                    mode="SingleModel",
                    # model_data_url=s3_model_file_url,
                    environment={
                        "HF_TASK": "feature-extraction",
                        "HF_MODEL_ID": "shibing624/text2vec-base-chinese",
                        "SAGEMAKER_CONTAINER_LOG_LEVEL": 20,
                        "SAGEMAKER_REGION": cdk.Aws.REGION,
                        # "SAGEMAKER_PROGRAM": "inference.py",
                        # "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code"
                    },
                )
            ],
        )

        # model.node.add_dependency(self._model_deployment)

        # =====================================
        # ===== SAGEMAKER ENDPOINT CONFIG =====
        # =====================================
        variant_name = "AllTraffic"
        endpoint_config = sagemaker.CfnEndpointConfig(
            self,
            f"{prefix}EndpointConfig",
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    initial_instance_count=1,
                    initial_variant_weight=1.0,
                    instance_type=instance_type,
                    model_name=model.attr_model_name,
                    variant_name=variant_name,
                )
            ],
        )

        # endpoint_config.add_dependency(model)
        endpoint_config.add_depends_on(model)
        # ==============================
        # ===== SAGEMAKER ENDPOINT =====
        # ==============================

        endpoint = sagemaker.CfnEndpoint(
            self,
            f"{prefix}Endpoint",
            endpoint_name=f'{prefix}Endpoint',
            endpoint_config_name=endpoint_config.attr_endpoint_config_name,
        )
        cdk.CfnOutput(
            self, "SagemakerModelEndpoint", value=endpoint.attr_endpoint_name
        )

        # add the autoscaling policy
        target = asg.ScalableTarget(
            self,
            "ScalableTarget",
            service_namespace=asg.ServiceNamespace.SAGEMAKER,
            max_capacity=2,
            min_capacity=1,
            resource_id=f"endpoint/{endpoint.attr_endpoint_name}/variant/{variant_name}",
            scalable_dimension="sagemaker:variant:DesiredInstanceCount",
            role=sagemaker_role
        )
        target.node.add_dependency(endpoint)

        target.scale_to_track_metric(
            "GPU35Tracking",
            target_value=35,
            custom_metric=cloudwatch.Metric(
                metric_name="GPUUtilization",
                namespace="/aws/sagemaker/Endpoints",
                period=cdk.Duration.minutes(3),
                dimensions_map={
                    "EndpointName": endpoint.attr_endpoint_name,
                    "VariantName": variant_name,
                },
                statistic="Average",
            ),
            scale_in_cooldown=cdk.Duration.seconds(600),
            scale_out_cooldown=cdk.Duration.seconds(300),
        )

        return endpoint

    def _create_data_bucket(self):
        data_bucket = s3.Bucket(
            self,
            f"{self._project_name}ModelData",
            removal_policy=cdk.RemovalPolicy.RETAIN,
            object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
            # removal_policy=cdk.RemovalPolicy.DESTROY if self._env.is_dev() else cdk.RemovalPolicy.RETAIN,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        data_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowSSLRequestsOnly",
                effect=iam.Effect.DENY,
                actions=["s3:*"],
                conditions={"Bool": {"aws:SecureTransport": "false"}},
                principals=[iam.AnyPrincipal()],
                resources=[
                    data_bucket.arn_for_objects("*"),
                    data_bucket.bucket_arn,
                ],
            )
        )

        cdk.CfnOutput(
            self, f"ModelBucketName", value=data_bucket.bucket_name)
        return data_bucket

    def _create_model_deployment(self):
        """
         Copy one trained model and test images to the s3 bucket

        :param bucket: bucket
        :type bucket:
        :return: a s3 bucket address for the model, the model is the one within this sample/model folder
        :rtype: basestring
        """
        model_deployment = s3_deployment.BucketDeployment(
            self,
            "model_file",
            sources=[s3_deployment.Source.asset(self._local_model_path)],
            destination_bucket=self._data_bucket,
            cache_control=[
                s3_deployment.CacheControl.from_string(
                    "max-age=65536,public,immutable"
                )
            ],
            memory_limit=1024,
            ephemeral_storage_size=cdk.Size.mebibytes(2048),
            destination_key_prefix="model",
        )

        return model_deployment, f"s3://{self._data_bucket.bucket_name}/model/{self._env.sagemaker_inference_model_name}"

    def _create_sagemaker_role(self):
        # IAM Roles
        name = "Sagemaker"
        sagemaker_role = iam.Role(
            self,
            f"{name}Role",
            description="SageMaker role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy(
                    self,
                    f"{name}Policy",
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:GetBucketAcl",
                                "s3:PutObjectAcl",
                                "s3:AbortMultipartUpload",
                            ],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetObject"],
                            resources=["*"],
                            conditions={
                                "StringEqualsIgnoreCase": {
                                    "s3:ExistingObjectTag/SageMaker": "true"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["iam:PassRole"],
                            resources=["*"],
                            conditions={
                                "StringEquals": {
                                    "iam:PassedToService": "sagemaker.amazonaws.com"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetBucketAcl", "s3:PutObjectAcl"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*sagemaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*SageMaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*Sagemaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*LabelingFunction*",
                            ],
                        ),
                        iam.PolicyStatement(
                            actions=["s3:ListBucket"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            actions=["s3:CreateBucket"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "sagemaker:DescribeEndpointConfig",
                                "sagemaker:DescribeModel",
                                "sagemaker:InvokeEndpoint",
                                "sagemaker:ListTags",
                                "sagemaker:DescribeEndpoint",
                                "sagemaker:CreateModel",
                                "sagemaker:CreateEndpointConfig",
                                "sagemaker:CreateEndpoint",
                                "sagemaker:DeleteModel",
                                "sagemaker:DeleteEndpointConfig",
                                "sagemaker:DeleteEndpoint",
                                "sagemaker:CreateTrainingJob",
                                "sagemaker:DescribeTrainingJob",
                                "sagemaker:UpdateEndpoint",
                                "sagemaker:UpdateEndpointWeightsAndCapacities",
                                "autoscaling:*",
                                "ecr:GetAuthorizationToken",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:SetRepositoryPolicy",
                                "ecr:CompleteLayerUpload",
                                "ecr:BatchDeleteImage",
                                "ecr:UploadLayerPart",
                                "ecr:DeleteRepositoryPolicy",
                                "ecr:InitiateLayerUpload",
                                "ecr:DeleteRepository",
                                "ecr:PutImage",
                                "ecr:CreateRepository",
                                "ec2:CreateVpcEndpoint",
                                "ec2:DescribeRouteTables",
                                "cloudwatch:PutMetricData",
                                "cloudwatch:GetMetricData",
                                "cloudwatch:GetMetricStatistics",
                                "cloudwatch:ListMetrics",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:GetLogEvents",
                                "logs:CreateLogGroup",
                                "logs:DescribeLogStreams",
                                "iam:ListRoles",
                                "iam:GetRole",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["kms:Decrypt",
                                     "kms:Encrypt", "kms:CreateGrant"],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["iam:CreateServiceLinkedRole"],
                            resources=[
                                "arn:aws:iam::*:role/aws-service-role/sagemaker.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_SageMakerEndpoint"
                            ],
                            conditions={
                                "StringLike": {
                                    "iam:AWSServiceName": "sagemaker.application-autoscaling.amazonaws.com",
                                }
                            },
                        ),
                    ],
                )
            ],
        )

        cdk.CfnOutput(self, "SagemakerRoleName", value=sagemaker_role.role_name)

        return sagemaker_role

    def _get_sagemaker_image_uri(self):

        repository = (
            f"{REGION_DICT[self._region]}.dkr.ecr.{self._region}.amazonaws.com/huggingface-pytorch-inference"
        )
    
        tag = f"{PYTORCH_VERSION}-transformers{TRANSFORMERS_VERSION}-{'gpu-py39-cu117' if self._is_gpu_instance() else 'cpu-py39'}-ubuntu20.04"
        # tag = f"{PYTORCH_VERSION}-{'gpu' if use_gpu == True else 'cpu'}-{PY_VERSION}"
        print(f'Image url:{repository}:{tag}')
        return f"{repository}:{tag}"

    def _is_gpu_instance(self):
        return True if self._instance_type.split(".")[1][0].lower() in ["p", "g"] else False

