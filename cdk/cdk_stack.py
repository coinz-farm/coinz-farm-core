from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_autoscaling as asg
from aws_cdk import core as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as lb
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as route53_targets


# FIXME: Move this to a Secret or parameter
DOMAIN_NAME = 'coinz.farm'
ECS_INSTANCE_TYPE = 'a1.medium'
ECS_AMI_PARAM = '/aws/service/ecs/optimized-ami/amazon-linux-2/arm64/recommended/image_id'


class CdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get Route53 Zone
        zone = route53.HostedZone.from_lookup(self, 'PublicZone', domain_name=DOMAIN_NAME)

        # FIXME: Move this to a parameter or Secret
        route53.TxtRecord(self, 'GithubVerifyTxtRecord',
            zone=zone,
            record_name='_github-challenge-coinz-farm.coinz.farm',
            values=['2ad9abb515']
        )

        # Networking
        vpc = ec2.Vpc(self, 'Vpc', nat_gateways=1)

        # Load Balancers
        lb.NetworkLoadBalancer(self, 'NLB', vpc=vpc, internet_facing=True)

        alb = lb.ApplicationLoadBalancer(self, 'ALB', vpc=vpc, internet_facing=True)

        # Public DNS Alias Records
        route53.ARecord(
            self, 'BaseARecord',
            zone=zone,
            record_name=DOMAIN_NAME,
            target=route53.RecordTarget.from_alias(
                route53_targets.LoadBalancerTarget(alb)
            )
        )
        route53.ARecord(
            self, 'WildcardARecord',
            zone=zone,
            record_name=f'*.{DOMAIN_NAME}',
            target=route53.RecordTarget.from_alias(
                route53_targets.LoadBalancerTarget(alb)
            )
        )

        # Cert with both base and wildcard domains
        cert = acm.Certificate(
            self, 'Certificate',
            domain_name=DOMAIN_NAME,
            validation=acm.CertificateValidation.from_dns(zone),
            subject_alternative_names=[f'*.{DOMAIN_NAME}']
        )

        # Redirect 80 -> 443
        alb.add_redirect()

        # HTTPS Listener
        listener = alb.add_listener(
            'HttpsListener',
            port=443,
            certificates=[cert],
            default_action=lb.ListenerAction.fixed_response(
                status_code=200,
                content_type='application/json',
                message_body='{"message":"Welcome to coinz.farm"}'
            )
        )

        cluster = ecs.Cluster(self, 'EcsCluster', vpc=vpc)

        # TODO: Got through ALL parameters and set appropriatly
        cluster.add_capacity('ArmCapacity',
            instance_type=ec2.InstanceType(ECS_INSTANCE_TYPE),
            machine_image=ec2.MachineImage.from_ssm_parameter(
                parameter_name=ECS_AMI_PARAM,
                os=ec2.OperatingSystemType.LINUX
            ),
            group_metrics=[asg.GroupMetrics.all()],
            instance_monitoring=asg.Monitoring.BASIC
        )

        task_def = ecs.TaskDefinition(self, "TaskDef",
            memory_mib='512',
            cpu='256',
            network_mode=ecs.NetworkMode.AWS_VPC,
            compatibility=ecs.Compatibility.EC2_AND_FARGATE,
        )
        task_def.add_container('Container',
            image=ecs.ContainerImage.from_registry('nginx'),
            memory_limit_mib=512,
            port_mappings=[{'containerPort': 80}]
        )

        service = ecs.Ec2Service(self, 'Service', cluster=cluster, task_definition=task_def)

        listener.add_targets('DomainTarget',
            port=80,
            targets=[service],
            priority=10,
            conditions=[
                lb.ListenerCondition.host_headers([f'nginx.{DOMAIN_NAME}'])
            ]
        )
