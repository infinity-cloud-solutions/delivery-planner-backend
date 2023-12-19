import boto3


class AWSClientManager:
    """
    This class is a manager for
    AWS resources, sessions, and clients.
    The class support the most used resources
    accross the project.
    - s3
    - dynamodb
    - location

    """
    def __init__(self):
        """
        It's init some most used resources
        """
        self.lambda_client = self.get_client('lambda')
        self.s3_resource = self.get_resource("s3")
        self.s3_client = self.get_client("s3")
        self.dynamodb = self.get_resource("dynamodb")
        self.location = self.get_client("location")

    def get_session(self, region="us-east-1"):
        """
        get a session using boto3 native session methods
        PARAMS:
        - region: Region Name
        RETURNS:
        - boto3 AWS session
        """
        return boto3.Session(region_name=region)

    def get_resource(self, resource: str, region="us-east-1"):
        """
        get a resource using boto3 native resource method
        PARAMS:
        - resource: Resource Name
        RETURNS:
        - boto3 AWS resource
        """
        return boto3.resource(resource, region_name=region)

    def get_client(self, resource: str, region="us-east-1"):
        """
        get a client using boto3 native client method
        PARAMS:
        - resource: Resource Name
        RETURNS:
        - boto3 AWS client
        """
        return boto3.client(resource, region_name=region)
