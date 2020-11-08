import subprocess as sp
import boto3 as boto
import os

print(boto.__version__)

# Run the script generated in create-default-instance.py,
# to update the libraries and do house-keeping before replication.
os.chmod('./generated_scripts/aws-login-create-image.sh', 0o755)
sp.call(["./generated_scripts/aws-login-create-image.sh"])

ec2 = boto.resource('ec2')
client = boto.client('ec2')
demo_instances = ec2.instances.filter(
    Filters=[{'Name': 'key-name', 'Values': ['ec2-keypair']}]
)

# Create a ``new'' Linux image with all the updated libraries to prevent duplication of actions on future 'slave' nodes.
for instance in demo_instances:
    if instance.public_ip_address is not None:  # Iterate through non-terminated instances in AWS
        public_ip_add = instance.public_ip_address

        image = instance.create_image(
            Description='image of distributed linux for copying',
            Name='IMAGE_LINUX'
        )
        image.wait_until_exists(Filters=[{'Name': 'state', 'Values': ['available']}])
        print("Image ID:", image.id)

        out_imageid_file = open('./tmp/image_id.txt', 'w')
        out_imageid_file.write(image.id)
