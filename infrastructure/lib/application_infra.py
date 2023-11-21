#!/usr/bin/env python3
import os

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_elasticloadbalancingv2 as elbv2,
    CfnOutput,
    aws_certificatemanager as cm,
    aws_acmpca as acmpca,
)
from constructs import Construct


class ApplicationInfra(Construct):
    """
    Create llm web ec2 instance and alb and a load balance before ec2 asg
    """

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id)
        region = kwargs["env"].region

        data = open("./user_data.sh", "rb").read()

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(str(data, "utf-8"))

        vpc_infra = VPCInfra(self, "LLMVPC")

        ec2_role = self._create_ec2_role()
        image_id = self._get_dl_image_id(scope)

        # creat load balance
        lb = elbv2.ApplicationLoadBalancer(
            self,
            "LLM-ALB",
            vpc=vpc_infra.vpc,
            internet_facing=True,
            load_balancer_name="LLM-ALB",
        )

        self._summarize_api = f"http://{lb.load_balancer_dns_name}/summarize"

        # creat asg
        asg: autoscaling.AutoScalingGroup = autoscaling.AutoScalingGroup(
            self,
            "LLMASG",
            vpc=vpc_infra.vpc,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.G4DN,
                ec2.InstanceSize.XLARGE2,
                # ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM
            ),
            ##todo for gpu? machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            machine_image=ec2.MachineImage.generic_linux(
                {region: image_id}
            ),  # pytorch gpu
            # machine_image=image_id,
            block_devices=[
                autoscaling.BlockDevice(
                    device_name="/dev/xvda",
                    volume=autoscaling.BlockDeviceVolume.ebs(
                        50,
                        volume_type=autoscaling.EbsDeviceVolumeType.GP3,
                        encrypted=True,
                        throughput=600,
                        delete_on_termination=True,
                    ),
                )
            ],
            role=ec2_role,
            user_data=user_data,
            ssm_session_permissions=True,
            min_capacity=1,
            max_capacity=1,
            termination_policies=[autoscaling.TerminationPolicy.OLDEST_INSTANCE],
        )

        cdk.Tags.of(asg).add("Patch Group", "AccountGuardian-PatchGroup-DO-NOT-DELETE")

        # cert = self._create_cert(id)
        # added listener
        listener = lb.add_listener(
            "Listener", port=80, protocol=elbv2.ApplicationProtocol.HTTP
        )

        listener.add_targets(
            "Target", port=5000, protocol=elbv2.ApplicationProtocol.HTTP, targets=[asg]
        )

        listener.connections.allow_default_port_from_any_ipv4("Open to the world")
        # listener.connections.allow_internally
        asg.scale_on_request_count("AModestLoad", target_requests_per_minute=60)

        # create apigateway in front to alb
        self._create_apigw(region, self._summarize_api)

    def _create_ec2_role(self):
        # EC2 IAM Roles
        name = "Ec2"
        ec2_role = iam.Role(
            self,
            f"{name}Role",
            description="LLM EC2 Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy(
                    self,
                    f"{name}Policy",
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "ecr:GetAuthorizationToken",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:SetRepositoryPolicy",
                                "ecr:CompleteLayerUpload",
                                "ecr:BatchDeleteImage",
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
                    ],
                )
            ],
        )

        return ec2_role

    def _get_dl_image_id(self, scope: Construct):
        """
        Get Deep Learning AMI GPU with PyTorch 1.13.1 for LLM docker
        """
        gpu_image = ec2.LookupMachineImage(
            name="Deep Learning AMI GPU PyTorch 1.13.1 (Amazon Linux 2)*",
            # name="al2023-ami-2023*x86_64",
            owners=["amazon"],
            windows=False,
        )

        return gpu_image.get_image(scope).image_id

    def _create_cert(self, prefix):
        ca_arn = "arn:aws:acm-pca:us-east-1:123456789012:certificate-authority/023077d8-2bfa-4eb0-8f22-05c96deade77"
        cert = cm.PrivateCertificate(
            self,
            f"{prefix}PrivateCertificate",
            domain_name="*.cloudfront.net",  # optional
            certificate_authority=acmpca.CertificateAuthority.from_certificate_authority_arn(
                self, "CA", ca_arn
            ),
        )
        return cert

    def _create_apigw(self, region, url):
        # api gateway resource
        self._api = apigw.RestApi(
            self,
            "summarize-api",
            endpoint_types=[apigw.EndpointType.REGIONAL],
        )

        summarize_root = self._api.root.add_resource(
            "summarize",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_methods=["POST", "OPTIONS"],
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_credentials=True,
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                ],
            ),
        )

        summarize_api_integration = apigw.HttpIntegration(
            url,
            http_method="POST",
            options=apigw.IntegrationOptions(
                # timeout=cdk.Duration.seconds(60),
                passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH,
                # passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_TEMPLATES,
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_templates={"application/json": ""},
                    )
                ],
                # request_templates={
                #         "application/json": "{ \"statusCode\": 200 }"
                # }
            ),
            proxy=False,
        )

        summarize_root.add_method(
            "POST",
            summarize_api_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Content-Type": True,
                    },
                    response_models={"application/json": apigw.Model.EMPTY_MODEL},
                )
            ],
        )

        CfnOutput(
            self,
            "SummarizeApi",
            export_name="SummarizeApi",
            value=f"https://{self._api.rest_api_id}.execute-api.{region}.amazonaws.com/prod/summarize",
        )


class VPCInfra(Construct):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id)

        self._scope = scope

        self._vpc = ec2.Vpc(
            self,
            "LLMVPC",
            max_azs=3,
            ip_addresses=ec2.IpAddresses.cidr("172.31.8.0/21"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=24,
                ),
            ],
        )

        # add flow log
        self._vpc.add_flow_log("FlowLogVPC")

    @property
    def subnet_selection(self):
        return self._vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        ).subnets

    @property
    def vpc(self):
        return self._vpc

    @property
    def vpc_endpoint(self):
        return self._vpc.endpoint_id
