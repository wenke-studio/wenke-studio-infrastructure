import pulumi
from pulumi_aws import ec2

PROJECT = pulumi.get_project()


def resource_name(group_name: str) -> str:
    return PROJECT + "-" + group_name


def create_public_subnets(
    resource_name: str,
    vpc: ec2.Vpc,
    availability_zones: list[str],
    subnet_offset: int = 0,
) -> list[ec2.Subnet]:
    return [
        ec2.Subnet(
            f"{resource_name}-{availability_zone}",
            vpc_id=vpc.id,
            availability_zone=availability_zone,
            cidr_block=f"10.0.{subnet_offset + index}.0/24",
            map_public_ip_on_launch=True,
        )
        for index, availability_zone in enumerate(availability_zones)
    ]
