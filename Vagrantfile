# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/trixie64"

  config.vm.provider :virtualbox do |vb, override|
    override.vm.synced_folder ".", "/myresel", :mount_options => ["dmode=777","fmode=700"]
    vb.memory = 2048
    vb.cpus = 2
  end

  config.vm.provider :libvirt do |lv, override|
    override.vm.synced_folder ".", "/vagrant", disabled: true
    override.vm.synced_folder ".", "/myresel", type: "9p"
    lv.memory = 2048
    lv.cpus = 2
  end

  config.vm.define "default", primary: true do |default|
      default.vm.box = "debian/trixie64"
      default.vm.hostname = "reseldev"
      
      default.vm.network "forwarded_port", guest: 8000, host: 8000, host_ip: "127.0.0.1", auto_correct: true
      default.vm.network "private_network", ip: "10.0.3.94"  # VLAN 994 (exterior)
      default.vm.network "private_network", ip: "10.0.3.95"  # VLAN 995
      default.vm.network "private_network", ip: "10.0.3.99"  # VLAN 999 (known machine)
      default.vm.network "private_network", ip: "10.0.3.199"  # VLAN 999 (unknown machine)

      default.vm.provision :shell, path: ".install/vagrant_bootstrap.sh"
  end

  config.vm.define "laputex", autostart: false do |laputex|
      laputex.vm.box = "fujimakishouten/debian-stretch64"
      # laputex.vm.hostname = "laputex"
      laputex.vm.hostname = "laputex-dev"
      laputex.vm.network "private_network", ip: "10.0.3.253"
      laputex.vm.provision :shell, path: ".install/vagrant_bootstrap_laputex.sh"
  end
end
