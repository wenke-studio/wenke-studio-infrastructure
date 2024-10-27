import pulumi
from pulumi_aws import acm, alb, ec2, route53

from .utils import create_public_subnets, resource_name


def create_load_balancer(
    vpc: ec2.Vpc,
    availability_zones: list[str],
    subnet_offset: int = 0,
) -> tuple[ec2.SecurityGroup, alb.TargetGroup]:
    group_name = "alb"

    subnets = create_public_subnets(
        resource_name(group_name),
        vpc=vpc,
        availability_zones=availability_zones,
        subnet_offset=subnet_offset,
    )

    security_group = ec2.SecurityGroup(
        resource_name(group_name),
        vpc_id=vpc.id,
    )
    ec2.SecurityGroupRule(
        resource_name(group_name + "-default-outbound"),
        security_group_id=security_group.id,
        type="egress",
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
    )

    load_balancer = alb.LoadBalancer(
        resource_name(group_name),
        security_groups=[security_group.id],
        subnets=[subnet.id for subnet in subnets],
        internal=False,
    )

    target_group = alb.TargetGroup(
        resource_name(group_name),
        vpc_id=vpc.id,
        protocol="HTTP",  # GitLab runs on HTTP (port 80)
        port=80,
        health_check=alb.TargetGroupHealthCheckArgs(
            enabled=True,
            protocol="HTTP",
            path="/users/sign_in",
            port="traffic-port",
            matcher="200",
            healthy_threshold=2,
            unhealthy_threshold=2,
            interval=30,
            timeout=5,
        ),
    )

    certificate = acm.Certificate(
        resource_name(group_name),
        domain_name="*.wenke-studio.com",
        validation_method="DNS",
    )
    alb.Listener(
        resource_name(group_name),
        load_balancer_arn=load_balancer.arn,
        protocol="HTTPS",
        port=443,
        certificate_arn=certificate.arn,
        ssl_policy="ELBSecurityPolicy-TLS13-1-2-2021-06",
        default_actions=[
            alb.ListenerDefaultActionArgs(
                type="forward",
                target_group_arn=target_group.arn,
            )
        ],
    )

    zone_id = pulumi.Config().require("zone_id")
    route53.Record(
        resource_name(group_name),
        zone_id=zone_id,
        type="A",
        name="gitlab.wenke-studio.com",
        aliases=[
            {
                "name": load_balancer.dns_name,
                "zoneId": load_balancer.zone_id,
                "evaluate_target_health": False,
            }
        ],
    )

    return security_group, target_group
