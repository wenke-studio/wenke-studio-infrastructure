import pulumi
from pulumi_aws import ec2, elasticache, rds

from .utils import create_public_subnets, resource_name


def create_postgresql(
    subnets: list[ec2.Subnet],
    security_group: ec2.SecurityGroup,
):
    subnet_group = rds.SubnetGroup(
        resource_name("postgresql"),
        subnet_ids=[subnet.id for subnet in subnets],
    )

    parameter_group = rds.ParameterGroup(
        resource_name("postgresql"),
        family="postgres15",
        description="Custom parameter group for GitLab PostgreSQL",
        parameters=[],
    )

    config = pulumi.Config()
    # GitLab does not support AWS Aurora (serverless db)
    rds.Instance(
        resource_name("postgresql"),
        # use below command to query engine versions:
        # `aws rds describe-db-engine-versions --engine postgres --query "DBEngineVersions[].EngineVersion"`
        engine="postgres",
        engine_version="15.8",
        instance_class="db.m5.large",
        allocated_storage=100,
        max_allocated_storage=1000,  # enable auto scaling
        storage_type=rds.StorageType.GP3,
        parameter_group_name=parameter_group.name,
        multi_az=True,
        db_name="gitlabhq_production",
        username="gitlab",
        password=config.require_secret("postgresql_password"),
        publicly_accessible=False,
        vpc_security_group_ids=[security_group.id],
        db_subnet_group_name=subnet_group.name,
        port=5432,
        skip_final_snapshot=True,
        backup_retention_period=7,
        # ! Do not upgrade the engine version automatically
        allow_major_version_upgrade=False,
        auto_minor_version_upgrade=False,
    )


def create_redis(
    subnets: list[ec2.Subnet],
    security_group: ec2.SecurityGroup,
):
    subnet_group = elasticache.SubnetGroup(
        resource_name("redis"),
        subnet_ids=[subnet.id for subnet in subnets],
    )

    parameter_group = elasticache.ParameterGroup(
        resource_name("redis"),
        family="redis7",  # redis7 is non-cluster version by default
        parameters=[],
    )

    elasticache.Cluster(
        resource_name("redis"),
        engine="redis",
        engine_version="7.1",
        node_type="cache.t3.medium",
        num_cache_nodes=1,
        parameter_group_name=parameter_group.name,
        port=6379,
        subnet_group_name=subnet_group.name,
        security_group_ids=[security_group.id],
        snapshot_retention_limit=30,
        auto_minor_version_upgrade=True,
    )


def create_databases(
    vpc: ec2.Vpc,
    availability_zones: list[str],
    subnet_offset: int,
) -> ec2.SecurityGroup:
    subnets = create_public_subnets(
        resource_name("database"),
        vpc=vpc,
        availability_zones=availability_zones,
        subnet_offset=subnet_offset,
    )

    security_group = ec2.SecurityGroup(
        resource_name("database"),
        vpc_id=vpc.id,
    )
    ec2.SecurityGroupRule(
        resource_name("database-default-outbound"),
        security_group_id=security_group.id,
        type="egress",
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
    )

    create_postgresql(subnets, security_group)
    create_redis(subnets, security_group)

    return security_group
