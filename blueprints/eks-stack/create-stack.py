"""
Build service item action for AWS EKS Cluster Service blueprint.
"""
from common.methods import set_progress
from infrastructure.models import CustomField, Environment
import boto3
from botocore.exceptions import ClientError
import ast
import time
from resources.models import Resource
from resourcehandlers.aws.models import AWSHandler


def get_boto_client(env_id=None, boto_service=''):
    if env_id == None:
        return None
    env = Environment.objects.get(id=env_id)
    rh = env.resource_handler.cast()
    client = boto3.client(boto_service,
                          region_name=env.aws_region,
                          aws_access_key_id=rh.serviceaccount,
                          aws_secret_access_key=rh.servicepasswd
                          )
    return client, env


def generate_options_for_node_instance_type(**kwargs):
    instance_types = ["t2.small", "t2.medium", "t2.large", "t2.xlarge", "t2.2xlarge", "t3.nano", "t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge", "t3.2xlarge", "m3.medium", "m3.large", "m3.xlarge", "m3.2xlarge", "m4.large", "m4.xlarge", "m4.2xlarge", "m4.4xlarge", "m4.10xlarge", "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge", "m5.12xlarge", "m5.24xlarge", "c4.large", "c4.xlarge", "c4.2xlarge", "c4.4xlarge", "c4.8xlarge", "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge", "c5.9xlarge", "c5.18xlarge", "i3.large", "i3.xlarge", "i3.2xlarge",
                      "i3.4xlarge", "i3.8xlarge", "i3.16xlarge", "r3.xlarge", "r3.2xlarge", "r3.4xlarge", "r3.8xlarge", "r4.large", "r4.xlarge", "r4.2xlarge", "r4.4xlarge", "r4.8xlarge", "r4.16xlarge", "x1.16xlarge", "x1.32xlarge", "p2.xlarge", "p2.8xlarge", "p2.16xlarge", "p3.2xlarge", "p3.8xlarge", "p3.16xlarge", "p3dn.24xlarge", "r5.large", "r5.xlarge", "r5.2xlarge", "r5.4xlarge", "r5.12xlarge", "r5.24xlarge", "r5d.large", "r5d.xlarge", "r5d.2xlarge", "r5d.4xlarge", "r5d.12xlarge", "r5d.24xlarge", "z1d.large", "z1d.xlarge", "z1d.2xlarge", "z1d.3xlarge", "z1d.6xlarge", "z1d.12xlarge"]
    return instance_types


def generate_options_for_env_id(server=None, **kwargs):
    options = []
    envs = Environment.objects.filter(
        resource_handler__resource_technology__name="Amazon Web Services").all()
    for env in envs:
        options.append((env.id, env.name+'/'+str(env.vpc_id)))
    return options


def generate_options_for_role_arn(control_value=None, server=None, **kwargs):
    options = []
    if control_value is None:
        return options
    env = Environment.objects.get(id=control_value)
    region = env.aws_region
    rh = env.resource_handler.cast()
    client = boto3.client('iam',
                          region_name=region,
                          aws_access_key_id=rh.serviceaccount,
                          aws_secret_access_key=rh.servicepasswd
                          )
    response = client.list_roles()
    roles = response['Roles']
    for role in roles:
        if role['AssumeRolePolicyDocument']['Statement'][0]['Principal']['Service'] == 'eks.amazonaws.com':
            options.append((role['Arn'], role['RoleName']))
    return options


def generate_options_for_subnets(control_value=None, server=None, **kwargs):
    options = []
    if control_value is not None:
        resource = Resource.objects.filter(
            blueprint__name__iexact="Amazon EKS", lifecycle="ACTIVE", name=control_value).first()
        rh = AWSHandler.objects.filter(id=resource.aws_rh_id).first()
        client = boto3.client('ec2',
                              region_name=resource.aws_region,
                              aws_access_key_id=rh.serviceaccount,
                              aws_secret_access_key=rh.servicepasswd
                              )
        response = client.describe_subnets(Filters=[
            {
                'Name': 'state',
                'Values': ['available']
            },
            {
                'Name': 'vpc-id',
                'Values': [resource.vpc_id]
            }
        ])
        subnets = response['Subnets']
        for subnet in subnets:
            options.append(subnet['SubnetId'])
    return options


def generate_options_for_cluster_security_group(control_value=None, server=None, **kwargs):
    options = []
    if control_value is not None:
        resource = Resource.objects.filter(
            blueprint__name__iexact="Amazon EKS", lifecycle="ACTIVE", name=control_value).first()
        options = ast.literal_eval(resource.security_groups)
    return options


def generate_options_for_cluster_name(server=None, **kwargs):
    rx = Resource.objects.filter(
        blueprint__name__iexact="Amazon EKS", lifecycle="ACTIVE").values_list("name", flat=True)
    return list(rx)


