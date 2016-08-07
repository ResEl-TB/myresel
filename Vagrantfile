# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/contrib-jessie64"

  config.vm.synced_folder ".", "/myresel", :mount_options => ["dmode=777","fmode=700"]
  config.vm.hostname = "reseldev"

  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "private_network", ip: "10.0.3.94"  # VLAN 994 (exterior)
  config.vm.network "private_network", ip: "10.0.3.95"  # VLAN 995
  config.vm.network "private_network", ip: "10.0.3.99"  # VLAN 999 (known machine)
  config.vm.network "private_network", ip: "10.0.3.199"  # VLAN 999 (unknown machine)

  config.vm.provision :shell, path: "vagrant/bootstrap.sh"
end

