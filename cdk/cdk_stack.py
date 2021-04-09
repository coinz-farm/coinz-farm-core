from aws_cdk import aws_certificatemanager as acm
from aws_cdk import core as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as lb
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as route53_targets


# FIXME: Move this to a Secret or parameter
DOMAIN_NAME = 'coinz.farm'


class CdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        zone = route53.HostedZone.from_lookup(self, 'PublicZone', domain_name=DOMAIN_NAME)

        # Networking
        vpc = ec2.Vpc(self, 'Vpc', nat_gateways=1)

        # Load Balancers
        # TODO: Confirm default SG is OK
        # TODO: Confirm Subnets handled as-expected
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

        # FIXME: Move this to a parameter or Secret
        route53.TxtRecord(self, 'GithubVerifyTxtRecord',
            zone=zone,
            record_name='_github-challenge-coinz-farm.coinz.farm',
            values=['2ad9abb515']
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
        alb.add_listener(
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

        cluster.add_capacity('ArmCapacity',
            instance_type=ec2.InstanceType('a1.medium'),
            machine_image=ec2.MachineImage.from_ssm_parameter(
                parameter_name='/aws/service/ecs/optimized-ami/amazon-linux-2/arm64/recommended/image_id',
                os=ec2.OperatingSystemType.LINUX
            )
        )
