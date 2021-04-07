from aws_cdk import aws_certificatemanager as acm
from aws_cdk import core as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as lb
from aws_cdk import aws_route53 as route53


# FIXME: Move this to a Secret
ROUTE_53_ZONE_ID = 'Z06379522WVSTB889UN1X'
DOMAIN_NAME = 'coinz.farm'


class CdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DNS and SSL
        zone = route53.HostedZone.from_hosted_zone_id(
            self, "Route53Zone",
            ROUTE_53_ZONE_ID
        )

        cert = acm.Certificate(
            self, 'Certificate',
            domain_name=DOMAIN_NAME,
            validation=acm.CertificateValidation.from_dns(zone)
        )

        # Networking
        vpc = ec2.Vpc(self, 'Vpc', nat_gateways=1)

        # Load Balancing
        # FIXME: Add SG
        # TODO: Confirm Subnets handled as-expected
        nlb = lb.NetworkLoadBalancer(
            self, 'Nlb',
            vpc=vpc,
            internet_facing=True
        )

        # FIXME: Add SG
        # TODO: Confirm Subnets handled as-expected
        alb = lb.ApplicationLoadBalancer(
            self, 'Alb',
            vpc=vpc,
            internet_facing=True
        )

        # Default behavior: 80 -> 443
        alb.add_redirect()

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
