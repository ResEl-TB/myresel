# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/contrib-jessie64"

  config.vm.synced_folder ".", "/myresel", :mount_options => ["dmode=777","fmode=700"]
  config.vm.hostname = "reseldev"

  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "private_network", ip: "10.0.3.2"  # VLAN 994 (exterior)
  config.vm.network "private_network", ip: "10.0.3.3"  # VLAN 995
  config.vm.network "private_network", ip: "10.0.3.4"  # VLAN 999 (unknown machine)
  config.vm.network "private_network", ip: "10.0.3.5"  # VLAN 999 (known machine)

  config.vm.provision :shell, path: "vagrant/bootstrap.sh"
end

