import pulumi
from components.cloudfront import CloudFront
from integrator.aws import acm, route53
from pulumi_aws import Provider


def main():
    stack = pulumi.get_stack()
    component_name = "official-website"
    resource_name = f"{component_name}-{stack}"

    if stack == "dev":
        cloudfront = CloudFront(component_name=component_name)

    if stack == "www":
        virginia = Provider("virginia", region="us-east-1")
        certificate = acm.Certificate.get(
            resource_name,
            arn="arn:aws:acm:us-east-1:426352940371:certificate/383e1e78-5986-46c5-bdcc-951d5fad5207",
            opts=pulumi.ResourceOptions(provider=virginia),
        )

        cloudfront = CloudFront(
            component_name=component_name,
            domain_name="www.wenke-studio.com",
            certificate=certificate,
        )
        zone = route53.Zone.get(resource_name, id="Z00953103US9YCDDRTT8Z")
        zone.create_cname_record(
            resource_name,
            name="www.wenke-studio.com",
            record=cloudfront.distribution.domain_name,
        )

        pulumi.export("distribution", cloudfront.distribution.id)
        pulumi.export("domain", cloudfront.distribution.domain_name)


if __name__ == "__main__":
    main()
