import boto3
import botocore
from handlers.exceptions import (EcrRepositoryError,
                                 UnsupportedRegionError)


def cleanup_ecr_handler(args):
    repos = args.repos
    region = args.region
    run_cleanup_ecr(repos, region)


def run_cleanup_ecr(repos, region):
    # Checking that region is supported by ECR
    session = boto3.session.Session()
    availableRegions = session.get_available_regions(service_name="ecr")
    if region not in availableRegions:
        raise UnsupportedRegionError(region, availableRegions)

    for repo in repos:
        print("Cleaning up repository : %s" % repo)

        client = boto3.client('ecr', region_name=region)
        try:
            response = client.list_images(repositoryName=repo,
                                          filter={'tagStatus': 'UNTAGGED'})
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "RepositoryNotFoundException":
                raise EcrRepositoryError(repo)
            else:
                raise
        images = response.get('imageIds')

        for image in images:
            print('Untagged image found : %s' % image)

        if images:
            delete_response = client.batch_delete_image(
                repositoryName=repo,
                imageIds=images
            )
            print('Deleted: %s' % delete_response.get('imageIds'))
        else:
            print('No images to delete')
