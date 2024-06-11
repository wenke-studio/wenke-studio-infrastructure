import pulumi
from components.cloudfront import CloudFront
from integrator.aws import route53


def main():
    stack = pulumi.get_stack()
    component_name = "official-website"
    resource_name = f"{component_name}-{stack}"

    cloudfront = CloudFront(component_name=component_name)
    zone = route53.Zone.get(resource_name, id="Z00953103US9YCDDRTT8Z")
    zone.create_cname_record(
        resource_name,
        name="www.wenke-studio.com",
        record=cloudfront.distribution.domain_name,
    )


if __name__ == "__main__":
    main()
