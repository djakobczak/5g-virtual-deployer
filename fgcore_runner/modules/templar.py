from dataclasses import dataclass, field
import ipaddress
import logging
from typing import Dict, Any, List
from pathlib import Path

from jinja2 import FileSystemLoader, Environment
from yaml import dump

from configs import MVM_IP


LOG = logging.getLogger(__name__)

class Templar:

    def __init__(self, template_dir: str) -> None:
        template_loader = FileSystemLoader(searchpath=template_dir)
        self.env = Environment(loader=template_loader)

    def render(self, src: str, **jinja_vars) -> Dict[str, Any]:
        template = self.env.get_template(src)
        generated = template.render(**jinja_vars)
        return generated

    @staticmethod
    def save(content: str, dst: str, mkparents=False) -> None:
        if mkparents:
            Path(dst).parent.mkdir(parents=True, exist_ok=True)

        with open(dst, 'w+') as out_fd:
            out_fd.write(content)

    @staticmethod
    def save_yaml(content: str, dst: str, mkparents: bool = False) -> None:
        if mkparents:
            Path(dst).parent.mkdir(parents=True, exist_ok=True)

        with open(dst, 'w+') as out_fd:
            dump(content, out_fd, default_flow_style=False)


class CloudTemplar(Templar):
    PACKAGES = [
        'python3',
        'python3-pip',
        'python3-setuptools',
        'python3-wheel',
        'ninja-build',
        'build-essential',
        'flex',
        'bison',
        'git',
        'libsctp-dev',
        'libgnutls28-dev',
        'libgcrypt-dev',
        'libssl-dev',
        'libidn11-dev',
        'libmongoc-dev',
        'libtalloc-dev',
        'libbson-dev',
        'libyaml-dev',
        'libnghttp2-dev',
        'libmicrohttpd-dev',
        'libcurl4-gnutls-dev',
        'libnghttp2-dev',
        'libtins-dev',
        'meson',
    ]

    CPLANE_PACKAGES = [
        'mongodb',
        'curl'
    ]

    RAN_PACKAGES = [
        'make',
        'gcc',
        'g++',
        'libsctp-dev',
        'lksctp-tools',
        'iproute2'
    ]

    PRE_RUNCMD_RAN = [
        'snap install cmake --classic'
    ]

    BUILD_UERANSIM = [
        'git clone https://github.com/aligungr/UERANSIM',
        'git checkout v3.2.6',
        'cd UERANSIM',
        'make'
    ]

    MVM_PACKAGES = [
        'nfs-kernel-server',
    ]

    MOUNT_NFS = [
        'mkdir -p /mnt/nfs_shared',
        f'mount {MVM_IP}:/mnt/nfs_shared /mnt/nfs_shared'
    ]

    BUILD_5GCORE = [
        'git clone https://github.com/open5gs/open5gs',
        'cd open5gs',
        'git checkout v2.4.4',
        './misc/netconf.sh',
        'meson build --prefix="${PWD}/install"',
        'ninja -C build',
        'cd build; ninja install; cd ..',
        'cd /open5gs/',
        'ln -s ${PWD}/build/subprojects/freeDiameter/extensions/dict_dcca_3gpp/dict_dcca_3gpp.fdx '
            '${PWD}/build/subprojects/freeDiameter/extensions/dict_dcca_3gpp.fdx',
        'cp install/bin/open5gs-* /usr/bin/',
        'chmod -R 755 /open5gs/'
    ]

    INSTALL_CPLANE_WEBUI = [
        'curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -',
        'sudo apt install nodejs',
        'cd /open5gs/webui',
        'npm ci --no-optional'
    ]

    SET_IPV4_FORWARDING = [
        'sed "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g" /etc/sysctl.conf',
        'sysctl -p'
    ]

    # RESET_CLOUD_INIT = ['cloud-init clean']  # cloud-init cannot finish correclty with it

    TUN_CONFIGURE = [
        'ip tuntap add name {TUN_DEV} mode tun',
        'ip addr add {TUN_IP} dev {TUN_DEV}',
        'ip link set {TUN_DEV} up',
        'iptables -t nat -A POSTROUTING -s {TUN_IP} ! -o ogstun -j MASQUERADE'
    ]

    UERANSIM_POST_INSTALL = [
        'cp /UERANSIM/build/* /usr/bin/'
    ]

    def __init__(self,
                 template_dir: str,
                 ssh_key_path: str = str(Path('keys', 'hyper_id_rsa.pub')),
                 user_data_fn: str = 'user-data.yaml.j2',
                 network_data_fn: str = 'network-data.yaml.j2'
            ) -> None:
        super().__init__(template_dir)
        self.ssh_key_path = ssh_key_path
        self.user_data_fn = user_data_fn
        self.network_data_fn = network_data_fn

    def generate_cplane_node_base(self, **config):
        user_data_vars, network_data_vars = self._generate_common_config(**config)
        user_data_vars['packages'] += self.CPLANE_PACKAGES
        user_data_vars['runcmd'] = self.BUILD_5GCORE + self.INSTALL_CPLANE_WEBUI

        user_data = self.render(self.user_data_fn, **user_data_vars)
        network_data = self.render(self.network_data_fn, **network_data_vars)
        return {
            'user_data': user_data,
            'network_data': network_data
        }

    def generate_ran_base_config(self, **config):
        user_data_vars, network_data_vars = self._generate_common_config(**config)
        user_data_vars['packages'] += self.RAN_PACKAGES
        user_data_vars['runcmd'] = self.PRE_RUNCMD_RAN + self.BUILD_UERANSIM
        return self._generate_cloud_configs(user_data_vars, network_data_vars)

    def _generate_cloud_configs(self, user_data_vars: dict, network_data_vars: dict):
        user_data = self.render(self.user_data_fn, **user_data_vars)
        network_data = self.render(self.network_data_fn, **network_data_vars)
        return {
            'user_data': user_data,
            'network_data': network_data
        }

    def generate_cplane_node(self, **config):
        user_data_vars, network_data_vars = self._generate_common_config(**config)
        user_data_vars['runcmd'] = ['echo OK']

        user_data = self.render(self.user_data_fn, **user_data_vars)
        network_data = self.render(self.network_data_fn, **network_data_vars)
        return {
            'user_data': user_data,
            'network_data': network_data
        }

    def generate_common_ran_config(self, **config):
        user_data_vars, network_data_vars = self._generate_common_config(**config)
        user_data_vars['runcmd'] = self.UERANSIM_POST_INSTALL
        return self._generate_cloud_configs(user_data_vars, network_data_vars)

    def generate_test_config(self, **config):
        config['minimal'] = True
        user_data_vars, network_data_vars = self._generate_common_config(**config)
        return self._generate_cloud_configs(user_data_vars, network_data_vars)

    def generate_upf_node(self, **config):
        user_data_vars, network_data_vars = self._generate_common_config(**config)
        user_data_vars['runcmd'] = self.SET_IPV4_FORWARDING

        user_plane_tunnels = config.get('tunnels')
        for tunnel in user_plane_tunnels:
            tun_dev = tunnel['dev']
            tun_ip = tunnel['ip']
            tun_conf = list(map(
                lambda ip_cmd: ip_cmd.format(TUN_DEV=tun_dev, TUN_IP=tun_ip),
                self.TUN_CONFIGURE)
            )
            user_data_vars['runcmd'].extend(tun_conf)

        user_data = self.render(self.user_data_fn, **user_data_vars)
        network_data = self.render(self.network_data_fn, **network_data_vars)
        return {
            'user_data': user_data,
            'network_data': network_data
        }

    def generate_mvm_config(self, **config):
        user_data_vars, network_data_vars = self._generate_common_config(**config)

        user_data_vars['packages'] = self.PACKAGES + self.MVM_PACKAGES
        runcmd_nfs = [
            'mkdir /mnt/nfs_shared',
            'chown -R nobody:nogroup /mnt/nfs_shared',
            'chmod 777 /mnt/nfs_shared',
            'echo "/mnt/nfs_shared 192.168.122.0/24(rw,sync,no_subtree_check)" >> /etc/exports',
            'sudo exportfs -a',
            'sudo systemctl restart nfs-kernel-server',
        ]

        runcmd_build_binaries = [
            'cd /mnt/nfs_shared',
            'git clone https://github.com/open5gs/open5gs',
            'cd open5gs',
            'git checkout v2.3.6',
            './misc/netconf.sh',
            'meson build --prefix="/home/ops/open5gs/install"',
            'ninja -C build',
            'cd build; ninja install; cd ..'
            'chmod -R 777 /mnt/nfs_shared/open5gs/build',
            'chmod 777 /mnt/nfs_shared/open5gs/',
            'ln -s /mnt/nfs_shared/open5gs/build/subprojects/freeDiameter/extensions/dict_dcca_3gpp/dict_dcca_3gpp.fdx '
            '/mnt/nfs_shared/open5gs/build/subprojects/freeDiameter/extensions/dict_dcca_3gpp.fdx',
        ]
        user_data_vars['runcmd'] = runcmd_nfs + runcmd_build_binaries

        user_data = self.render(self.user_data_fn, **user_data_vars)
        network_data = self.render(self.network_data_fn, **network_data_vars)
        return {
            'user_data': user_data,
            'network_data': network_data
        }

    def _generate_common_config(self, **config):
        with open(self.ssh_key_path, 'r') as key_fd:
            key = key_fd.read()

        user_data_vars = {
            'hostname': config['name'],
            'keys': [key],
            'packages': self.PACKAGES if not config.get('minimal') else []
        }

        network_data_vars = {
            'interfaces': [
                {
                    'name': 'eth01',
                    'mac': config['mac'],
                    'addresses': [config['ip']],
                    'gateway4': '192.168.122.1',
                    'dns_servers': '8.8.8.8',
                }
            ]
        }
        return user_data_vars, network_data_vars


