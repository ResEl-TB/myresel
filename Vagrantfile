# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/contrib-jessie64"

  config.vm.synced_folder ".", "/myresel", :mount_options => ["dmode=777","fmode=700"]
  config.vm.hostname = "myreseldev"

  config.vm.network "forwarded_port", guest: 8000, host: 8000

  config.vm.provision :shell, path: "myresel_bootstrap.sh"
end

