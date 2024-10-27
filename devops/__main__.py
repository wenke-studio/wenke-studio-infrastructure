import pulumi
from pulumi_aws import ec2, get_availability_zones
from resources import (
    create_databases,
    create_gitlab,
    create_load_balancer,
    resource_name,
)


def create_network(max_azs: int = 3) -> tuple[ec2.Vpc, list[str]]:
    group_name = "network"

    vpc = ec2.Vpc(
        resource_name(group_name),
        cidr_block="10.0.0.0/16",
        enable_dns_support=True,
    )
    available = get_availability_zones(state="available")
    availability_zones = available.names[:max_azs]

    igw = ec2.InternetGateway(
        resource_name(group_name),
    )
    ec2.InternetGatewayAttachment(
        resource_name(group_name),
        internet_gateway_id=igw.id,
        vpc_id=vpc.id,
    )
    ec2.Route(
        resource_name(group_name),
        route_table_id=vpc.main_route_table_id,
        destination_cidr_block="0.0.0.0/0",
        gateway_id=igw.id,
    )
    pulumi.export("availability_zones", availability_zones)

    return vpc, availability_zones


def main():
    vpc, availability_zones = create_network(max_azs=3)

    alb_sg, target_group = create_load_balancer(
        vpc, availability_zones, subnet_offset=10
    )

    db_sg = create_databases(vpc, availability_zones, subnet_offset=20)

    gitlab_sg = create_gitlab(
        vpc,
        availability_zones,
        subnet_offset=30,
        target_group=target_group,
    )

    # todo: runner

    # todo: security group rules


if __name__ == "__main__":
    main()
