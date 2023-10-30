import json

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
  aws_ec2 as ec2,
  aws_opensearchservice as opensearch,
  aws_secretsmanager as sm,
)
from constructs import Construct

class KnowledgeVectorDbInfra(Construct):
  """
  Create a vector db to host embeddings for knowledge search by KNN.
  This implementation will use AWS OpenSearchService as and knowledge vector db.
  """

  @property
  def domain_endpoint_name(self):
    return self._open_search_service.domain_endpoint

  @property
  def domain_arn(self):
    return self._open_search_service.domain_arn

  def __init__(self,
               scope: Construct,
               id: str,
               **kwargs):
    super().__init__(scope, id, **kwargs)

    self._open_search_service = self._create_open_search_domain()

    cdk.CfnOutput(self, f"OpenSearchDomainEndpoint",
                  value=self._open_search_service.domain_endpoint)

    cdk.CfnOutput(self, 'OPSHostEndpoint', value=self.search_domain_endpoint, export_name='OPSHostEndpoint')
    cdk.CfnOutput(self, 'OPSDashboardURL', value=f"{self.search_domain_endpoint}/_dashboards/", export_name='OPSDashboardURL')

  def _create_secret(self):
    """
    Create a master user-password pair which has 12 characters,
    """
    master_user_secret = sm.Secret(self, "OSMasterUserSecret",
                                         generate_secret_string=sm.SecretStringGenerator(
                                             secret_string_template=json.dumps({"username": "admin"}),
                                             generate_string_key="password",
                                             # Master pass word must be at least 8 characters long and contain at least one uppercase letter,
                                             # one lowercase letter, one number, and one special character.
                                             password_length=12
                                            ),
                                         secret_name="opensearch-master-user"
                                     )
    return master_user_secret
  def _create_open_search_domain(self):
    """
    Create open search with a small instance type to host data and a removal_policy of DESTROY. Please change the params if necessary.
    """
    secret = self._create_secret()

    ops_domain = opensearch.Domain(self,
                                   "OpenSearch",
                                    domain_name='knowledge-vector-db',
                                    version=opensearch.EngineVersion.OPENSEARCH_2_7,
                                    capacity={
                                        "master_nodes": 0,
                                        "master_node_instance_type": "t3.small.search",
                                        "data_nodes": 1,
                                        "data_node_instance_type": "t3.small.search"
                                    },
                                    ebs={
                                        "volume_size": 5,
                                        "volume_type": ec2.EbsDeviceVolumeType.GP3
                                    },
                                    fine_grained_access_control=opensearch.AdvancedSecurityOptions(
                                        master_user_name=secret.secret_value_from_json("username").unsafe_unwrap(),
                                        master_user_password=secret.secret_value_from_json("password")
                                    ),
                                    enforce_https=True,  # Enforce HTTPS is required when fine-grained access control is enabled.
                                    node_to_node_encryption=True, # Node-to-node encryption is required when fine-grained access control is enabled
                                    encryption_at_rest={ # Encryption-at-rest is required when fine-grained access control is enabled.
                                        "enabled": True
                                    },
                                    use_unsigned_basic_auth=True,  # default: False
                                    removal_policy=cdk.RemovalPolicy.DESTROY,
                                   )

    cdk.Tags.of(ops_domain).add('Name', 'smartsearch-ops')

    self.search_domain_endpoint = ops_domain.domain_endpoint
    self.search_domain_arn = ops_domain.domain_arn