def create_custom_fields():
    CustomField.objects.get_or_create(
        name='aws_rh_id',
        defaults={
            'label': 'AWS RH ID', 'type': 'STR',
            'description': 'Used by the AWS blueprints'
        }
    )
    CustomField.objects.get_or_create(
        name='stack_id',
        defaults={
            "label": 'AWS EKS Stack ID',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='cluster_name',
        defaults={
            "label": 'AWS EKS Cluster Name',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='cluster_security_group',
        defaults={
            "label": 'AWS cluster control plane security group',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='node_group_name',
        defaults={
            "label": 'AWS EKS Stack Node Group Name',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='scaling_max_size',
        defaults={
            "label": 'AWS EKS Stack Max Size',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='scaling_min_size',
        defaults={
            "label": 'AWS EKS Stack Min Size',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='scaling_desired_capacity',
        defaults={
            "label": 'AWS EKS Stack Scaling Desired Capacity',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='node_instance_type',
        defaults={
            "label": 'AWS EKS Stack Node Instance Type',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='node_image_id',
        defaults={
            "label": 'AWS EKS Stack Node Image ID',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='node_volume_size',
        defaults={
            "label": 'AWS EKS Stack Node Volume Size',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='key_name',
        defaults={
            "label": 'AWS EKS Stack Key Name',
            "type": 'STR',
            "show_as_attribute": True
        }
    )
    CustomField.objects.get_or_create(
        name='bootstrap_arguments',
        defaults={
            "label": 'AWS EKS Stack Bootstrap Arguments',
            "type": 'STR',
            "show_as_attribute": True
        }
    )


def run(resource, logger=None, **kwargs):
    stack_name = '{{ stack_name }}'
    cluster_name = '{{cluster_name}}'
    cluster_resource = Resource.objects.filter(
        blueprint__name__iexact="Amazon EKS", lifecycle="ACTIVE", name=cluster_name).first()
    rh = AWSHandler.objects.filter(id=resource.aws_rh_id).first()
    region = cluster_resource.aws_region
    cluster_security_group = '{{cluster_security_group}}'

    # Worker node parameters
    node_group_name = '{{node_group_name}}'
    scaling_min_size = '{{scaling_min_size}}'
    scaling_desired_capacity = '{{scaling_desired_capacity}}'
    scaling_max_size = '{{scaling_max_size}}'
    node_instance_type = '{{node_instance_type}}'
    node_image_id = '{{node_image_id}}'
    node_volume_size = '{{node_volume_size}}'
    key_name = '{{key_name}}'
    bootstrap_arguments = '{{bootstrap_arguments}}'

    # Network Configuration
    vpc_id = cluster_resource.vpc_id
    subnets = ast.literal_eval("{{subnets}}")

    create_custom_fields()

    resource.name = stack_name
    resource.cluster_name = cluster_name
    resource.aws_region = region
    # Store the resource handler's ID on this resource so the teardown action
    # knows which credentials to use.
    resource.aws_rh_id = rh.id
    resource.parent_resource = cluster_resource
    set_progress('Connecting to Amazon Cloudformation service...')
    client = boto3.client('cloudformation',
                          region_name=region,
                          aws_access_key_id=rh.serviceaccount,
                          aws_secret_access_key=rh.servicepasswd
                          )

    set_progress('Creating Amazon EKS stack "{}"'.format(stack_name))

    try:
        parameters = [
            {"ParameterKey": "ClusterControlPlaneSecurityGroup",
                "ParameterValue": cluster_security_group},
            {"ParameterKey": "NodeGroupName", "ParameterValue": node_group_name},
            {"ParameterKey": "NodeAutoScalingGroupMinSize",
             "ParameterValue": scaling_min_size},
            {"ParameterKey": "NodeAutoScalingGroupDesiredCapacity",
             "ParameterValue": scaling_desired_capacity},
            {"ParameterKey": "NodeAutoScalingGroupMaxSize",
             "ParameterValue": scaling_max_size},
            {"ParameterKey": "NodeInstanceType",
             "ParameterValue": node_instance_type},
            {"ParameterKey": "ClusterName", "ParameterValue": cluster_name},
            {"ParameterKey": "NodeVolumeSize",
             "ParameterValue": node_volume_size},
            {"ParameterKey": "KeyName", "ParameterValue": key_name},
            {"ParameterKey": "NodeVolumeSize",
             "ParameterValue": node_volume_size},
            {"ParameterKey": "BootstrapArguments",
             "ParameterValue": bootstrap_arguments},
            {"ParameterKey": "VpcId", "ParameterValue": vpc_id},
            {"ParameterKey": "NodeImageId", "ParameterValue": node_image_id}
        ]

        for subnet in subnets:
            parameters.append(
                {"ParameterKey": "Subnets", "ParameterValue": subnet})

        response = client.create_stack(
            StackName=stack_name,
            TemplateURL='https://amazon-eks.s3-us-west-2.amazonaws.com/cloudformation/2019-02-11/amazon-eks-nodegroup.yaml',
            Parameters=parameters,
            Capabilities=['CAPABILITY_IAM']
        )
        resource.stack_id = response['StackId']
        resource.lifecycle = 'ACTIVE'

        resource.cluster_security_group = cluster_security_group
        resource.node_group_name = node_group_name
        resource.scaling_min_size = scaling_min_size
        resource.scaling_desired_capacity = scaling_desired_capacity
        resource.scaling_max_size = scaling_max_size
        resource.node_instance_type = node_instance_type
        resource.node_image_id = node_image_id
        resource.node_volume_size = node_volume_size
        resource.key_name = key_name
        resource.bootstrap_arguments = bootstrap_arguments
        response = client.describe_stacks(
            StackName=stack_name
        )
        stacks = response['Stacks']
        # wait for stack to be created. Check status every minutes
        while stacks[0]['StackStatus'] == 'CREATE_IN_PROGRESS':
            set_progress('status of {}: "{}"'.format(
                stack_name, stacks[0]['StackStatus']))
            time.sleep(60)
            response = client.describe_stacks(
                StackName=stack_name
            )
            stacks = response['Stacks']

        resource.save()
        if stacks[0]['StackStatus'] == 'CREATE_COMPLETE':
            return "SUCCESS", "Stack creation was successful", ""
        else:
            return "FAILURE", "Stack creation was not successful", ""
    except ClientError as e:
        resource.delete()
        set_progress('AWS ClientError: {}'.format(e))
        return "FAILURE", "", e
    except Exception as err:
        return "FAILURE", "", err

    return "SUCCESS", "Created service cluster successfully", ""
