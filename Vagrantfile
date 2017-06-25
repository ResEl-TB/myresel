# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/contrib-jessie64"
  config.vm.synced_folder ".", "/myresel", :mount_options => ["dmode=777","fmode=700"]

  config.vm.define "default", primary: true do |default|
      config.vm.hostname = "reseldev"
      
      config.vm.network "private_network", ip: "10.0.3.94"  # VLAN 994 (exterior)
      config.vm.network "private_network", ip: "10.0.3.95"  # VLAN 995
      config.vm.network "private_network", ip: "10.0.3.99"  # VLAN 999 (known machine)
      config.vm.network "private_network", ip: "10.0.3.199"  # VLAN 999 (unknown machine)

      config.vm.provision :shell, path: ".install/vagrant_bootstrap.sh"
      config.vm.provider "virtualbox" do |vb| 
          vb.memory = "1024"
      end
  end

  config.vm.define "laputex", autostart: false do |laputex|
      config.vm.box = "fujimakishouten/debian-stretch64"
      # config.vm.hostname = "laputex.adm.resel.fr"
      config.vm.hostname = "laputex-dev"
      config.vm.network "private_network", ip: "10.0.3.253"
      config.vm.provision :shell, path: ".install/vagrant_bootstrap_laputex.sh"
  end
end
