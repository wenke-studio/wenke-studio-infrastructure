import pulumi
from integrator.aws import route53
from pulumi_aws import cognito

STACK = pulumi.get_stack()

DOMAIN = "wenke-studio.com"

ALLOWED_DOMAIN = "https://example.com"


def _(name: str) -> str:
    return f"{name}-{STACK}"


def main():
    user_pool = cognito.UserPool(
        _("user-management"),
        username_attributes=["email"],
        mfa_configuration="OFF",
        password_policy=cognito.UserPoolPasswordPolicyArgs(
            temporary_password_validity_days=7,
            minimum_length=8,
            require_numbers=True,
            require_symbols=False,
            require_lowercase=True,
            require_uppercase=True,
        ),
        account_recovery_setting=cognito.UserPoolAccountRecoverySettingArgs(
            recovery_mechanisms=[
                cognito.UserPoolAccountRecoverySettingRecoveryMechanismArgs(
                    # can be of the following: verified_email, verified_phone_number and admin_only
                    name="verified_email",
                    priority=1,
                )
            ]
        ),
    )

    google_identity_provider = cognito.IdentityProvider(
        _("user-management"),
        user_pool_id=user_pool.id,
        provider_name="Google",
        provider_type="Google",
        provider_details={
            "authorize_scopes": "email",
            "client_id": "your client_id",
            "client_secret": "your client_secret",
            # default created by cognito
            "attributes_url": "https://people.googleapis.com/v1/people/me?personFields=",
            "attributes_url_add_attributes": "true",
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "oidc_issuer": "https://accounts.google.com",
            "token_request_method": "POST",
            "token_url": "https://www.googleapis.com/oauth2/v4/token",
        },
        attribute_mapping={
            "email": "email",
            "username": "sub",
        },
    )
    user_pool_client = cognito.UserPoolClient(
        _("user-management"),
        user_pool_id=user_pool.id,
        generate_secret=False,
        callback_urls=[
            f"{ALLOWED_DOMAIN}/callback",
        ],
        logout_urls=[
            f"{ALLOWED_DOMAIN}/logout",
        ],
        allowed_oauth_flows=[
            "code",
            "implicit",
        ],
        allowed_oauth_scopes=[
            "email",
            "openid",
        ],
        # options: COGNITO | SAML | Facebook | Google | LoginWithAmazon | SignInWithApple | OIDC
        supported_identity_providers=[
            "COGNITO",
            google_identity_provider.provider_name,
        ],
    )

    user_pool_domain = cognito.UserPoolDomain(
        _("user-management"),
        user_pool_id=user_pool.id,
        domain=f"{_('user-management')}.{DOMAIN}",
        certificate_arn="arn:aws:acm:us-east-1:426352940371:certificate/383e1e78-5986-46c5-bdcc-951d5fad5207",
    )
    zone = route53.Zone.get(
        _("user-management"),
        id="Z00953103US9YCDDRTT8Z",
    )
    zone.create_cname_record(
        _("user-management"),
        name=user_pool_domain.domain,
        record=user_pool_domain.cloudfront_distribution,
    )

    pulumi.export(
        "hosted-ui",
        pulumi.Output.all(
            domain=user_pool_domain.domain,
            client_id=user_pool_client.id,
            redirect_uri=f"{ALLOWED_DOMAIN}/callback",
        ).apply(
            lambda kwargs: {
                "login": f"https://{kwargs['domain']}/login?response_type=code&client_id={kwargs['client_id']}&redirect_uri={kwargs['redirect_uri']}"
            }
        ),
    )


if __name__ == "__main__":
    main()
