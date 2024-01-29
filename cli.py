import itertools
import json
import logging
from argparse import ArgumentParser, FileType
from typing import List, TextIO

from yarl import URL

from experiments import two_client_test
from experiments.two_client_test import Host

UPLOAD_SIZE = 1024 * 1024 * 80  # 80 MB


def main(size: int, deployment_file: TextIO):
    hosts = list(load_hosts(deployment_file))
    for i in itertools.count(1):
        two_client_test.experiment(experiment_id=str(i), upload_size=size, hosts=hosts).run()


def load_hosts(deployment: TextIO) -> List[Host]:
    data = json.load(deployment)
    for instance in data['CodexInstances']:
        container = instance['Containers']['Containers'][0]
        name = container['Name']
        api_address = next(address for address in container['Addresses']
                           if address['PortTag'] == 'codex_api_port' and not address['IsInteral'])
        yield Host(
            name=name,
            url=URL(f'{api_address["Address"]["Host"]}:{api_address["Address"]["Port"]}')
        )


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file-size', type=int, default=UPLOAD_SIZE)
    parser.add_argument('--deployment-file', type=FileType('r'), required=True)

    logging.basicConfig(format='[%(asctime)s] %(levelname)-8s %(message)s', level=logging.INFO)

    args = parser.parse_args()
    main(args.file_size, args.deployment_file)
