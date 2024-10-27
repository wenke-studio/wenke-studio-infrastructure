## 0.2.0 (2024-10-27)

### Feat

- **devops**: remove the dev stack
- **users**: use clerk instead cognito
- **user**: create the user management project and the dev stack
- **bin**: add a new script to handle pulumi login process
- add the resources for www website
- create official website service
- **devops**: add structure for devops
- **about**: add default resources for about.wenke-studio.com
- import wenke-studio.com domain
- import the root resource: s3.bucket, iam.group and iam.user
- create wenke-studio project

### Fix

- **wenke-studio**: redirect requests for bucket's endpoint to another domain
- **user**: add the custom domain resources
- **wenke-studio**: create an A record for cognito custom domain
- **user**: add the cognito client with Google identity provider
- **template**: remove the demo sites
- **root**: add the validation record for root certificate
- **official_website**: enable HTTP/2 support
- import the root certificate from virginia region
- remove about resources
- **template**: create a generic module to create templates
- add default tags to wenke-studio