MAX_UPFS = 4

@dataclass
class CoreIpSchema:
    sbi_net: ipaddress.IPv4Network
    ext_net: ipaddress.IPv4Network
    amf_sbi: ipaddress.IPv4Address = field(init=False)
    amf_ngap: ipaddress.IPv4Address = field(init=False)
    ausf_sbi: ipaddress.IPv4Address = field(init=False)
    bsf_sbi: ipaddress.IPv4Address = field(init=False)
    nrf_sbi: ipaddress.IPv4Address = field(init=False)
    nssf_sbi: ipaddress.IPv4Address = field(init=False)
    pcf_sbi: ipaddress.IPv4Address = field(init=False)
    smf_sbi: ipaddress.IPv4Address = field(init=False)
    udm_sbi: ipaddress.IPv4Address = field(init=False)
    udr_sbi: ipaddress.IPv4Address = field(init=False)
    upfs: List[ipaddress.IPv4Address] = field(init=False)
    gnodeb: ipaddress.IPv4Address = field(init=False)
    ues: List[ipaddress.IPv4Address] = field(init=False)
    gnb_linkIp: ipaddress.IPv4Address = field(init=False)
    gnb_ngapIp: ipaddress.IPv4Address = field(init=False)
    gnb_gtpIp: ipaddress.IPv4Address = field(init=False)
    ran_builder: ipaddress.IPv4Address = field(init=False)
    gnb_ip: ipaddress.IPv4Address = field(init=False)
    ue_ip: ipaddress.IPv4Address = field(init=False)
    builder_ip: ipaddress.IPv4Address = field(init=False)
    test_ip: ipaddress.IPv4Address = field(init=False)

    def __post_init__(self):
        self.ext_ip = self.ext_net[10]  # !TODO cplane all in one vm
        self.amf_sbi = self.sbi_net[10]
        self.amf_ngap = self.ext_ip
        self.ausf_sbi = self.sbi_net[11]
        self.bsf_sbi = self.sbi_net[12]
        self.nrf_sbi = self.sbi_net[13]
        self.pcf_sbi = self.sbi_net[14]
        self.pcrf_sbi = self.sbi_net[15]
        self.smf_sbi = self.sbi_net[16]
        self.smf_gtpc = self.sbi_net[16]
        self.smf_gtpu = self.sbi_net[16]
        self.smf_pfcp = self.ext_ip
        self.udm_sbi = self.sbi_net[17]
        self.udr_sbi = self.sbi_net[18]
        self.udm_sbi = self.sbi_net[19]
        self.nssf_sbi = self.sbi_net[20]
        self.upfs = [self.ext_net[100 + n]
                     for n in range(MAX_UPFS)]
        self.gnb_ip = self.ext_net[50]
        self.gnb_linkIp = self.gnb_ip  # 1 gnb support
        self.gnb_ngapIp = self.gnb_ip
        self.gnb_gtpIp = self.gnb_ip
        self.ran_builder = self.ext_net[200]
        self.ue_ip = self.ext_net[60]
        self.builder_ip = self.ext_net[210]
        self.test_ip = self.ext_net[253]

    def get_dict(self):
        return {
            'amf': {
                'sbi_ip': self.amf_sbi,
                'ngap_ip': self.amf_ngap
            },
            'ausf': { 'sbi_ip': self.ausf_sbi },
            'bsf': { 'sbi_ip': self.bsf_sbi },
            'nrf': { 'sbi_ip': self.nrf_sbi },
            'nssf': { 'sbi_ip': self.nssf_sbi },
            'pcf': { 'sbi_ip': self.pcf_sbi },
            'pcrf': { 'sbi_ip': self.pcrf_sbi },
            'smf': {
                'sbi_ip': self.smf_sbi,
                'pfcp_ip': self.smf_pfcp,
                'gtpc_ip': self.smf_gtpc,
                'gtpu_ip': self.smf_gtpu,
            },
            'udm': { 'sbi_ip': self.udm_sbi },
            'udr': { 'sbi_ip': self.udr_sbi },
            'ausf': { 'sbi_ip': self.ausf_sbi },
            'upfs': [
                {
                    'pfcp_ip': self.upfs[n],
                    'gtpu_ip': self.upfs[n]
                }
                for n in range(MAX_UPFS)
            ],
            'gnb': {
                'linkIp': self.gnb_linkIp,
                'ngapIp': self.gnb_ngapIp,
                'gtpIp': self.gnb_gtpIp
            }
        }

