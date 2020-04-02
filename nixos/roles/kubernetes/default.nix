{ config, lib, pkgs, ... }:
let

  # Kubernetes services depend on autogenerated certs.
  # Certmgr needs some seconds to generate them if they don't exist.
  # We have to wait for the certs or the services will fail.
  mkUnitWaitForCerts = name: certNames:
    lib.nameValuePair "${name}"
      {
        preStart = let
          secretsPath = config.services.kubernetes.secretsPath;
          certConditions = map (n: "! -f ${secretsPath}/${n}.pem") certNames;
        in ''
          echo Waiting for required certs: ${lib.concatStringsSep ", " certNames}...
          while [[ ${lib.concatStringsSep " || " certConditions } ]]
          do
            sleep 1
          done
        '';
      };

  kubernetesModules = [
    "services/cluster/kubernetes/addons/dns.nix"
    "services/cluster/kubernetes/addons/dashboard.nix"
    "services/cluster/kubernetes/addon-manager.nix"
    "services/cluster/kubernetes/apiserver.nix"
    "services/cluster/kubernetes/controller-manager.nix"
    "services/cluster/kubernetes/default.nix"
    "services/cluster/kubernetes/flannel.nix"
    "services/cluster/kubernetes/kubelet.nix"
    "services/cluster/kubernetes/pki.nix"
    "services/cluster/kubernetes/proxy.nix"
    "services/cluster/kubernetes/scheduler.nix"
    "services/networking/flannel.nix"
    "services/security/certmgr.nix"
    "services/security/cfssl.nix"
    "services/misc/etcd.nix"
  ];

  nixos-19_09 = (import ../../../versions.nix {}).nixos-19_09;
in
{

  disabledModules = kubernetesModules;

  imports = [
    ./frontend.nix
    ./master.nix
    ./node.nix
  ] ++ map (m: "${nixos-19_09}/nixos/modules/${m}") kubernetesModules;

  options = with lib; {
    flyingcircus.kubernetes.lib = mkOption {
      description = "Common code for our kubernetes modules.";
      type = types.attrs;
    };
  };

  config = lib.mkMerge [

    (lib.mkIf config.services.kubernetes.flannel.enable {
      # Fix forgotten dependency in NixOS 19.03.
      # This is already fixed upstream in unstable.
      systemd.services.flannel.path = [ pkgs.iptables ];
    })

    {
      flyingcircus.kubernetes.lib = { inherit mkUnitWaitForCerts; };

      systemd.services.kube-certmgr-bootstrap.preStart = ''
        mkdir -p ${config.services.kubernetes.secretsPath}
      '';

    }
  ];

}
