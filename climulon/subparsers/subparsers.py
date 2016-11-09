from handlers import provision
from handlers import decommission
from handlers import deploy
from handlers import status
from handlers import cleanup


def add_parser_provision(subparsers):
    # Subcommand for stack provisioning
    parser_provision = subparsers.add_parser(
        'provision', help='Creates infrastructure, task defs and services')
    parser_provision.add_argument(
        '-c', '--conf',
        help='Name of the config file that describes the environment.',
        required=True,
        type=str)
    parser_provision.add_argument(
        '-s', '--stacks',
        help='Will only provision the stacks listed.'
        'The stack with the flag "ComputeStack" set to true in the config '
        'file will trigger the creation of taskDefs, services and ECS '
        'cluster',
        type=str, nargs='+')
    parser_provision.add_argument(
        '-t', '--timeout',
        help='Timeout for the stack creation.',
        type=int)
    parser_provision.add_argument(
        '--dry-run',
        help='Runs the checks but do not provision the environment',
        action='store_true')
    parser_provision.set_defaults(func=provision.provision_handler)


def add_parser_decommission(subparsers):
    # Subcommand for stack decommission
    parser_decommission = subparsers.add_parser(
        'decommission',
        help='Decommissions infrastructure, task defs and cluster')
    parser_decommission.add_argument(
        '-c', '--conf',
        help='Name of the config file that describes the environment.',
        required=True,
        type=str)
    parser_decommission.add_argument(
        '-s', '--stacks',
        help='Will only decommission the stacks listed.'
        'The stack with the flag "ComputeStack" set to true in the config '
        'file will trigger the deletion of taskDefs, services and ECS '
        'cluster',
        type=str, nargs='+')
    parser_decommission.set_defaults(func=decommission.decommission_handler)


def add_parser_deploy(subparsers):
    # Subcommand for deploy through infra template files update
    parser_deploy = subparsers.add_parser(
        'deploy', help='Deploy app by updating templates from codeship')
    parser_deploy.add_argument(
        '-c', '--conf',
        help='Name of the config file that describes the environment.',
        required=True,
        type=str)
    parser_deploy.set_defaults(func=deploy.deploy_handler)


def add_parser_status(subparsers):
    # Subcommand for status check through infra template files
    parser_status = subparsers.add_parser(
        'status', help='Check app deployment status')
    parser_status.add_argument(
        '-c', '--conf',
        help='Name of the config file that describes the environment.',
        required=True,
        type=str)
    parser_status.add_argument(
        '-d', '--deploymentTimeout',
        help='Timeout for service deployment (in seconds)',
        type=int, default=300)
    parser_status.add_argument(
        '-s', '--stabilityTimeout',
        help='Timeout for containers to reach stability (in seconds)',
        type=int, default=90)
    parser_status.add_argument(
        '-t', '--tick',
        help='Time in seconds between each check iteration',
        type=int, default=10)
    parser_status.set_defaults(func=status.status_handler)


def add_parser_cleanup_ecr(subparsers):
    # Subcommand for ecr untagged image cleanup
    parser_cleanup_ecr = subparsers.add_parser(
        'cleanup-ecr', help='Remove untagged ecr docker images')
    parser_cleanup_ecr.add_argument(
        '-r', '--repos',
        help='Name of ECR docker repositories to be cleaned up',
        required=True,
        type=str, nargs='+')
    parser_cleanup_ecr.add_argument(
        '-g', '--region',
        help='Region code of the repositories (e.g. eu-central-1)',
        required=True,
        type=str)
    parser_cleanup_ecr.set_defaults(func=cleanup.cleanup_ecr_handler)