class NfTemplar(Templar):
    SERVICES = [
        'amf', 'ausf', 'bsf', 'nrf', 'nssf',
        'pcf', 'pcrf', 'smf', 'udm', 'udr', 'upf',
        'gnb', 'ue'
    ]

    def __init__(self, nfs_templates_dir: str) -> None:
        super().__init__(nfs_templates_dir)
        self.nfs_templates_dir = nfs_templates_dir

    def generate(self, ip_schema: CoreIpSchema, n_ue: int=20, **tunnels):
        templates = {}
        jinja_vars = ip_schema.get_dict()
        upfs_vars = self._get_upf_config(jinja_vars, **tunnels)
        jinja_vars.update(upfs_vars)

        # upfs configs
        upfs_configs = self._generate_upf_config(upfs_vars)
        templates.update(upfs_configs)

        ue_configs = self._generate_ue_configs(jinja_vars,n_ue)
        templates.update(ue_configs)

        for service in self.SERVICES:
            if service in ['upf', 'ue']:
                continue  # !TODO
            nf_config = self.render(f'{service}.yaml.j2', **jinja_vars)
            templates[service] = nf_config
            LOG.debug(f"Config for service {service} generated")
        return templates

    def _generate_upf_config(self, upfs_vars: dict):
        configs = {}
        for idx, upf_conf in enumerate(upfs_vars['upfs']):
            print(f"generate config for upf: {upf_conf}")
            upf_config = self.render('upf.yaml.j2', **upf_conf)
            configs[f'upf-{idx}'] = upf_config
        return configs

    def _get_upf_config(self, jinja_vars: dict, **tunnels):
        configs = {'upfs': []}
        for upf_idx, tuns_def in enumerate(tunnels.values()):
            upf_def = jinja_vars['upfs'][upf_idx]
            upf_vars = {'nets': tuns_def, **upf_def}
            configs['upfs'].append(upf_vars)
        return configs

    def _generate_ue_configs(self, jinja_vars: dict, n_ue: int):
        configs = {}
        for ue_idx in range(n_ue):
            msisdn = f'{ue_idx+1}'.zfill(10)
            # IMSI = [MCC|MNC|MSISDN]
            imsi = f'imsi-00101{msisdn}'
            ue_config = {'imsi': imsi}
            ue_config.update(jinja_vars)
            upf_config = self.render('ue.yaml.j2', **ue_config)
            configs[f'ue-{ue_idx}'] = upf_config
        return configs

if __name__ == "__main__":
    TEMPLATES_DIR = Path(Path(__file__).resolve().parent.parent, 'templates', 'nf_configs')
    LOGGER_FORMAT = '%(name)s - %(levelname)s - %(asctime)s - %(message)s'

    logging.basicConfig(format=LOGGER_FORMAT, datefmt='%I:%M:%S %p', level=logging.DEBUG)

    ipschema = CoreIpSchema(ipaddress.IPv4Network('127.0.0.0/24'), ipaddress.IPv4Network('192.168.122.0/24'), 2)
    nft = NfTemplar(TEMPLATES_DIR)
    templates = nft.generate(ipschema)
